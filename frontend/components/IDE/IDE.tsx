import "allotment/dist/style.css";
import { Allotment } from "allotment";
import { useEffect, useState } from "react";
import { FileExplorer } from "./FileExplorer";
import { EditorComponent as Editor } from "./Editor";
import { Preview } from "./Preview";
import dynamic from 'next/dynamic';

// Dynamically import the Terminal component with SSR disabled
const Terminal = dynamic(() => import('./Terminal').then(mod => mod.Terminal), {
  ssr: false,
});

interface IDEProps {
  prompt: string;
}

export interface FileSystemTree {
    [key: string]: {
        type: 'file' | 'folder';
        content?: string;
        children?: FileSystemTree;
    }
}

// Helper to create nested structure
const setNestedPath = (fs: FileSystemTree, path: string, type: 'file' | 'folder', content?: string): FileSystemTree => {
    const parts = path.split(/[\\/]/).filter(p => p);
    let currentLevel = fs;

    for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        const isLast = i === parts.length - 1;

        if (isLast) {
            currentLevel[part] = type === 'file' 
                ? { type: 'file', content: content || '' }
                : { type: 'folder', children: currentLevel[part]?.children || {} };
        } else {
            if (!currentLevel[part]) {
                currentLevel[part] = { type: 'folder', children: {} };
            }
            // Type assertion to satisfy TypeScript
            currentLevel = (currentLevel[part] as { children: FileSystemTree }).children!;
        }
    }
    return fs;
};

// Helper to get file content from nested structure
const getFileContent = (fs: FileSystemTree, path: string): string | undefined => {
    const parts = path.split(/[\\/]/).filter(p => p);
    let currentLevel: any = fs;
    for (const part of parts) {
        if (!part) continue;
        const nextLevel = currentLevel[part] || (currentLevel.children ? currentLevel.children[part] : undefined);
        if (nextLevel) {
            currentLevel = nextLevel;
        } else {
            return undefined; // Path not found
        }
    }
    return currentLevel.type === 'file' ? currentLevel.content : undefined;
}

// Helper to determine language from filename
const getLanguageFromPath = (path: string): string => {
    const extension = path.split('.').pop()?.toLowerCase();
    switch (extension) {
        case 'js':
        case 'jsx':
            return 'javascript';
        case 'ts':
        case 'tsx':
            return 'typescript';
        case 'py':
            return 'python';
        case 'css':
            return 'css';
        case 'json':
            return 'json';
        case 'md':
            return 'markdown';
        case 'html':
            return 'html';
        default:
            return 'plaintext';
    }
};


export function IDE({ prompt }: IDEProps) {
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileSystem, setFileSystem] = useState<FileSystemTree>({});
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeProcessId, setActiveProcessId] = useState<string | null>(null);
  const [logSource, setLogSource] = useState<EventSource | null>(null);

  // Effect for cleaning up the event source on unmount
  useEffect(() => {
    return () => {
      logSource?.close();
    };
  }, [logSource]);

  useEffect(() => {
    if (prompt) {
      try {
        const formData = JSON.parse(prompt);
        
        const params = new URLSearchParams();
        params.append('app_name', formData.appName);
        params.append('app_type', formData.appType);
        params.append('description', formData.description);
        if (Array.isArray(formData.features)) {
            params.append('features', formData.features.join(','));
        }

        const eventSource = new EventSource(`/api/generate?${params.toString()}`);

        eventSource.onopen = () => {
            setLogs(prev => [...prev, "Connection to server established. Generating code..."]);
        };

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);

          if (data.type === 'create_folder' || data.type === 'create_file' || data.type === 'update_file') {
              setFileSystem(prevFs => {
                  const newFs = JSON.parse(JSON.stringify(prevFs)); // Deep copy
                  
                  // Use a new function to handle file content updates
                  if (data.type === 'update_file') {
                    return setNestedPath(newFs, data.path, 'file', data.content);
                  }
                  
                  // Existing logic for create
                  return setNestedPath(newFs, data.path, data.type.split('_')[1], data.content);
              });

              // If it's a file creation/update, set it as the active file
              if (data.type === 'create_file' || data.type === 'update_file') {
                setActiveFile(data.path);
              }
          } else if (data.type === 'log') {
              setLogs(prevLogs => [...prevLogs, data.message]);
          } else if (data.type === 'done') {
              eventSource.close();
          } else if (data.type === 'error') {
              setError(data.message);
              eventSource.close();
          }
        };

        eventSource.onerror = (err) => {
          setError("Error streaming code. Connection failed or server is down.");
          console.error("EventSource failed:", err);
          eventSource.close();
        };

        return () => {
          eventSource.close();
        };
      } catch (e) {
        setError("Failed to parse prompt data. Please try again.");
        console.error("Error parsing prompt JSON:", e);
      }
    }
  }, [prompt]);

  const handleEditorChange = (path: string, value: string) => {
    setFileSystem(prevFs => {
        const newFs = JSON.parse(JSON.stringify(prevFs));
        return setNestedPath(newFs, path, 'file', value);
    });
  };

  const handleRunProject = async () => {
    if (activeProcessId) {
      await handleStopProject();
    }

    setIsRunning(true);
    // Clear previous logs and show a starting message
    setLogs(["Attempting to run project..."]);
    setError('');
    setPreviewUrl(null);

    try {
      const response = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileSystem }),
      });

      const result = await response.json();

      if (response.ok) {
        setPreviewUrl(result.url);
        setActiveProcessId(result.process_id);
        setLogs(prev => [...prev, `Project is running at: ${result.url} (PID: ${result.process_id})`]);
        
        // Start listening for logs
        const newLogSource = new EventSource(`/api/logs/${result.process_id}`);
        newLogSource.onopen = () => {
            setLogs(prev => [...prev, "[Log Stream] Connection established."]);
        };
        newLogSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'log') {
                setLogs(prev => [...prev, data.message]);
            } else if (data.type === 'done') {
                setLogs(prev => [...prev, `[Log Stream] ${data.message}`]);
                newLogSource.close();
                setLogSource(null);
            }
        };
        newLogSource.onerror = (err) => {
            setLogs(prev => [...prev, "[Log Stream] Error connecting to log stream."]);
            console.error("Log EventSource failed:", err);
            newLogSource.close();
            setLogSource(null);
        };
        setLogSource(newLogSource);

      } else {
        setError(`Failed to run project: ${result.error}`);
        setLogs(prev => [...prev, `Error: ${result.error}`]);
      }
    } catch (e: any) {
      setError(`Error running project: ${e.message}`);
      setLogs(prev => [...prev, `Error: ${e.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStopProject = async () => {
    if (!activeProcessId) return;

    // Close the log stream before stopping the project
    logSource?.close();
    setLogSource(null);

    setLogs(prev => [...prev, `Stopping project (PID: ${activeProcessId})...`]);
    try {
      const response = await fetch('/api/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ process_id: activeProcessId }),
      });

      const result = await response.json();

      if (response.ok) {
        setLogs(prev => [...prev, `Project stopped successfully.`]);
        setPreviewUrl(null);
        setActiveProcessId(null);
      } else {
        setError(`Failed to stop project: ${result.error}`);
      }
    } catch (e: any) {
      setError(`Error stopping project: ${e.message}`);
    }
  };

  const activeFileContent = activeFile ? getFileContent(fileSystem, activeFile) : '';
  const activeFileLanguage = activeFile ? getLanguageFromPath(activeFile) : 'plaintext';

  return (
    <div className="h-screen w-screen bg-[#1e1e1e] text-white flex flex-col">
        {/* Header Bar */}
        <div className="flex-shrink-0 h-12 bg-[#2d2d30] border-b border-[#3e3e42] flex items-center px-4">
            <div className="flex items-center space-x-3">
                <div className="w-6 h-6 bg-[#007acc] rounded flex items-center justify-center">
                    <span className="text-white text-xs font-bold">A</span>
                </div>
                <h1 className="text-lg font-medium text-[#cccccc]">AgentForge</h1>
                <div className="text-sm text-[#858585]">•</div>
                <div className="text-sm text-[#858585]">Generated Project</div>
            </div>
            <div className="flex-grow"></div>
            <div className="flex items-center space-x-2">
                <button
                    onClick={handleStopProject}
                    disabled={!activeProcessId}
                    className="bg-[#f14c4c] hover:bg-[#d73a3a] disabled:bg-[#404040] disabled:text-[#858585] text-white font-medium py-1.5 px-3 rounded text-sm transition-colors"
                >
                    Stop
                </button>
                <button
                    onClick={handleRunProject}
                    disabled={isRunning}
                    className="bg-[#007acc] hover:bg-[#005a9e] disabled:bg-[#404040] disabled:text-[#858585] text-white font-medium py-1.5 px-3 rounded text-sm transition-colors"
                >
                    {isRunning ? 'Starting...' : (activeProcessId ? 'Restart' : 'Run Project')}
                </button>
            </div>
        </div>
        
        {/* Main Content Area */}
        <div className="flex-grow">
            <Allotment>
                {/* File Explorer */}
                <Allotment.Pane minSize={200} preferredSize="20%">
                    <div className="h-full bg-[#252526] border-r border-[#3e3e42]">
                        <FileExplorer fileSystem={fileSystem} onFileSelect={setActiveFile} />
                    </div>
                </Allotment.Pane>
                
                {/* Editor and Preview */}
                <Allotment.Pane>
                    <Allotment vertical>
                        {/* Code Editor */}
                        <Allotment.Pane>
                            <div className="h-full bg-[#1e1e1e]">
                                <Editor 
                                    value={activeFileContent || ''} 
                                    language={activeFileLanguage}
                                    onChange={(value) => activeFile && handleEditorChange(activeFile, value || '')}
                                />
                            </div>
                        </Allotment.Pane>
                        
                        {/* Live Preview */}
                        <Allotment.Pane>
                            <div className="h-full bg-[#1e1e1e] border-t border-[#3e3e42]">
                                <Preview url={previewUrl} onStop={handleStopProject} />
                            </div>
                        </Allotment.Pane>
                    </Allotment>
                </Allotment.Pane>
                
                {/* Terminal/Logs */}
                <Allotment.Pane minSize={200} preferredSize="30%">
                     <div className="h-full bg-[#1e1e1e] border-l border-[#3e3e42]">
                        {error ? (
                        <div className="text-[#f14c4c] p-4 bg-[#2d2d30]">
                            <div className="flex items-center space-x-2 mb-2">
                                <div className="w-4 h-4 bg-[#f14c4c] rounded-full flex items-center justify-center">
                                    <span className="text-white text-xs">!</span>
                                </div>
                                <span className="font-medium">Error</span>
                            </div>
                            <div className="text-sm">{error}</div>
                        </div>
                        ) : (
                        <Terminal logs={logs} />
                        )}
                    </div>
                </Allotment.Pane>
            </Allotment>
        </div>
    </div>
  );
}

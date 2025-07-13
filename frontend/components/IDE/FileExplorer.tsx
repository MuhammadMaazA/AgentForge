import { useState } from 'react';
import { ChevronRight, File, Folder, FileJson, FileCode, FileText, FileImage } from 'lucide-react';
import { FileSystemTree } from './IDE';

interface FileExplorerProps {
    fileSystem: FileSystemTree;
    onFileSelect: (path: string) => void;
}

interface FileTreeProps {
    items: FileSystemTree;
    onFileSelect: (path: string) => void;
    level?: number;
    basePath?: string;
}

const getFileIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
        case 'json':
            return <FileJson className="w-4 h-4 mr-2 text-[#ffd700] flex-shrink-0" />;
        case 'js':
        case 'jsx':
            return <FileCode className="w-4 h-4 mr-2 text-[#f7df1e] flex-shrink-0" />;
        case 'ts':
        case 'tsx':
            return <FileCode className="w-4 h-4 mr-2 text-[#3178c6] flex-shrink-0" />;
        case 'css':
        case 'scss':
            return <FileCode className="w-4 h-4 mr-2 text-[#1572b6] flex-shrink-0" />;
        case 'html':
            return <FileCode className="w-4 h-4 mr-2 text-[#e34f26] flex-shrink-0" />;
        case 'py':
            return <FileCode className="w-4 h-4 mr-2 text-[#3776ab] flex-shrink-0" />;
        case 'md':
            return <FileText className="w-4 h-4 mr-2 text-[#083fa1] flex-shrink-0" />;
        case 'png':
        case 'jpg':
        case 'jpeg':
        case 'gif':
        case 'svg':
            return <FileImage className="w-4 h-4 mr-2 text-[#a855f7] flex-shrink-0" />;
        default:
            return <File className="w-4 h-4 mr-2 text-[#cccccc] flex-shrink-0" />;
    }
};

const FileTree = ({ items, onFileSelect, level = 0, basePath = '' }: FileTreeProps) => {
  const [expanded, setExpanded] = useState<{ [key: string]: boolean }>({});
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const toggleExpand = (name: string) => {
    setExpanded(prev => ({ ...prev, [name]: !prev[name] }));
  };

  const handleFileClick = (path: string) => {
    setSelectedFile(path);
    onFileSelect(path);
  }

  return (
    <div>
      {Object.entries(items).map(([name, item]) => {
        const currentPath = basePath ? `${basePath}/${name}` : name;
        const isExpanded = expanded[name] || false;

        if (item.type === 'folder') {
          return (
            <div key={currentPath}>
              <div
                className="flex items-center cursor-pointer hover:bg-[#2a2d2e] rounded p-1"
                style={{ paddingLeft: `${level * 1.2}rem` }}
                onClick={() => toggleExpand(name)}
              >
                <ChevronRight className={`w-3 h-3 mr-1 transition-transform text-[#cccccc] ${isExpanded ? 'rotate-90' : ''}`} />
                <Folder className="w-4 h-4 mr-2 text-[#dcb67a]" />
                <span className="text-[#cccccc] text-sm">{name}</span>
              </div>
              {isExpanded && item.children && (
                <FileTree items={item.children} onFileSelect={onFileSelect} level={level + 1} basePath={currentPath} />
              )}
            </div>
          );
        }

        return (
          <div
            key={currentPath}
            className={`flex items-center cursor-pointer hover:bg-[#2a2d2e] rounded p-1 ${selectedFile === currentPath ? 'bg-[#37373d]' : ''}`}
            style={{ paddingLeft: `${level * 1.2}rem` }}
            onClick={() => handleFileClick(currentPath)}
          >
            <div style={{ width: '0.8rem' }}></div> {/* Spacer for alignment with folder icons */}
            {getFileIcon(name)}
            <span className="ml-2 text-[#cccccc] text-sm">{name}</span>
          </div>
        );
      })}
    </div>
  );
};

export function FileExplorer({ fileSystem, onFileSelect }: FileExplorerProps) {
  return (
    <div className="w-full h-full bg-[#252526] text-[#cccccc]">
      <div className="p-3 border-b border-[#2d2d30] bg-[#2d2d30]">
        <div className="font-medium mb-0 uppercase text-[#cccccc] text-xs tracking-wide">Explorer</div>
      </div>
      <div className="p-2">
        <FileTree items={fileSystem} onFileSelect={onFileSelect} />
      </div>
    </div>
  );
}

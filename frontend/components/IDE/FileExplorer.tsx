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
            return <FileJson className="w-4 h-4 mr-2 text-yellow-500 flex-shrink-0" />;
        case 'js':
        case 'jsx':
            return <FileCode className="w-4 h-4 mr-2 text-yellow-500 flex-shrink-0" />;
        case 'ts':
        case 'tsx':
            return <FileCode className="w-4 h-4 mr-2 text-blue-500 flex-shrink-0" />;
        case 'css':
        case 'scss':
            return <FileCode className="w-4 h-4 mr-2 text-pink-500 flex-shrink-0" />;
        case 'html':
            return <FileCode className="w-4 h-4 mr-2 text-orange-500 flex-shrink-0" />;
        case 'md':
            return <FileText className="w-4 h-4 mr-2 text-gray-400 flex-shrink-0" />;
        case 'png':
        case 'jpg':
        case 'jpeg':
        case 'gif':
        case 'svg':
            return <FileImage className="w-4 h-4 mr-2 text-green-400 flex-shrink-0" />;
        default:
            return <File className="w-4 h-4 mr-2 text-gray-500 flex-shrink-0" />;
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
                className="flex items-center cursor-pointer hover:bg-gray-700 rounded-md p-1"
                style={{ paddingLeft: `${level * 1.5}rem` }}
                onClick={() => toggleExpand(name)}
              >
                <ChevronRight className={`w-4 h-4 mr-1 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                <Folder className="w-4 h-4 mr-2 text-blue-400" />
                <span>{name}</span>
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
            className={`flex items-center cursor-pointer hover:bg-gray-700 rounded-md p-1 ${selectedFile === currentPath ? 'bg-gray-600' : ''}`}
            style={{ paddingLeft: `${level * 1.5}rem` }}
            onClick={() => handleFileClick(currentPath)}
          >
            <div style={{ width: '1rem' }}></div> {/* Spacer for alignment with folder icons */}
            {getFileIcon(name)}
            <span>{name}</span>
          </div>
        );
      })}
    </div>
  );
};

export function FileExplorer({ fileSystem, onFileSelect }: FileExplorerProps) {
  return (
    <div className="p-2 text-sm text-gray-300">
      <div className="font-bold mb-2 uppercase text-gray-400 text-xs px-1">Explorer</div>
      <FileTree items={fileSystem} onFileSelect={onFileSelect} />
    </div>
  );
}

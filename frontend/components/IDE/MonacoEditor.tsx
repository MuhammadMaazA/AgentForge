import Editor from "@monaco-editor/react";

interface MonacoEditorProps {
  value: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
}

export function MonacoEditor({ value, language, onChange }: MonacoEditorProps) {
  return (
    <Editor
      height="100%"
      theme="vs-dark"
      language={language || 'javascript'}
      value={value}
      onChange={onChange}
      options={{
        readOnly: false, // Make editor writable
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        fontSize: 14,
      }}
    />
  );
}

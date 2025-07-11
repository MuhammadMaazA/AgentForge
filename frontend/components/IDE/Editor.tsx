import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('./MonacoEditor').then(mod => mod.MonacoEditor), {
  ssr: false,
  loading: () => <div className="h-full bg-gray-900 text-white p-4">Loading Editor...</div>
});

interface EditorProps {
  value: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
}

export function EditorComponent({ value, language, onChange }: EditorProps) {
  return (
    <div className="h-full bg-gray-900">
      <MonacoEditor 
        value={value} 
        language={language}
        onChange={onChange}
      />
    </div>
  );
}

import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('./MonacoEditor').then(mod => mod.MonacoEditor), {
  ssr: false,
  loading: () => <div className="h-full bg-[#1e1e1e] text-[#cccccc] p-4 flex items-center justify-center">Loading Editor...</div>
});

interface EditorProps {
  value: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
}

export function EditorComponent({ value, language, onChange }: EditorProps) {
  return (
    <div className="h-full bg-[#1e1e1e]">
      <MonacoEditor 
        value={value} 
        language={language}
        onChange={onChange}
      />
    </div>
  );
}

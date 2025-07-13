import { useEffect, useRef } from 'react';

interface TerminalProps {
  logs: string[];
}

export function Terminal({ logs }: TerminalProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  return (
    <div className="h-full bg-[#1e1e1e] text-[#cccccc] font-mono text-sm flex flex-col">
      <div className="bg-[#2d2d30] p-3 text-[#cccccc] font-medium border-b border-[#3e3e42]">
        Terminal
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        {logs.map((log, index) => (
          <div key={index} className="whitespace-pre-wrap">
            <span className="text-[#4ec9b0] mr-2">$</span>
            <span className="text-[#cccccc]">{log}</span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}

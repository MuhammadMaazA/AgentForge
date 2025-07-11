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
    <div className="h-full bg-gray-950 text-white font-mono text-sm p-4 overflow-y-auto">
      <div className="text-gray-400 mb-2">Terminal Logs</div>
      {logs.map((log, index) => (
        <div key={index} className="whitespace-pre-wrap">
          <span className="text-green-400 mr-2">$</span>
          {log}
        </div>
      ))}
      <div ref={logsEndRef} />
    </div>
  );
}

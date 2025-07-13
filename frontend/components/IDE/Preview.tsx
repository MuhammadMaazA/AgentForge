interface PreviewProps {
  url: string | null;
  onStop?: () => void;
}

export function Preview({ url, onStop }: PreviewProps) {
  return (
    <div className="h-full bg-[#1e1e1e] flex flex-col">
      <div className="bg-[#2d2d30] p-3 text-sm text-[#cccccc] font-medium flex items-center justify-between border-b border-[#3e3e42]">
        <span>Live Preview</span>
        <div className="flex gap-2">
          {url && (
            <button
              onClick={() => window.open(url, '_blank')}
              className="text-xs bg-[#007acc] hover:bg-[#005a9e] text-white font-medium py-1.5 px-3 rounded transition-colors"
            >
              Open in New Tab
            </button>
          )}
          {url && onStop && (
            <button
              onClick={onStop}
              className="text-xs bg-[#d73a49] hover:bg-[#b92534] text-white font-medium py-1.5 px-3 rounded transition-colors"
            >
              Stop
            </button>
          )}
        </div>
      </div>
      {url ? (
        <iframe
          src={url}
          className="w-full h-full border-none"
          title="Live Preview"
        />
      ) : (
        <div className="flex-grow flex items-center justify-center bg-[#1e1e1e] text-[#969696]">
          Click "Run Project" to see a live preview.
        </div>
      )}
    </div>
  );
}

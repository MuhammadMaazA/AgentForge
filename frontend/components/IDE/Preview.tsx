interface PreviewProps {
  url: string | null;
  onStop?: () => void;
}

export function Preview({ url, onStop }: PreviewProps) {
  return (
    <div className="h-full bg-white flex flex-col">
      <div className="bg-gray-200 p-2 text-sm text-gray-700 font-semibold flex items-center justify-between">
        <span>Live Preview</span>
        <div className="flex gap-2">
          {url && (
            <button
              onClick={() => window.open(url, '_blank')}
              className="text-xs bg-blue-500 hover:bg-blue-600 text-white font-bold py-1 px-2 rounded"
            >
              Open in New Tab
            </button>
          )}
          {url && onStop && (
            <button
              onClick={onStop}
              className="text-xs bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-2 rounded"
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
        <div className="flex-grow flex items-center justify-center bg-gray-50 text-gray-500">
          Click "Run Project" to see a live preview.
        </div>
      )}
    </div>
  );
}

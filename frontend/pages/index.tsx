import { useState } from 'react';

export default function Home() {
  const [description, setDescription] = useState('');
  const [result, setResult] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('http://localhost:8000/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    const data = await res.json();
    setResult(data.generated_code);
  };

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">AgentForge</h1>
      <form onSubmit={handleSubmit} className="mb-4">
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full border p-2"
          rows={4}
          placeholder="Describe your agent..."
        />
        <button type="submit" className="mt-2 px-4 py-2 bg-blue-500 text-white">
          Generate
        </button>
      </form>
      {result && (
        <pre className="bg-gray-100 p-4 whitespace-pre-wrap">{result}</pre>
      )}
    </main>
  );
}

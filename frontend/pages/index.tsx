import { useState } from 'react'

export default function Home() {
  const [text, setText] = useState('')
  const [response, setResponse] = useState('')

  const submit = async () => {
    const res = await fetch(
      process.env.NEXT_PUBLIC_BACKEND_URL + '/generate',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      }
    )
    const data = await res.json()
    setResponse(data.message || data.error)
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-4">
      <h1 className="text-2xl font-bold">AgentForge Frontend</h1>
      <textarea
        className="border p-2 w-full max-w-md"
        rows={4}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded"
        onClick={submit}
      >
        Send
      </button>
      {response && (
        <pre className="mt-4 whitespace-pre-wrap max-w-md">{response}</pre>
      )}
    </div>
  )
}

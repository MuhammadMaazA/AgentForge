import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // The EventSource connection is a GET request
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method Not Allowed' });
  }

  // Extract parameters from the query string
  const { app_name, app_type, description, features } = req.query;

  if (!app_name || !app_type) {
    return res.status(400).json({ message: 'app_name and app_type are required' });
  }

  try {
    const backendResponse = await fetch('http://127.0.0.1:8000/generate_project_stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        app_name: app_name as string,
        // Split the features string back into an array
        features: typeof features === 'string' ? features.split(',') : [],
        app_type: app_type as string,
        description: description as string,
      }),
    });

    if (!backendResponse.ok) {
      const error = await backendResponse.text();
      throw new Error(`Backend error: ${error}`);
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    });

    const reader = backendResponse.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }
      const chunk = decoder.decode(value);
      res.write(chunk);
    }

    res.end();

  } catch (error) {
    console.error(error);
    const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
    // We can't send a 500 here because headers are already sent.
    console.error('Error streaming code:', errorMessage);
    res.end();
  }
}

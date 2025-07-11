import type { NextApiRequest, NextApiResponse } from 'next';

// The URL of your Python preview server
const PREVIEW_SERVER_URL = 'http://127.0.0.1:8001/api/run';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // We only want to handle POST requests for this endpoint
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).end(`Method ${req.method} Not Allowed`);
  }

  try {
    // Forward the POST request to the Python preview server
    const response = await fetch(PREVIEW_SERVER_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body),
    });

    // If the preview server returns an error, forward that to the client
    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`Error from preview server (${response.status}):`, errorBody);
      return res.status(response.status).json({ error: `Preview server failed: ${errorBody}` });
    }

    // If successful, forward the JSON response from the preview server to the client
    const data = await response.json();
    res.status(200).json(data);

  } catch (error) {
    console.error('Error proxying request to preview server:', error);
    res.status(500).json({ error: 'Failed to connect to the preview server.' });
  }
}

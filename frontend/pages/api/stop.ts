import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).end('Method Not Allowed');
  }

  const { process_id } = req.body;

  if (!process_id) {
    return res.status(400).json({ error: 'process_id is required' });
  }

  try {
    const previewServerUrl = 'http://127.0.0.1:8001/api/stop';
    
    // Add timeout to prevent hanging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    const backendRes = await fetch(previewServerUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ process_id }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const data = await backendRes.json();

    if (!backendRes.ok) {
      console.error('Error from preview server:', data);
      return res.status(backendRes.status).json({ error: data.detail || 'Failed to stop project' });
    }

    res.status(200).json(data);
  } catch (error) {
    console.error('Error forwarding stop request:', error);
    if (error.name === 'AbortError') {
      return res.status(408).json({ error: 'Request timeout - preview server not responding' });
    }
    res.status(500).json({ error: 'Internal Server Error' });
  }
}

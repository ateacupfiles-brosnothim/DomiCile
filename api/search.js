// api/search.js — Vercel Edge Function
// Proxies all AI requests to Gemini 2.0 Flash, keeping GEMINI_API_KEY server-side.
// Handles both text prompts (search/sentiment/neighborhood) and PDF base64 extraction.

export const config = { runtime: 'edge' };

export default async function handler(req) {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    });
  }

  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'GEMINI_API_KEY not set on server. Add it in Vercel → Settings → Environment Variables.' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON body' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  const { prompt, pdfBase64 } = body;

  if (!prompt || typeof prompt !== 'string' || prompt.length > 10000) {
    return new Response(JSON.stringify({ error: 'Invalid or missing prompt' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  try {
    const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

    // Build parts — text only, or PDF + text for document extraction
    const parts = [];
    if (pdfBase64) {
      parts.push({
        inline_data: {
          mime_type: 'application/pdf',
          data: pdfBase64,
        },
      });
    }
    parts.push({ text: prompt });

    const isPdfRequest = !!pdfBase64;

    const geminiBody = {
      contents: [{ parts }],
      // Only attach Google Search for non-PDF requests
      ...(isPdfRequest ? {} : { tools: [{ google_search: {} }] }),
      generationConfig: {
        temperature: 0.1,
        maxOutputTokens: 4000,
        // Only force JSON for non-PDF requests
        ...(isPdfRequest ? {} : { responseMimeType: 'application/json' }),
      },
      systemInstruction: {
        parts: [{
          text: isPdfRequest
            ? 'You are a document text extractor. Return only the raw plain text from the document with no commentary.'
            : 'You are a real estate research assistant. Always respond with raw JSON only — no markdown fences, no explanation, no preamble. Never wrap JSON in backticks.',
        }],
      },
    };

    const geminiRes = await fetch(geminiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(geminiBody),
    });

    const geminiData = await geminiRes.json();

    if (!geminiRes.ok) {
      const errMsg = geminiData.error?.message || `Gemini error ${geminiRes.status}`;
      return new Response(JSON.stringify({ error: errMsg }), {
        status: geminiRes.status,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      });
    }

    const text = geminiData.candidates?.[0]?.content?.parts
      ?.filter(p => p.text)
      ?.map(p => p.text)
      ?.join('\n') || '';

    return new Response(JSON.stringify({ text }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'no-store',
      },
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }
}

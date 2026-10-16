import { env } from 'cloudflare:workers';

export function GET() {
  const configured = Boolean(env.GEMINI_API_KEY || process.env.GEMINI_API_KEY);
  return Response.json({ configured, provider: 'Gemini',
    model: env.GEMINI_MODEL || process.env.GEMINI_MODEL || 'gemini-3.8-flash',
    knowledgeArticles: 32, sources: 6,
  }, { headers: { 'Cache-Control': 'no-store' } });
}

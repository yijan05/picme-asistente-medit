import knowledge from '@/lib/knowledge.json';

export const dynamic = 'force-dynamic';

export function GET() {
  const configured = Boolean(process.env.GEMINI_API_KEY);
  return Response.json({ configured, provider: 'Gemini',
    model: process.env.GEMINI_MODEL || 'gemini-3.5-flash-lite',
    knowledgeArticles: knowledge.articulos.length, sources: knowledge.fuentes.length,
  }, { headers: { 'Cache-Control': 'no-store' } });
}

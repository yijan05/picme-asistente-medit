import { env } from 'cloudflare:workers';
import { answerQuestion } from '@/lib/assistant.mjs';

const rate = new Map<string, { count: number; until: number }>();

export async function POST(request: Request) {
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return Response.json({ error: 'Origen no permitido.' }, { status: 403 });
  if (!request.headers.get('content-type')?.includes('application/json')) return Response.json({ error: 'Envía JSON.' }, { status: 415 });
  if (Number(request.headers.get('content-length') || 0) > 64000) return Response.json({ error: 'Solicitud demasiado grande.' }, { status: 413 });
  const key = request.headers.get('oai-authenticated-user-id') || request.headers.get('cf-connecting-ip') || 'anonymous';
  const now = Date.now();
  const current = rate.get(key);
  if (current && current.until > now && current.count >= 12) return Response.json({ error: 'Espera un minuto antes de enviar más preguntas.' }, { status: 429 });
  if (rate.size > 1000) for (const [id, item] of rate) if (item.until < now) rate.delete(id);
  rate.set(key, current && current.until > now ? { ...current, count: current.count + 1 } : { count: 1, until: now + 60000 });
  try {
    const text = await request.text();
    if (text.length > 64000) return Response.json({ error: 'Solicitud demasiado grande.' }, { status: 413 });
    const input = JSON.parse(text);
    const result = await answerQuestion(input, {
      apiKey: env.GEMINI_API_KEY || process.env.GEMINI_API_KEY || '',
      model: env.GEMINI_MODEL || process.env.GEMINI_MODEL || 'gemini-3.8-flash',
    });
    return Response.json(result, { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return Response.json({ error: 'Revisa la pregunta (máximo 2000 caracteres) y el formato del historial.' }, { status: 400 });
  }
}

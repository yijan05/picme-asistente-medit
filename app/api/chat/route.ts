import { answerQuestion } from '@/lib/assistant.mjs';

export const runtime = 'nodejs';
export const maxDuration = 60;

const rate = new Map<string, { count: number; until: number }>();

export async function POST(request: Request) {
  const origin = request.headers.get('origin');
  const url = new URL(request.url);
  const protocol = (process.env.VERCEL && request.headers.get('x-forwarded-proto')?.split(',')[0].trim()) || url.protocol.slice(0, -1);
  const expectedOrigin = new URL(`${protocol}://${request.headers.get('host') || url.host}`).origin;
  if (origin && origin !== expectedOrigin) return Response.json({ error: 'Origen no permitido.' }, { status: 403 });
  if (!request.headers.get('content-type')?.includes('application/json')) return Response.json({ error: 'Envía JSON.' }, { status: 415 });
  if (Number(request.headers.get('content-length') || 0) > 64000) return Response.json({ error: 'Solicitud demasiado grande.' }, { status: 413 });
  const key = process.env.VERCEL
    ? request.headers.get('x-forwarded-for')?.split(',')[0].trim() || 'anonymous'
    : request.headers.get('oai-authenticated-user-id') || request.headers.get('cf-connecting-ip') || 'anonymous';
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
      apiKey: process.env.GEMINI_API_KEY || '',
      model: process.env.GEMINI_MODEL || 'gemini-3.5-flash-lite',
    });
    return Response.json(result, { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return Response.json({ error: 'Revisa la pregunta (máximo 2000 caracteres) y el formato del historial.' }, { status: 400 });
  }
}

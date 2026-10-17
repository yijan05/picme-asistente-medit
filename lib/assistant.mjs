import seed from './knowledge.json' with { type: 'json' };
import { SYSTEM_PROMPT } from './prompt.mjs';

export const DEFAULT_MODEL = 'gemini-3.5-flash-lite';
export const MAX_QUESTION_LENGTH = 2000;
export const documents = seed.articulos;
const byId = new Map(documents.map(d => [d.id, d]));
const sourceById = new Map(seed.fuentes.map(s => [s.id, s]));
const stop = new Set('a al algo cual cuales como con de del dime el en es esas ese esta este estos favor hay la las lo los me mi mis para por porque que quiero se si sobre son su sus te un una unos y yo ser puedo puede puedes podrias saber quisiera explica explicame explicas cuentame hablame importante importancia what how can i tell explain about is are the why of for in and as would you please does do to an it its'.split(' '));
const aliases = { ucundinamarca: 'universidad', unicundi: 'universidad', udec: 'universidad', principios: 'principio', puntos: 'principio', punto: 'principio', principles: 'principio', principle: 'principio', dimensiones: 'dimension', ejes: 'eje', campos: 'campo', transhumano: 'transhumana', transhumanas: 'transhumana', transhuman: 'transhumana' };
const numbers = { uno: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, primero: 1, primer: 1, segundo: 2, tercero: 3, cuarto: 4, quinto: 5, sexto: 6, septimo: 7, octavo: 8, noveno: 9, decimo: 10, undecimo: 11, duodecimo: 12 };

export function normalize(value) {
  return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim()
    .replace(/\b(?:trans|tras)\s+(human[ao]s?)\b/g, 'trans$1');
}
Object.assign(aliases, { trashumana: 'transhumana', trashumano: 'transhumana', trashumanas: 'transhumana', trashumanos: 'transhumana', transumana: 'transhumana', transumano: 'transhumana' });
function tokenize(value) {
  return new Set(normalize(value).split(' ').filter(t => t && !stop.has(t)).map(t => aliases[t] || t));
}
const tokenSets = new Map(documents.map(d => [d.id, tokenize([d.titulo, ...d.preguntas, ...d.palabras_clave].join(' '))]));
const weights = new Map();
for (const dt of tokenSets.values()) for (const t of dt) weights.set(t, (weights.get(t) || 0) + 1);
for (const [t, n] of weights) weights.set(t, Math.log(1 + documents.length / (1 + n)));

export function validateInput(input) {
  if (!input || typeof input.question !== 'string' || !input.question.trim()) throw new Error('Escribe una pregunta.');
  if (input.question.length > MAX_QUESTION_LENGTH) throw new Error('La pregunta puede tener hasta 2000 caracteres.');
  if (input.history !== undefined && !Array.isArray(input.history)) throw new Error('El historial debe ser una lista.');
  const history = (input.history || []).slice(-8).map(t => {
    if (!t || !['user', 'assistant'].includes(t.role) || typeof t.content !== 'string' || t.content.length > 12000) throw new Error('El historial contiene un turno inválido.');
    return { role: t.role, content: t.content.slice(0, 3000) };
  });
  const previousIds = Array.isArray(input.previousArticleIds)
    ? input.previousArticleIds.filter(id => typeof id === 'string' && byId.has(id)).slice(0, 4) : [];
  return { question: input.question.trim(), history, previousIds };
}

export function retrieve(question, previousIds = []) {
  const q = normalize(question);
  const words = q.split(' ');
  const ids = [];
  const principleMention = words.some(w => ['principio', 'principios', 'punto', 'puntos', 'principle', 'principles'].includes(w));
  const listMention = ['principios', 'puntos', 'principles'].some(w => words.includes(w));
  const foundNumbers = words.filter(w => /^\d+$/.test(w) || numbers[w]).map(w => /^\d+$/.test(w) ? Number(w) : numbers[w]);
  if (principleMention && listMention && (foundNumbers.includes(12) || foundNumbers.length === 0)) ids.push('declaracion_completa');
  else if (principleMention || /^(?:y )?(?:el )?\d+$/.test(q)) {
    for (const n of foundNumbers) if (n >= 1 && n <= 12) ids.push(`principio_${String(n).padStart(2, '0')}`);
    if (foundNumbers.some(n => n < 1 || n > 12)) return [];
  }
  if (['siguiente', 'el siguiente', 'y el siguiente'].includes(q)) {
    const d = byId.get(previousIds[0]);
    if (d?.principio && d.principio < 12) ids.push(`principio_${String(d.principio + 1).padStart(2, '0')}`);
  }
  if (['un ejemplo', 'dame un ejemplo', 'mas sencillo', 'explicalo', 'in english', 'en ingles', 'compare them'].includes(q)) ids.push(...previousIds);
  if (q.includes('identidad de genero') || q.includes('transgenero')) ids.push('declaracion_contexto');
  const query = tokenize(question);
  if (!ids.length || (ids.length === 1 && ids[0] === 'declaracion_completa' && !foundNumbers.length)) {
    const personal = query.has('transhumana') && words.some(w => ['soy', 'somos', 'eres', 'cumplo', 'cumplimos', 'considerarme', 'considero', 'identificarme', 'convertirme', 'ser', 'reconocerme'].includes(w));
    const application = ['principio', 'declaracion'].some(w => query.has(w))
      && words.some(w => ['aplico', 'aplicar', 'aplicarlos', 'practico', 'practicar', 'vivir'].includes(w))
      && words.some(w => ['mi', 'mis', 'vida', 'cotidiana', 'diaria'].includes(w));
    if (personal || application) return ['declaracion_reflexion', 'declaracion_completa'].map(id => byId.get(id));
    if (query.has('transhumana') && [...query].every(w => ['persona', 'transhumana', 'significado', 'significa', 'declaracion', 'universidad', 'cundinamarca', 'medit'].includes(w))) return [byId.get('declaracion_resumen')];
  }
  if (query.has('medit') || (query.has('persona') && query.has('transhumana'))) {
    query.delete('universidad'); query.delete('cundinamarca');
  }
  const generic = new Set(['medit', 'universidad', 'cundinamarca', 'declaracion', 'persona', 'transhumana', 'principio']);
  const denominator = [...query].reduce((total, t) => total + (weights.get(t) || 2), 0) || 1;
  const ranked = [];
  for (const d of documents) {
    const dt = tokenSets.get(d.id);
    const shared = [...query].filter(t => dt.has(t));
    if (!shared.length) continue;
    if ([...query].some(t => !generic.has(t)) && !shared.some(t => !generic.has(t))) continue;
    let score = 0;
    for (const phrase of [d.titulo, ...d.preguntas, d.palabras_clave.join(' ')]) {
      const pt = tokenize(phrase);
      const overlap = [...query].filter(t => pt.has(t));
      const coverage = overlap.reduce((total, t) => total + (weights.get(t) || 2), 0) / denominator;
      score = Math.max(score, coverage * 0.85 + 0.15 * overlap.length / Math.max(pt.size, 1));
    }
    if (score >= 0.45) ranked.push({ id: d.id, score });
  }
  ranked.sort((a, b) => b.score - a.score);
  ids.push(...ranked.map(d => d.id));
  if (query.has('medit') && ids.length && !ids.includes('medit_definicion')) ids.splice(1, 0, 'medit_definicion');
  return [...new Set(ids)].slice(0, 4).map(id => byId.get(id)).filter(Boolean);
}

function sourcesFor(ids) {
  return [...new Set(ids.map(id => byId.get(id)?.fuente_id).filter(Boolean))].map(id => sourceById.get(id));
}

export function localAnswer(question, evidence) {
  const q = normalize(question);
  if (['hola', 'hello', 'buenas', 'buenos dias'].includes(q)) return 'Hola. Puedo ayudarte con el MEDIT y la Declaración Persona Transhumana. ¿Qué te gustaría explorar?';
  if (['gracias', 'thanks', 'muchas gracias'].includes(q)) return 'Con gusto. Puedes explorar otro principio o consultar sus fuentes.';
  if (!evidence.length) return 'No encontré sustento suficiente en esta base. Puedo ayudarte con el MEDIT, la declaración y datos generales de UCundinamarca. Para trámites y datos vigentes, consulta los canales oficiales.';
  return evidence.slice(0, evidence.length > 1 && /compar|diferenc|relacion/.test(q) ? 2 : 1).map(d => d.contenido).join('\n\n────────\n\n');
}

export function buildGeminiPayload(question, evidence, history) {
  return {
    systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
    contents: [{ role: 'user', parts: [{ text: JSON.stringify({
      documentos_recuperados: evidence.map(d => ({ id: d.id, titulo: d.titulo, contenido: d.contenido, fuente: sourceById.get(d.fuente_id)?.titulo })),
      historial_reciente: history, pregunta: question,
    }) }] }],
    generationConfig: {
      temperature: 0.2, maxOutputTokens: 4096, responseMimeType: 'application/json',
      responseSchema: { type: 'OBJECT', properties: {
        respuesta: { type: 'STRING' }, articulos_usados: { type: 'ARRAY', items: { type: 'STRING' } },
      }, required: ['respuesta', 'articulos_usados'] },
    },
  };
}

export function parseGeneration(body, allowedIds) {
  const candidate = body?.candidates?.[0];
  if (!candidate || (candidate.finishReason && candidate.finishReason !== 'STOP')) throw new Error('La generación fue bloqueada o interrumpida.');
  const text = (candidate.content?.parts || []).filter(p => !p.thought).map(p => p.text || '').join('');
  let parsed;
  try { parsed = JSON.parse(text); } catch { throw new Error('El LLM no devolvió el formato esperado.'); }
  if (!parsed || typeof parsed.respuesta !== 'string' || !parsed.respuesta.trim() || parsed.respuesta.length > 12000) throw new Error('La respuesta no tiene un tamaño válido.');
  if (!Array.isArray(parsed.articulos_usados) || parsed.articulos_usados.some(id => typeof id !== 'string' || !allowedIds.has(id))) throw new Error('La respuesta incluyó referencias no recuperadas.');
  return { answer: parsed.respuesta.trim(), articleIds: [...new Set(parsed.articulos_usados)] };
}

export async function answerQuestion(input, settings = {}, fetchImpl = fetch) {
  const { question, history, previousIds } = validateInput(input);
  if (['fuentes', 'referencias', 'cuales son tus fuentes'].includes(normalize(question))) return {
    answer: 'Estas son las fuentes de la base de conocimiento. Puedes abrirlas y contrastar la información.',
    articleIds: [], sources: seed.fuentes, mode: 'local', llmUsed: false, model: null, notice: null,
  };
  const evidence = retrieve(question, previousIds);
  const localIds = evidence.length ? [evidence[0].id] : [];
  const base = { answer: localAnswer(question, evidence), articleIds: localIds,
    sources: sourcesFor(localIds), mode: 'local', llmUsed: false, model: null,
    notice: settings.apiKey ? null : 'Gemini aún no está configurado. Esta respuesta es una consulta local.' };
  if (!evidence.length || !settings.apiKey) return base;
  const model = settings.model || DEFAULT_MODEL;
  if (!/^[A-Za-z0-9._-]+$/.test(model)) return { ...base, notice: 'La configuración del modelo no es válida.' };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 45000);
  try {
    const response = await fetchImpl(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': settings.apiKey },
      body: JSON.stringify(buildGeminiPayload(question, evidence, history)), signal: controller.signal,
    });
    if (!response.ok) {
      const reasons = { 400: 'Revisa el modelo y los parámetros del proveedor.', 401: 'El proveedor rechazó la credencial.',
        403: 'La credencial no tiene acceso al modelo.', 404: 'El modelo no está disponible para esta clave.',
        429: 'Se alcanzó el límite de consultas del proveedor.' };
      throw new Error(reasons[response.status] || 'El proveedor no está disponible.');
    }
    const parsed = parseGeneration(await response.json(), new Set(evidence.map(d => d.id)));
    return { ...parsed, sources: sourcesFor(parsed.articleIds), mode: 'gemini', llmUsed: true, model, notice: null };
  } catch (error) {
    // Nunca devuelve cuerpos HTTP, cabeceras o mensajes que puedan contener claves.
    const safe = error instanceof Error && /^(Revisa|El proveedor|La credencial|El modelo|Se alcanzó|La generación|El LLM|La respuesta)/.test(error.message)
      ? error.message : 'No se pudo completar la conexión con Gemini.';
    return { ...base, mode: 'local_respaldo', notice: safe + ' Se muestra el contenido local.' };
  } finally { clearTimeout(timeout); }
}

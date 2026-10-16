'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowRight, ArrowUpRight, BookOpen, Check, ChevronRight, CircleHelp, CornerDownLeft, ExternalLink, FileText, Leaf, Menu, MessageSquare, Plus, SendHorizontal, ShieldCheck, Sparkles, Workflow, X } from 'lucide-react';
import knowledge from '@/lib/knowledge.json';
import { reflection } from '@/lib/reflection';

type View = 'chat' | 'principles' | 'sources' | 'reflection' | 'architecture';
type Source = { id?: string; titulo: string; url: string; consultada_el?: string };
type Message = { role: 'user' | 'assistant'; content: string; articleIds?: string[]; sources?: Source[]; mode?: string; notice?: string | null };
type ChatResult = { answer: string; articleIds: string[]; sources: Source[]; mode: string; notice: string | null; error?: string };
const initialMessage: Message = { role: 'assistant', content: 'Hola, soy PicMe. Estoy aquí para explorar contigo el MEDIT y los doce principios de la Declaración Persona Transhumana. ¿Por dónde empezamos?', mode: 'welcome' };
const navigation: { id: View; label: string; icon: typeof BookOpen }[] = [
  { id: 'chat', label: 'Asistente', icon: MessageSquare },
  { id: 'principles', label: 'Los doce principios', icon: BookOpen },
  { id: 'sources', label: 'Fuentes y contexto', icon: FileText },
  { id: 'reflection', label: 'Reflexión · ES / EN', icon: Leaf },
  { id: 'architecture', label: 'Cómo funciona', icon: Workflow },
];
const principles = knowledge.articulos.filter(a => 'principio' in a).sort((a, b) => (a.principio || 0) - (b.principio || 0));
const titles = ['Organizo mi vida', 'Defiendo la vida', 'Edifico mi bienestar', 'Aprendo de mi experiencia', 'Me valoro y cuido', 'Voy más allá de mí', 'Me perfecciono', 'Contribuyo a la paz', 'Soy libre y responsable', 'Forjo mi personalidad', 'Transformo para mejorar', 'Cultivo mi felicidad'];
const promptCards = [
  { tag: 'ENTENDER EL MODELO', title: '¿Qué es el MEDIT?', question: '¿Qué es el MEDIT y cuáles son sus dimensiones?' },
  { tag: 'APLICAR UN PRINCIPIO', title: 'Ir más allá de mí', question: 'Explícame el principio 6 con un ejemplo en un trabajo en equipo.' },
  { tag: 'PENSAR CON CRITERIO', title: 'Autonomía y cuidado', question: 'Compara los principios 5 y 9 en el contexto del aprendizaje.' },
];

function BrandMark({ small = false }: { small?: boolean }) {
  return <span className={`brand-mark ${small ? 'small' : ''}`} aria-hidden="true"><span /><span /><span /></span>;
}

export default function Home() {
  const [view, setView] = useState<View>('chat');
  const [mobileMenu, setMobileMenu] = useState(false);
  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState<{ configured: boolean; model: string } | null>(null);
  const [language, setLanguage] = useState<'es' | 'en'>('es');
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const controller = useRef<AbortController | null>(null);
  const inflight = useRef(false);
  useEffect(() => {
    fetch('/api/status').then(r => r.ok ? r.json() : Promise.reject()).then(value => {
      const data = value as { configured?: unknown; model?: unknown };
      if (typeof data.configured === 'boolean' && typeof data.model === 'string') setStatus({ configured: data.configured, model: data.model });
    }).catch(() => setStatus(null));
    return () => controller.current?.abort();
  }, []);
  useEffect(() => { if (messages.length > 1) bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, [messages, busy]);

  function go(next: View) { setView(next); setMobileMenu(false); }
  function reset() {
    controller.current?.abort(); controller.current = null; inflight.current = false;
    setBusy(false); setMessages([initialMessage]); setError(''); setQuestion(''); go('chat');
    setTimeout(() => input.current?.focus(), 0);
  }
  async function ask(value = question) {
    if (!value.trim() || inflight.current) return;
    if (value.length > 2000) { setError('Usa una pregunta de hasta 2000 caracteres.'); return; }
    inflight.current = true; setBusy(true); setQuestion(''); setError(''); go('chat');
    const previous = messages;
    const last = [...previous].reverse().find(m => m.role === 'assistant' && m.articleIds?.length);
    setMessages([...previous, { role: 'user', content: value.trim() }]);
    const requestController = new AbortController(); controller.current = requestController;
    const timer = setTimeout(() => requestController.abort(), 50000);
    try {
      const result = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: requestController.signal,
        body: JSON.stringify({ question: value.trim(), history: previous.filter(m => m.mode !== 'welcome').slice(-8).map(m => ({ role: m.role, content: m.content })), previousArticleIds: last?.articleIds || [] }),
      });
      const data = await result.json() as Partial<ChatResult>;
      if (!result.ok) throw new Error(data.error || 'No se pudo completar la consulta.');
      if (typeof data.answer !== 'string') throw new Error('La respuesta del servidor no tiene el formato esperado.');
      if (controller.current !== requestController) return;
      setMessages(current => [...current, { role: 'assistant', content: data.answer as string, articleIds: data.articleIds || [], sources: data.sources || [], mode: data.mode || 'local', notice: data.notice }]);
    } catch (failure) {
      if (controller.current !== requestController) return;
      setError(failure instanceof Error && failure.name !== 'AbortError' ? failure.message : 'La consulta tardó demasiado. Intenta de nuevo.');
      setQuestion(value);
    } finally {
      clearTimeout(timer);
      if (controller.current === requestController) { controller.current = null; inflight.current = false; setBusy(false); }
    }
  }
  const reflectionText = reflection[language];
  const pageTitle = navigation.find(item => item.id === view)?.label;

  return <div className="app-shell">
    <aside className={`sidebar ${mobileMenu ? 'open' : ''}`}>
      <a className="brand" href="#" onClick={event => { event.preventDefault(); go('chat'); }} aria-label="PicMe, inicio"><BrandMark /><span>Pic<span className="brand-light">Me</span><small>APRENDER PARA LA VIDA</small></span></a>
      <button className="new-chat" onClick={reset}><Plus size={17} /> Nueva conversación <span>↗</span></button>
      <p className="nav-eyebrow">TU ESPACIO DE APRENDIZAJE</p>
      <nav aria-label="Navegación principal">{navigation.map(item => <button key={item.id} className={view === item.id ? 'nav-item active' : 'nav-item'} onClick={() => go(item.id)}><item.icon size={18} strokeWidth={1.65} /><span>{item.label}</span>{view === item.id && <span className="nav-dot" />}</button>)}</nav>
      <div className="sidebar-note"><span className="note-icon"><Leaf size={21} /></span><p>Ir más allá de mí.</p><span>Aprender también es cuidar de los demás y de nuestro entorno.</span><button onClick={() => ask('Explícame el principio 6')}>Explorar el principio 06 <ArrowUpRight size={14} /></button></div>
      <div className="sidebar-footer"><span className="avatar">EV</span><div><strong>Evelin Virguez</strong><small>Proyecto académico · PicMe</small></div><ShieldCheck size={16} /></div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="breadcrumb"><button className="mobile-toggle" aria-label="Abrir menú" aria-expanded={mobileMenu} onClick={() => setMobileMenu(!mobileMenu)}>{mobileMenu ? <X size={20} /> : <Menu size={20} />}</button><span>UCundinamarca</span><ChevronRight size={13} /><strong>{pageTitle}</strong></div><span className="campus"><span /> Seccional Ubaté</span></header>
      <main>
        {view === 'chat' && <div className={`chat-page ${messages.length > 1 ? 'has-conversation' : ''}`}>
          <section className="welcome-heading"><p className="eyebrow"><Sparkles size={14} /> ASISTENTE DE APRENDIZAJE</p><h1>Una pregunta.<br /><em>Un nuevo aprendizaje.</em></h1><p>Exploremos el MEDIT y la Declaración Persona Transhumana.<br className="desktop-br" /> Con ideas claras, ejemplos y fuentes para pensar por ti misma.</p></section>
          <div className="knowledge-line"><span className="knowledge-pill"><BookOpen size={13} /> 32 notas de conocimiento</span><span>6 fuentes institucionales</span><span className="separator" /><span className={status?.configured ? 'model-status on' : 'model-status'}><span />{status === null ? 'Comprobando conexión' : status.configured ? 'Gemini configurado' : 'Consulta local'}</span></div>
          {status && !status.configured && <div className="connection-note"><CircleHelp size={16} /><p>Gemini aún no está configurado. Puedes consultar la base local; las respuestas generadas por un LLM se identificarán cuando se active la conexión.</p></div>}
          <section className="conversation" aria-label="Conversación" aria-live="polite">{messages.map((message, i) => <article key={i} className={`message ${message.role}`}>
            {message.role === 'assistant' && <div className="message-mark"><BrandMark small /></div>}
            <div className="message-body"><div className="message-caption"><strong>{message.role === 'user' ? 'Tú' : 'PicMe'}</strong>{message.role === 'assistant' && message.mode !== 'welcome' && <span>{message.mode === 'gemini' ? <><Sparkles size={11} /> Gemini</> : <><BookOpen size={11} /> Consulta local</>}</span>}</div><p className="message-text">{message.content}</p>{message.notice && <p className="message-notice">{message.notice}</p>}{Boolean(message.sources?.length) && <div className="citation-list">{message.sources?.map(source => <a key={source.url} href={source.url} target="_blank" rel="noreferrer"><FileText size={12} /><span>{source.titulo}</span><ArrowUpRight size={12} /></a>)}</div>}</div>
          </article>)}{busy && <article className="message assistant"><div className="message-mark"><BrandMark small /></div><div className="message-body"><div className="typing"><span /><span /><span /></div><p className="working-label">Consultando las fuentes y preparando tu respuesta…</p></div></article>}<div ref={bottom} /></section>
          {messages.length === 1 && <section className="prompt-cards" aria-label="Ideas para comenzar">{promptCards.map(card => <button key={card.tag} onClick={() => ask(card.question)}><span>{card.tag}</span><strong>{card.title}</strong><ArrowUpRight size={17} /></button>)}</section>}
          <div className="composer-area">{error && <div role="alert" className="error-message">{error}</div>}<form className={`composer ${busy ? 'disabled' : ''}`} onSubmit={event => { event.preventDefault(); ask(); }}><label htmlFor="question" className="sr-only">Tu pregunta sobre el MEDIT o la declaración</label><textarea ref={input} id="question" value={question} onChange={event => setQuestion(event.target.value)} placeholder="¿Qué te gustaría comprender hoy?" rows={2} maxLength={2000} disabled={busy} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); ask(); } }} /><div className="composer-bottom"><span><ShieldCheck size={12} /> Conversación sin acceso a datos biométricos</span><button type="submit" aria-label="Enviar pregunta" disabled={busy || !question.trim()}><ArrowRight size={19} /></button></div></form><p className="composer-hint">La IA puede equivocarse. Contrasta las fuentes. {status?.configured ? 'La pregunta y los fragmentos se enviarán a Gemini.' : 'En modo local, tus preguntas no se envían a un LLM.'}</p></div>
        </div>}
        {view === 'principles' && <div className="content-page"><p className="eyebrow"><BookOpen size={14} /> DECLARACIÓN PERSONA TRANSHUMANA</p><h1>Doce compromisos.<br /><em>Una forma de vivir.</em></h1><p className="page-lead">Lee cada principio y explora cómo se relaciona con tu aprendizaje y tu entorno.</p><div className="declaration-note"><Leaf size={19} /><p>La firma de la declaración corresponde a Adriano Muñoz Barrera, Fusagasugá, 26 de agosto de 2022. Las explicaciones y ejemplos son material didáctico del proyecto.</p></div><div className="principle-grid">{principles.map((article, i) => <details key={article.id} className="principle-card"><summary><span className="principle-number">{String(i + 1).padStart(2, '0')}</span><strong>{titles[i]}</strong><Plus size={17} /></summary><div className="principle-body"><p>{article.contenido.split('\n\n').slice(1).join('\n\n')}</p><button onClick={() => ask(`Explícame el principio ${i + 1} y su relación con el aprendizaje`)}>Explorar con PicMe <ArrowRight size={14} /></button></div></details>)}</div><a className="text-link" href={knowledge.fuentes[0].url} target="_blank" rel="noreferrer">Leer la declaración en la fuente oficial <ArrowUpRight size={15} /></a></div>}
        {view === 'sources' && <div className="content-page"><p className="eyebrow"><FileText size={14} /> INFORMACIÓN CON ORIGEN</p><h1>Las fuentes<br /><em>también enseñan.</em></h1><p className="page-lead">La base reúne documentos públicos de UCundinamarca, consultados el 15 de octubre de 2026. Los enlaces permiten contrastar las respuestas.</p><div className="source-list">{knowledge.fuentes.map((source, i) => <a href={source.url} target="_blank" rel="noreferrer" key={source.id} className="source-card"><span className="source-index">0{i + 1}</span><div><span className="source-type">UCUNDINAMARCA · {source.url.endsWith('.pdf') ? 'DOCUMENTO PDF' : 'SITIO INSTITUCIONAL'}</span><h2>{source.titulo}</h2><p>{source.nota}</p></div><ArrowUpRight size={20} /></a>)}</div><div className="declaration-note"><CircleHelp size={19} /><p>La base no contiene valores de matrícula, calendarios vigentes ni estados de trámites personales. Para esos datos, consulta directamente a la Universidad.</p></div></div>}
        {view === 'reflection' && <div className="content-page reflection-page"><div className="reflection-toolbar"><p className="eyebrow"><Leaf size={14} /> TECNOLOGÍA CON SENTIDO</p><div className="language-switch" aria-label="Idioma de la reflexión"><button className={language === 'es' ? 'selected' : ''} onClick={() => setLanguage('es')}>ES</button><button className={language === 'en' ? 'selected' : ''} onClick={() => setLanguage('en')}>EN</button></div></div><h1 className="reflection-title">{reflectionText.title}</h1><p className="reflection-question">{reflectionText.question}</p><div className="reflection-article" lang={language}>{reflectionText.paragraphs.map((paragraph, i) => <section key={i}><span>0{i + 1}</span><p>{paragraph}</p></section>)}</div><div className="reflection-footer"><span><ShieldCheck size={17} /> {language === 'es' ? 'Supervisión humana · Fuentes visibles · Autonomía' : 'Human oversight · Visible sources · Autonomy'}</span></div></div>}
        {view === 'architecture' && <div className="content-page architecture-page"><p className="eyebrow"><Workflow size={14} /> DEL DOCUMENTO A LA CONVERSACIÓN</p><h1>Comprender<br /><em>cómo responde.</em></h1><p className="page-lead">El asistente combina recuperación de conocimiento con un modelo de lenguaje. Cada parte tiene una responsabilidad concreta.</p><div className="architecture-flow">{[['01', 'Tu pregunta', 'Se valida el tamaño y el historial.'], ['02', 'Conocimiento', 'Se recuperan hasta cuatro fragmentos relevantes.'], ['03', 'Contexto y LLM', 'Gemini recibe el prompt, los fragmentos y el contexto reciente.'], ['04', 'Respuesta y fuentes', 'Se valida el formato y que las referencias existan.']].map(([n, title, text]) => <article key={n}><span>{n}</span><h2>{title}</h2><p>{text}</p></article>)}</div><div className="technical-grid"><article><ShieldCheck size={21} /><h2>Un propósito delimitado</h2><p>El system prompt incluye reglas de evidencia, ejemplos, límites de dominio y respeto por la autonomía. El LLM no puede ejecutar consultas SQL ni cambiar datos.</p></article><article><BookOpen size={21} /><h2>RAG léxico y documentos</h2><p>La versión web usa los mismos 32 artículos estructurados que la base SQLite del programa de escritorio. La selección se realiza por coincidencias ponderadas; no usa embeddings.</p></article><article><Sparkles size={21} /><h2>Conexión transparente</h2><p>{status?.configured ? `Modelo configurado: ${status.model}. Su disponibilidad se comprueba al realizar una consulta.` : 'No hay una clave de Gemini configurada. La integración está preparada y la consulta local permanece disponible.'} Las respuestas del LLM llevan la etiqueta Gemini.</p></article><article><CircleHelp size={21} /><h2>Límites reales</h2><p>La validación de referencias no garantiza que cada afirmación sea correcta. La revisión humana y la consulta de las fuentes siguen siendo necesarias.</p></article></div><div className="declaration-note"><Leaf size={19} /><p>Este chat educativo acompaña a PicMe. El reconocimiento facial y el registro de ingresos se ejecutan en el programa de escritorio, separados del proveedor de lenguaje.</p></div></div>}
      </main>
      <footer className="page-footer"><span>PicMe · Conocimiento que transforma</span><span>Proyecto académico · Introducción a Machine Learning</span></footer>
    </div>
  </div>;
}

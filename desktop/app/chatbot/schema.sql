PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS metadato (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fuente (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    url TEXT NOT NULL,
    consultada_el TEXT NOT NULL,
    nota TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS articulo (
    id TEXT PRIMARY KEY,
    categoria TEXT NOT NULL,
    titulo TEXT NOT NULL,
    contenido TEXT NOT NULL,
    palabras_clave TEXT NOT NULL,
    fuente_id TEXT NOT NULL REFERENCES fuente(id),
    principio INTEGER UNIQUE CHECK (principio BETWEEN 1 AND 12)
);
CREATE TABLE IF NOT EXISTS pregunta_ejemplo (
    id INTEGER PRIMARY KEY,
    articulo_id TEXT NOT NULL REFERENCES articulo(id) ON DELETE CASCADE,
    texto TEXT NOT NULL,
    UNIQUE(articulo_id, texto)
);
CREATE INDEX IF NOT EXISTS idx_articulo_categoria ON articulo(categoria);

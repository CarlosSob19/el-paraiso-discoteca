-- ============================================================
-- EL PARAÍSO — Discoteca Montería
-- BORRADOR: esquema y datos iniciales para PostgreSQL
--
-- Versión Postgres de elparaiso.sql (mismas tablas y datos).
-- Se puede ejecutar varias veces: no borra ni duplica datos.
--
-- El usuario administrador NO está aquí a propósito: lo crea
-- app.py al arrancar, con la contraseña de ADMIN_PASSWORD.
-- ============================================================

SET client_encoding = 'UTF8';

-- ------------------------------------------------------------
-- Tablas
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL          NOT NULL,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(120) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    es_admin      BOOLEAN      DEFAULT FALSE,
    creado_en     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_usuarios_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS generos_musicales (
    id          SERIAL         NOT NULL,
    nombre      VARCHAR(50) NOT NULL,
    slug        VARCHAR(50) NOT NULL,
    descripcion TEXT,
    PRIMARY KEY (id),
    CONSTRAINT uq_generos_slug UNIQUE (slug)
);

CREATE TABLE IF NOT EXISTS eventos (
    id               SERIAL          NOT NULL,
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    precio_general   DOUBLE PRECISION       NOT NULL,
    precio_vip       DOUBLE PRECISION       NOT NULL,
    precio_palco     DOUBLE PRECISION       NOT NULL,
    precio_backstage DOUBLE PRECISION       NOT NULL,
    precio_king      DOUBLE PRECISION       NOT NULL,
    cupos            INT          DEFAULT 500,
    imagen           VARCHAR(200) DEFAULT 'default.jpg',
    genero_id        INT          NOT NULL,
    destacado        BOOLEAN      DEFAULT FALSE,
    fecha_evento     DATE         NOT NULL,
    hora_evento      VARCHAR(10)  DEFAULT '22:00',
    artista          VARCHAR(100),
    ubicacion        VARCHAR(100) DEFAULT 'Calle 9 Mz 15 Lote 10, Montería',
    creado_en        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_eventos_genero FOREIGN KEY (genero_id) REFERENCES generos_musicales (id)
);

CREATE TABLE IF NOT EXISTS imagenes_galeria (
    id           SERIAL          NOT NULL,
    titulo       VARCHAR(100) NOT NULL,
    categoria    VARCHAR(50)  DEFAULT 'general',
    imagen_url   VARCHAR(300) NOT NULL,
    fecha_evento DATE,
    orden        INT          DEFAULT 0,
    activa       BOOLEAN      DEFAULT TRUE,
    creado_en    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS promociones (
    id                   SERIAL          NOT NULL,
    codigo               VARCHAR(20)  NOT NULL,
    nombre               VARCHAR(100) NOT NULL,
    descripcion          TEXT,
    descuento_porcentaje INT          DEFAULT 0,
    descuento_valor      DOUBLE PRECISION       DEFAULT 0,
    tipo_entrada         VARCHAR(20),
    usos_maximos         INT          DEFAULT 100,
    usos_actuales        INT          DEFAULT 0,
    fecha_inicio         DATE,
    fecha_fin            DATE,
    activa               BOOLEAN      DEFAULT TRUE,
    creado_en            TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_promociones_codigo UNIQUE (codigo)
);

CREATE TABLE IF NOT EXISTS licores (
    id          SERIAL          NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio      DOUBLE PRECISION       NOT NULL,
    categoria   VARCHAR(50)  DEFAULT 'whiskey',
    imagen      VARCHAR(300) DEFAULT 'default.jpg',
    disponible  BOOLEAN      DEFAULT TRUE,
    creado_en   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS reservas_mesa (
    id          SERIAL          NOT NULL,
    mesa_id     VARCHAR(20)  NOT NULL,
    mesa_zona   VARCHAR(50)  NOT NULL,
    mesa_precio DOUBLE PRECISION       NOT NULL DEFAULT 0,
    fecha       DATE         NOT NULL,
    personas    INT          NOT NULL DEFAULT 1,
    nombre      VARCHAR(100) NOT NULL,
    telefono    VARCHAR(30)  NOT NULL,
    email       VARCHAR(120) NOT NULL,
    notas       TEXT,
    estado      VARCHAR(20)  DEFAULT 'pendiente',
    usuario_id  INT,
    creado_en   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_reservas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);

CREATE TABLE IF NOT EXISTS ordenes (
    id           SERIAL         NOT NULL,
    usuario_id   INT         NOT NULL,
    total        DOUBLE PRECISION      DEFAULT 0,
    estado       VARCHAR(20) DEFAULT 'pendiente',
    tipo_entrada VARCHAR(20) DEFAULT 'general',
    creado_en    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_ordenes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
);

-- evento_id y licor_id son NULL cuando el ítem es una reserva de mesa
CREATE TABLE IF NOT EXISTS items_orden (
    id              SERIAL         NOT NULL,
    orden_id        INT         NOT NULL,
    evento_id       INT,
    cantidad        INT         NOT NULL,
    precio_unitario DOUBLE PRECISION      NOT NULL,
    tipo_entrada    VARCHAR(20) DEFAULT 'general',
    licor_id        INT,
    PRIMARY KEY (id),
    CONSTRAINT fk_items_licor  FOREIGN KEY (licor_id)  REFERENCES licores (id),
    CONSTRAINT fk_items_orden  FOREIGN KEY (orden_id)  REFERENCES ordenes (id),
    CONSTRAINT fk_items_evento FOREIGN KEY (evento_id) REFERENCES eventos (id)
);

-- ------------------------------------------------------------
-- Índices
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_eventos_fecha ON eventos (fecha_evento);
CREATE INDEX IF NOT EXISTS idx_reservas_fecha ON reservas_mesa (fecha);

-- ------------------------------------------------------------
-- Datos iniciales (los mismos que crea init_db() en app.py)
-- ------------------------------------------------------------

INSERT INTO generos_musicales (nombre, slug, descripcion) VALUES
    ('Crossover',          'crossover',   'Salsa, Vallenato, Merengue y más en una sola noche'),
    ('Reggaetón & Urbano', 'reggaeton',   'Lo más candente del género urbano'),
    ('Electrónica',        'electronica', 'House, Techno y Latin House'),
    ('Dembow',             'dembow',      'El ritmo que está rompiendo en toda Colombia'),
    ('Champeta',           'champeta',    'El sonido autóctono de la Costa Caribe')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Éxitos de la Champeta',
       'Disfruta una noche de éxitos de la champeta en Paraíso Club.',
       20000, 45000, 90000, 160000, 280000, 300, g.id,
       'https://images.unsplash.com/photo-1740572569816-9c437c4b9c4d?q=80&w=1170&auto=format&fit=crop',
       TRUE, CURRENT_DATE + 5, '21:00', 'Paraíso Club', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'champeta'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Éxitos de la Champeta');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Noche de Locura',
       'Llega que sí es para eso: rumba toda la noche en Paraíso Club.',
       30000, 60000, 120000, 200000, 350000, 300, g.id,
       'https://images.unsplash.com/photo-1647314620432-7e27193891cb?q=80&w=1169&auto=format&fit=crop',
       TRUE, CURRENT_DATE + 8, '22:00', 'Paraíso Club', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Noche de Locura');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'El Clásico Español en Pantalla Gigante',
       'Vive el clásico español en pantalla gigante en Paraíso Club.',
       20000, 45000, 90000, 160000, 280000, 300, g.id,
       'https://images.unsplash.com/photo-1647314620432-7e27193891cb?q=80&w=1169&auto=format&fit=crop',
       TRUE, CURRENT_DATE + 12, '14:00', 'Pantalla gigante', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'El Clásico Español en Pantalla Gigante');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Selección Colombia en Pantalla Gigante',
       'Vamos todos, apoyemos a la Selección Colombia. Te esperamos en Paraíso Club Montería.',
       20000, 45000, 90000, 160000, 280000, 300, g.id,
       'https://images.unsplash.com/photo-1740572569816-9c437c4b9c4d?q=80&w=1170&auto=format&fit=crop',
       TRUE, CURRENT_DATE + 19, '18:00', 'Pantalla gigante', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Selección Colombia en Pantalla Gigante');

-- ------------------------------------------------------------
-- Licores: marcas muy vendidas en Colombia
-- Precios y fotos de licoresmedellin.com, consultados el 2026-11-09
-- Fotos de esa tienda, sin fondo, guardadas en static/img/licores/.
-- ------------------------------------------------------------

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Aguardiente Antioqueño Tapa Verde 750 ml',
       'Aguardiente colombiano de la Fábrica de Licores de Antioquia, el más vendido del país.',
       53900, 'aguardiente',
       '/static/img/licores/aguardiente-antioqueno-tapa-verde-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Aguardiente Antioqueño Tapa Verde 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Aguardiente Antioqueño Tapa Azul 750 ml',
       'Versión sin azúcar del aguardiente de la Fábrica de Licores de Antioquia.',
       55900, 'aguardiente',
       '/static/img/licores/aguardiente-antioqueno-tapa-azul-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Aguardiente Antioqueño Tapa Azul 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Aguardiente Amarillo de Manzanares 750 ml',
       'Aguardiente de la Industria Licorera de Caldas.',
       57900, 'aguardiente',
       '/static/img/licores/aguardiente-amarillo-de-manzanares-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Aguardiente Amarillo de Manzanares 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Ron Medellín 3 Años Añejo 750 ml',
       'Ron añejo colombiano de la Fábrica de Licores de Antioquia.',
       56900, 'ron',
       '/static/img/licores/ron-medellin-3-anos-anejo-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Ron Medellín 3 Años Añejo 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Ron Viejo de Caldas 3 Años Tradicional 750 ml',
       'Ron colombiano de la Industria Licorera de Caldas.',
       58900, 'ron',
       '/static/img/licores/ron-viejo-de-caldas-3-anos-tradicional-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Ron Viejo de Caldas 3 Años Tradicional 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Ron Viejo de Caldas 8 Años Carta de Oro 750 ml',
       'Ron colombiano añejado 8 años, de la Industria Licorera de Caldas.',
       102900, 'ron',
       '/static/img/licores/ron-viejo-de-caldas-8-anos-carta-de-oro-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Ron Viejo de Caldas 8 Años Carta de Oro 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Old Parr 12 Años 750 ml',
       'Whisky escocés de mezcla, añejado 12 años.',
       159000, 'whiskey',
       '/static/img/licores/whisky-old-parr-12-anos-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Old Parr 12 Años 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Buchanan''s Deluxe 12 Años 750 ml',
       'Whisky escocés de mezcla, añejado 12 años.',
       185900, 'whiskey',
       '/static/img/licores/whisky-buchanan-s-deluxe-12-anos-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Buchanan''s Deluxe 12 Años 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Buchanan''s Master 750 ml',
       'Whisky escocés de mezcla de la casa Buchanan''s.',
       217900, 'whiskey',
       '/static/img/licores/whisky-buchanan-s-master-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Buchanan''s Master 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Johnnie Walker Red Label 700 ml',
       'Whisky escocés de mezcla.',
       79900, 'whiskey',
       '/static/img/licores/whisky-johnnie-walker-red-label-700-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Johnnie Walker Red Label 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Johnnie Walker Black Label 700 ml',
       'Whisky escocés de mezcla, añejado 12 años.',
       172900, 'whiskey',
       '/static/img/licores/whisky-johnnie-walker-black-label-700-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Johnnie Walker Black Label 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Vodka Absolut 700 ml',
       'Vodka sueco.',
       93000, 'vodka',
       '/static/img/licores/vodka-absolut-700-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Vodka Absolut 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Vodka Smirnoff N° 21 700 ml',
       'Vodka clásico de la marca Smirnoff.',
       111000, 'vodka',
       '/static/img/licores/vodka-smirnoff-n-21-700-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Vodka Smirnoff N° 21 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Tequila José Cuervo Especial Reposado 750 ml',
       'Tequila mexicano reposado.',
       98900, 'tequila',
       '/static/img/licores/tequila-jose-cuervo-especial-reposado-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Tequila José Cuervo Especial Reposado 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Tequila José Cuervo Especial Silver 750 ml',
       'Tequila mexicano plateado.',
       98900, 'tequila',
       '/static/img/licores/tequila-jose-cuervo-especial-silver-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Tequila José Cuervo Especial Silver 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Tequila Don Julio Blanco 700 ml',
       'Tequila mexicano blanco.',
       271900, 'tequila',
       '/static/img/licores/tequila-don-julio-blanco-700-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Tequila Don Julio Blanco 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Champagne Moët & Chandon Brut 750 ml',
       'Champagne francés brut.',
       563900, 'champagne',
       '/static/img/licores/champagne-moet-chandon-brut-750-ml.webp',
       TRUE
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Champagne Moët & Chandon Brut 750 ml');

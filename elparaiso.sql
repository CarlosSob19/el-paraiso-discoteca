-- ============================================================
-- EL PARAÍSO — Discoteca Montería
-- Esquema y datos iniciales para MySQL 5.7+ / 8.x / MariaDB 10.3+
--
-- Generado a partir de los modelos de app.py.
-- Se puede ejecutar varias veces: no borra ni duplica datos.
--
-- Importante: selecciona primero la base de datos de destino.
-- El usuario administrador NO está aquí a propósito: lo crea
-- app.py al arrancar, con la contraseña de ADMIN_PASSWORD.
-- ============================================================

SET NAMES utf8mb4;

-- ------------------------------------------------------------
-- Tablas
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS usuarios (
    id            INT          NOT NULL AUTO_INCREMENT,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(120) NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    es_admin      BOOLEAN      DEFAULT FALSE,
    creado_en     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuarios_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS generos_musicales (
    id          INT         NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(50) NOT NULL,
    slug        VARCHAR(50) NOT NULL,
    descripcion TEXT,
    PRIMARY KEY (id),
    UNIQUE KEY uq_generos_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS eventos (
    id               INT          NOT NULL AUTO_INCREMENT,
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    precio_general   DOUBLE       NOT NULL,
    precio_vip       DOUBLE       NOT NULL,
    precio_palco     DOUBLE       NOT NULL,
    precio_backstage DOUBLE       NOT NULL,
    precio_king      DOUBLE       NOT NULL,
    cupos            INT          DEFAULT 500,
    imagen           VARCHAR(200) DEFAULT 'default.jpg',
    genero_id        INT          NOT NULL,
    destacado        BOOLEAN      DEFAULT FALSE,
    fecha_evento     DATE         NOT NULL,
    hora_evento      VARCHAR(10)  DEFAULT '22:00',
    artista          VARCHAR(100),
    ubicacion        VARCHAR(100) DEFAULT 'El Paraíso - Montería',
    creado_en        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_eventos_fecha (fecha_evento),
    CONSTRAINT fk_eventos_genero FOREIGN KEY (genero_id) REFERENCES generos_musicales (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS imagenes_galeria (
    id           INT          NOT NULL AUTO_INCREMENT,
    titulo       VARCHAR(100) NOT NULL,
    categoria    VARCHAR(50)  DEFAULT 'general',
    imagen_url   VARCHAR(300) NOT NULL,
    fecha_evento DATE,
    orden        INT          DEFAULT 0,
    activa       BOOLEAN      DEFAULT TRUE,
    creado_en    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS promociones (
    id                   INT          NOT NULL AUTO_INCREMENT,
    codigo               VARCHAR(20)  NOT NULL,
    nombre               VARCHAR(100) NOT NULL,
    descripcion          TEXT,
    descuento_porcentaje INT          DEFAULT 0,
    descuento_valor      DOUBLE       DEFAULT 0,
    tipo_entrada         VARCHAR(20),
    usos_maximos         INT          DEFAULT 100,
    usos_actuales        INT          DEFAULT 0,
    fecha_inicio         DATE,
    fecha_fin            DATE,
    activa               BOOLEAN      DEFAULT TRUE,
    creado_en            DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_promociones_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS licores (
    id          INT          NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio      DOUBLE       NOT NULL,
    categoria   VARCHAR(50)  DEFAULT 'whiskey',
    imagen      VARCHAR(300) DEFAULT 'default.jpg',
    disponible  BOOLEAN      DEFAULT TRUE,
    creado_en   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reservas_mesa (
    id          INT          NOT NULL AUTO_INCREMENT,
    mesa_id     VARCHAR(20)  NOT NULL,
    mesa_zona   VARCHAR(50)  NOT NULL,
    mesa_precio DOUBLE       NOT NULL DEFAULT 0,
    fecha       DATE         NOT NULL,
    personas    INT          NOT NULL DEFAULT 1,
    nombre      VARCHAR(100) NOT NULL,
    telefono    VARCHAR(30)  NOT NULL,
    email       VARCHAR(120) NOT NULL,
    notas       TEXT,
    estado      VARCHAR(20)  DEFAULT 'pendiente',
    usuario_id  INT,
    creado_en   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_reservas_fecha (fecha),
    CONSTRAINT fk_reservas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ordenes (
    id           INT         NOT NULL AUTO_INCREMENT,
    usuario_id   INT         NOT NULL,
    total        DOUBLE      DEFAULT 0,
    estado       VARCHAR(20) DEFAULT 'pendiente',
    tipo_entrada VARCHAR(20) DEFAULT 'general',
    creado_en    DATETIME    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_ordenes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- evento_id es NULL cuando el ítem es una reserva de mesa
CREATE TABLE IF NOT EXISTS items_orden (
    id              INT         NOT NULL AUTO_INCREMENT,
    orden_id        INT         NOT NULL,
    evento_id       INT,
    cantidad        INT         NOT NULL,
    precio_unitario DOUBLE      NOT NULL,
    tipo_entrada    VARCHAR(20) DEFAULT 'general',
    PRIMARY KEY (id),
    CONSTRAINT fk_items_orden  FOREIGN KEY (orden_id)  REFERENCES ordenes (id),
    CONSTRAINT fk_items_evento FOREIGN KEY (evento_id) REFERENCES eventos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Datos iniciales (los mismos que crea init_db() en app.py)
-- ------------------------------------------------------------

INSERT IGNORE INTO generos_musicales (nombre, slug, descripcion) VALUES
    ('Crossover',          'crossover',   'Salsa, Vallenato, Merengue y más en una sola noche'),
    ('Reggaetón & Urbano', 'reggaeton',   'Lo más candente del género urbano'),
    ('Electrónica',        'electronica', 'House, Techno y Latin House'),
    ('Dembow',             'dembow',      'El ritmo que está rompiendo en toda Colombia'),
    ('Champeta',           'champeta',    'El sonido autóctono de la Costa Caribe');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Noche de Crossover',
       'La mejor noche de salsa, vallenato y merengue de Montería. Con DJ Pipe y la orquesta Costa Brava en vivo.',
       30000, 60000, 120000, 200000, 350000, 500, g.id,
       'https://images.unsplash.com/photo-1740572569816-9c437c4b9c4d?q=80&w=1170&auto=format&fit=crop',
       TRUE, CURDATE() + INTERVAL 5 DAY, '22:00', 'DJ Pipe & Costa Brava', 'El Paraíso - Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Noche de Crossover');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Reggaetón Night',
       'Lo más candente del género urbano. Bad Bunny, Feid, Karol G y más en una noche inolvidable.',
       35000, 70000, 140000, 220000, 380000, 600, g.id,
       'https://zumbido.cl/wp-content/uploads/2024/08/J-Alvarez-2.jpg',
       TRUE, CURDATE() + INTERVAL 12 DAY, '23:00', 'DJ Urbano & MC Karibe', 'El Paraíso - Montería'
FROM generos_musicales g
WHERE g.slug = 'reggaeton'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Reggaetón Night');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Electro Paradise',
       'Noche de electrónica con los mejores DJs de la región. Luces láser, efectos especiales y mucha energía.',
       40000, 80000, 150000, 250000, 400000, 400, g.id,
       'https://tse2.mm.bing.net/th/id/OIP.0iJTnYNpez6CU0wWfeBKvAHaE7?r=0&rs=1&pid=ImgDetMain',
       TRUE, CURDATE() + INTERVAL 19 DAY, '23:30', 'DJ Neon & Laser Crew', 'El Paraíso - Montería'
FROM generos_musicales g
WHERE g.slug = 'electronica'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Electro Paradise');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Dembow Explosion',
       'El ritmo del momento. Una noche llena de perreo intenso y los mejores éxitos del dembow colombiano.',
       25000, 50000, 100000, 180000, 320000, 700, g.id,
       'https://tse1.mm.bing.net/th/id/OIP.zLPUwqKqg7n86YpRZ8WsJAHaFv?r=0&rs=1&pid=ImgDetMain',
       FALSE, CURDATE() + INTERVAL 8 DAY, '22:30', 'DJ Dembow & La Banda', 'El Paraíso - Montería'
FROM generos_musicales g
WHERE g.slug = 'dembow'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Dembow Explosion');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Champeta Classics',
       'El sonido autóctono de la Costa Caribe. Una noche para bailar champeta hasta el amanecer.',
       20000, 45000, 90000, 160000, 280000, 800, g.id,
       'https://tse4.mm.bing.net/th/id/OIP.L-dzQVOagzvJ8hkqLl0Q8gHaE8?r=0&rs=1&pid=ImgDetMain',
       FALSE, CURDATE() + INTERVAL 15 DAY, '21:00', 'Grupo Niche Champetero', 'El Paraíso - Montería'
FROM generos_musicales g
WHERE g.slug = 'champeta'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Champeta Classics');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'VIP Experience',
       'Noche exclusiva con open bar, servicio personalizado y las mejores vistas del club.',
       50000, 100000, 180000, 300000, 450000, 300, g.id,
       'https://images.unsplash.com/photo-1647314620432-7e27193891cb?q=80&w=1169&auto=format&fit=crop',
       TRUE, CURDATE() + INTERVAL 26 DAY, '22:00', 'Artista Sorpresa', 'El Paraíso - Montería'
FROM generos_musicales g
WHERE g.slug = 'reggaeton'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'VIP Experience');

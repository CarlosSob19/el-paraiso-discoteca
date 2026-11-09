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
    ubicacion        VARCHAR(100) DEFAULT 'Calle 9 Mz 15 Lote 10, Montería',
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

-- evento_id y licor_id son NULL cuando el ítem es una reserva de mesa
CREATE TABLE IF NOT EXISTS items_orden (
    id              INT         NOT NULL AUTO_INCREMENT,
    orden_id        INT         NOT NULL,
    evento_id       INT,
    cantidad        INT         NOT NULL,
    precio_unitario DOUBLE      NOT NULL,
    tipo_entrada    VARCHAR(20) DEFAULT 'general',
    licor_id        INT,
    PRIMARY KEY (id),
    CONSTRAINT fk_items_licor  FOREIGN KEY (licor_id)  REFERENCES licores (id),
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
SELECT 'Éxitos de la Champeta',
       'Disfruta una noche de éxitos de la champeta en Paraíso Club.',
       20000, 45000, 90000, 160000, 280000, 300, g.id,
       'https://images.unsplash.com/photo-1740572569816-9c437c4b9c4d?q=80&w=1170&auto=format&fit=crop',
       TRUE, CURDATE() + INTERVAL 5 DAY, '21:00', 'Paraíso Club', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'champeta'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Éxitos de la Champeta');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Noche de Locura',
       'Llega que sí es para eso: rumba toda la noche en Paraíso Club.',
       30000, 60000, 120000, 200000, 350000, 300, g.id,
       'https://images.unsplash.com/photo-1647314620432-7e27193891cb?q=80&w=1169&auto=format&fit=crop',
       TRUE, CURDATE() + INTERVAL 8 DAY, '22:00', 'Paraíso Club', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Noche de Locura');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'El Clásico Español en Pantalla Gigante',
       'Vive el clásico español en pantalla gigante en Paraíso Club.',
       20000, 45000, 90000, 160000, 280000, 300, g.id,
       'https://images.unsplash.com/photo-1647314620432-7e27193891cb?q=80&w=1169&auto=format&fit=crop',
       TRUE, CURDATE() + INTERVAL 12 DAY, '14:00', 'Pantalla gigante', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'El Clásico Español en Pantalla Gigante');

INSERT INTO eventos (nombre, descripcion, precio_general, precio_vip, precio_palco, precio_backstage, precio_king, cupos, genero_id, imagen, destacado, fecha_evento, hora_evento, artista, ubicacion)
SELECT 'Selección Colombia en Pantalla Gigante',
       'Vamos todos, apoyemos a la Selección Colombia. Te esperamos en Paraíso Club Montería.',
       20000, 45000, 90000, 160000, 280000, 300, g.id,
       'https://images.unsplash.com/photo-1740572569816-9c437c4b9c4d?q=80&w=1170&auto=format&fit=crop',
       TRUE, CURDATE() + INTERVAL 19 DAY, '18:00', 'Pantalla gigante', 'Calle 9 Mz 15 Lote 10, Montería'
FROM generos_musicales g
WHERE g.slug = 'crossover'
  AND NOT EXISTS (SELECT 1 FROM eventos e WHERE e.nombre = 'Selección Colombia en Pantalla Gigante');

-- ------------------------------------------------------------
-- Licores: marcas muy vendidas en Colombia
-- Precios y fotos de licoresmedellin.com, consultados el 2026-11-09
-- Las fotos pertenecen a esa tienda; se enlazan, no se copian.
-- ------------------------------------------------------------

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Aguardiente Antioqueño Tapa Verde 750 ml',
       'Aguardiente colombiano de la Fábrica de Licores de Antioquia, el más vendido del país.',
       53900, 'aguardiente',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/AGUARDIENTE_ANTIOQUENO_TAPA_VERDE_BOTELLA_750ML.jpg?v=1793051613',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Aguardiente Antioqueño Tapa Verde 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Aguardiente Antioqueño Tapa Azul 750 ml',
       'Versión sin azúcar del aguardiente de la Fábrica de Licores de Antioquia.',
       55900, 'aguardiente',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/aguardiente-antioqueno-tapa-azul-botella-750mlaguardiente-antioqueno-tapa-azul-botella-750mlaguardiente-antioquenolicores-medellin-2388907.jpg?v=1759123399',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Aguardiente Antioqueño Tapa Azul 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Aguardiente Amarillo de Manzanares 750 ml',
       'Aguardiente de la Industria Licorera de Caldas.',
       57900, 'aguardiente',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/aguardiente-amarillo-de-manzanares-botella-750mlaguardiente-amarillo-de-manzanares-botella-750mlindustria-licorera-de-caldaslicores-medellin-7021712.jpg?v=1765494233',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Aguardiente Amarillo de Manzanares 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Ron Medellín 3 Años Añejo 750 ml',
       'Ron añejo colombiano de la Fábrica de Licores de Antioquia.',
       56900, 'ron',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/ron-medellin-3-anos-anejo-botella-750mlron-medellin-3-anos-anejo-botella-750mlron-medellinlicores-medellin-8660657.jpg?v=1759123251',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Ron Medellín 3 Años Añejo 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Ron Viejo de Caldas 3 Años Tradicional 750 ml',
       'Ron colombiano de la Industria Licorera de Caldas.',
       58900, 'ron',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/ron-viejo-de-caldas-3-anos-tradicional-botella-750mlron-viejo-de-caldas-3-anos-tradicional-botella-750mlron-viejo-de-caldaslicores-medellin-1250736.jpg?v=1759123369',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Ron Viejo de Caldas 3 Años Tradicional 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Ron Viejo de Caldas 8 Años Carta de Oro 750 ml',
       'Ron colombiano añejado 8 años, de la Industria Licorera de Caldas.',
       102900, 'ron',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/ron-viejo-de-caldas-8-anos-carta-de-oro-botella-750mlron-viejo-de-caldas-8-anos-carta-de-oro-botella-750mlron-viejo-de-caldaslicores-medellin-8336735.jpg?v=1759123370',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Ron Viejo de Caldas 8 Años Carta de Oro 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Old Parr 12 Años 750 ml',
       'Whisky escocés de mezcla, añejado 12 años.',
       159000, 'whiskey',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-old-parr-12-anos-botella-750mlwhisky-old-parr-12-anos-botella-750mlold-parrlicores-medellin-1357166.jpg?v=1759122553',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Old Parr 12 Años 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Buchanan''s Deluxe 12 Años 750 ml',
       'Whisky escocés de mezcla, añejado 12 años.',
       185900, 'whiskey',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-buchanans-deluxe-12-anos-botella-750mlwhisky-buchanans-deluxe-12-anos-botella-750mlbuchananslicores-medellin-2276071.jpg?v=1765490172',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Buchanan''s Deluxe 12 Años 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Buchanan''s Master 750 ml',
       'Whisky escocés de mezcla de la casa Buchanan''s.',
       217900, 'whiskey',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-buchanans-master-botella-750mlwhisky-buchanans-master-botella-750mlbuchananslicores-medellin-3145715.jpg?v=1759122553',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Buchanan''s Master 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Johnnie Walker Red Label 700 ml',
       'Whisky escocés de mezcla.',
       79900, 'whiskey',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-johnnie-walker-red-label-botella-700mlwhisky-johnnie-walker-red-label-botella-700mljohnnie-walkerlicores-medellin-9011566.jpg?v=1759122553',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Johnnie Walker Red Label 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Whisky Johnnie Walker Black Label 700 ml',
       'Whisky escocés de mezcla, añejado 12 años.',
       172900, 'whiskey',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/WHISKY_JOHNNIE_WALKER_BLACK_LABEL_BOTELLA_700ML.jpg?v=1764364351',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Whisky Johnnie Walker Black Label 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Vodka Absolut 700 ml',
       'Vodka sueco.',
       93000, 'vodka',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/vodka-absolut-botella-700mlvodka-absolut-botella-700mlabsolut-vodkalicores-medellin-2766595.jpg?v=1759122630',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Vodka Absolut 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Vodka Smirnoff N° 21 700 ml',
       'Vodka clásico de la marca Smirnoff.',
       111000, 'vodka',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/vodka-smirnoff-botella-700mlvodka-smirnoff-botella-700mlsmirnofflicores-medellin-2446150.jpg?v=1759122630',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Vodka Smirnoff N° 21 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Tequila José Cuervo Especial Reposado 750 ml',
       'Tequila mexicano reposado.',
       98900, 'tequila',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/tequila-jose-cuervo-especial-reposado-botella-750mltequila-jose-cuervo-especial-reposado-botella-750mljose-cuervolicores-medellin-5501636.jpg?v=1776272385',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Tequila José Cuervo Especial Reposado 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Tequila José Cuervo Especial Silver 750 ml',
       'Tequila mexicano plateado.',
       98900, 'tequila',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/tequila-jose-cuervo-especial-silver-botella-750mltequila-jose-cuervo-especial-silver-botella-750mljose-cuervolicores-medellin-2367928.jpg?v=1759123228',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Tequila José Cuervo Especial Silver 750 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Tequila Don Julio Blanco 700 ml',
       'Tequila mexicano blanco.',
       271900, 'tequila',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/tequila-don-julio-blanco-botella-700mltequila-don-julio-blanco-botella-700mltequila-don-juliolicores-medellin-3471506.jpg?v=1764878992',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Tequila Don Julio Blanco 700 ml');

INSERT INTO licores (nombre, descripcion, precio, categoria, imagen, disponible)
SELECT 'Champagne Moët & Chandon Brut 750 ml',
       'Champagne francés brut.',
       563900, 'champagne',
       'https://cdn.shopify.com/s/files/1/0602/6376/0011/files/champagne-moet-chandon-brut-botella-750mlchampagne-moet-chandon-brut-botella-750mlmoet-hennessylicores-medellin-2709495.jpg?v=1759122554',
       TRUE
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM licores l WHERE l.nombre = 'Champagne Moët & Chandon Brut 750 ml');

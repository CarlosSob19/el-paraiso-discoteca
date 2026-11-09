# EL PARAÍSO — Discoteca Montería

Aplicación web para la discoteca **El Paraíso** de Montería, Colombia: venta de entradas, carta de licores, reservas de mesa y panel de administración.

- **Sitio publicado:** https://el-paraiso-discoteca.onrender.com
- **Integrantes:** Carlos Sobrado y Jorge Mercado
- **Documentación completa:** [docs/Documentacion_El_Paraiso.pdf](docs/Documentacion_El_Paraiso.pdf)

## Funcionalidades

- Registro, inicio y cierre de sesión seguros.
- Catálogo de eventos filtrado por género musical y cinco tipos de entrada.
- Carta de licores, carrito y compra con pago simulado.
- Reserva de mesas sobre un mapa por zonas.
- Panel de administración: eventos, licores, promociones, galería, usuarios y reservas.
- Seguridad: contraseñas con hash, tokens CSRF, límite de intentos y control de acceso por rol.

## Tecnologías

- Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF y Flask-Limiter
- PostgreSQL en producción; SQLite o MySQL en local
- HTML5, CSS3, JavaScript, Jinja2, GSAP y Lenis
- Render como servidor web

## Estructura

```
├── app.py                  Modelos, rutas, seguridad e inicialización
├── elparaiso.sql           Script de la base para MySQL / MariaDB
├── elparaiso_postgres.sql  Script de la base para PostgreSQL
├── requirements.txt        Dependencias
├── docs/                   Documentación en PDF
├── templates/              Páginas HTML (Jinja2), partials/ y admin/
└── static/                 css/, js/ e imágenes
```

## Ejecución local

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La aplicación queda en `http://127.0.0.1:5000`. Sin configuración usa SQLite y crea sola las tablas y los datos iniciales.

## Variables de entorno

Se definen en un archivo `.env` (que no se sube al repositorio) o en el panel de Render:

| Variable | Uso |
|----------|-----|
| `SECRET_KEY` | Firma de las sesiones; debe ser aleatoria en producción |
| `DATABASE_URL` | Conexión a la base de datos |
| `ADMIN_PASSWORD` | Contraseña inicial del administrador |

El administrador se crea la primera vez que arranca la aplicación con el correo `admin@elparaiso.com`, y entra por `/login`.

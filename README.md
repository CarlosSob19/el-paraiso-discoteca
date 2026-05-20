# EL PARAÍSO — Discoteca Montería

Aplicación web de venta de entradas para la discoteca **El Paraíso** en Montería, Colombia. Incluye catálogo de eventos, compra de entradas por tipo (General, VIP, Palco, Backstage, King), registro de usuarios, checkout y panel de administración para gestionar eventos.

## Descripción del proyecto

Este proyecto es una plataforma completa de venta de entradas desarrollada con Flask y SQLite. Está diseñada para ofrecer:

- Navegación por eventos y géneros musicales (Crossover, Reggaetón, Electrónica, Dembow, Champeta).
- Páginas de detalle de evento con múltiples tipos de entrada y precios.
- Carrito dinámico que funciona para usuarios anónimos y registrados.
- Autenticación de usuarios con registro, login y logout.
- Checkout seguro para usuarios registrados con múltiples métodos de pago colombianos.
- Panel de administración para crear, editar y eliminar eventos.
- Inicialización automática de la base de datos con datos de ejemplo y usuario administrador.

## Funcionalidades principales

- **Catálogo de eventos** filtrado por género musical.
- **5 tipos de entrada**: General ($30.000), VIP ($60.000), Palco ($120.000), Backstage ($200.000), King ($350.000).
- Carrito persistente en sesión para usuarios no autenticados.
- Migración del carrito de sesión a la base de datos al iniciar sesión.
- Gestión de cupos al comprar entradas.
- Dashboard admin con métricas de eventos, usuarios y ventas.
- CRUD completo de eventos desde el panel de administración.
- Login obligatorio para checkout y administración.

## Tecnologías usadas

- Python 3.11+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite por defecto
- HTML5, CSS3, JavaScript
- GSAP para animaciones
- Lenis Smooth Scroll
- python-dotenv
- PyMySQL (compatibilidad con MySQL)

## Estructura del proyecto

```
├── app.py                 — Aplicación Flask principal, modelos, rutas y logica
├── templates/             — Vistas HTML con Jinja2
│   ├── base.html
│   ├── index.html
│   ├── eventos.html
│   ├── evento.html
│   ├── carrito.html
│   ├── checkout.html
│   ├── login.html
|   ├── confirmacion.html
|   ├── faq.html
|   ├── confirmacion.html
|   ├── galeria.html
|   ├── licores.html
|   ├── mis_ordenes.html
│   ├── registro.html
|   ├── politica.html
|   ├── recuperar_password.html
|   ├── registro.html
|   ├── reservas.html
|   ├── reset_password.html
|   ├── .terminoshtml
│   ├── partials/
│   │   ├── nav.html
│   │   ├── footer.html
│   │   └── preloader.html
│   └── admin/
│       ├── dashboard.html
│       ├── eventos.html
│       ├── crear_evento.html
|       ├── crear_licor.html
|       ├── crear_promocion.html
|       ├── editar_licor.html
|       ├── eventos.html
|       ├── galeria.html
|       ├── licores.html
|       ├── promociones.html
│       └── editar_evento.html
├── static/
│   ├── css/style.css      — Estilos nightclub neón
│   └── js/main.js         — Animaciones y lógica del carrito
└── requirements.txt       — Dependencias
```

## Configuración y ejecución

1. Clonar el repositorio:

```bash
git clone <repo-url>
cd el-paraiso
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate   # Windows
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear un archivo `.env` opcional:

```env
SECRET_KEY=tu_clave_secreta
DATABASE_URL=sqlite:///elparaiso.db
```

5. Ejecutar la aplicación:

```bash
python app.py
```

6. Abrir en el navegador:

```
http://127.0.0.1:5000
```

## Usuario administrador

Al iniciar la aplicación por primera vez, se crea automáticamente un administrador:

- **Email:** `admin@elparaiso.com`
- **Contraseña:** `admin123`

Este usuario puede acceder al panel de administración en `/admin`.

## Rutas principales

- `/` — Página inicial con eventos destacados.
- `/eventos` — Calendario completo de eventos.
- `/eventos/<slug>` — Eventos filtrados por género musical.
- `/evento/<id>` — Detalle del evento con tipos de entrada.
- `/carrito` — Carrito de entradas.
- `/checkout` — Confirmar compra (requiere login).
- `/login` — Iniciar sesión.
- `/registro` — Registrar nuevo usuario.
- `/logout` — Cerrar sesión.
- `/admin` — Dashboard de administración.
- `/admin/eventos` — Gestión de eventos.
- `/admin/eventos/crear` — Crear nuevo evento.
- `/admin/eventos/editar/<id>` — Editar evento.

## Tipos de entrada y precios

| Tipo | Precio (COP) | Características |
|------|-------------|-----------------|
| General | $30.000 | Acceso pista principal |
| VIP | $60.000 | Zona VIP, acceso preferencial |
| Palco | $120.000 | Mesa compartida, 4 personas, 1 botella |
| Backstage | $200.000 | Acceso backstage, meet & greet, barra libre |
| King | $350.000 | Mesa privada, 8 personas, 2 botellas, servicio exclusivo |

## Géneros musicales

- **Crossover**: Salsa, Vallenato, Merengue
- **Reggaetón & Urbano**: Bad Bunny, Feid, Karol G
- **Electrónica**: House, Techno, Latin House
- **Dembow**: Ritmo del momento en Colombia
- **Champeta**: Sonido autóctono de la Costa Caribe

## Notas adicionales

- El proyecto usa `Flask-Login` para manejar sesiones de usuario.
- El checkout descuenta cupos de los eventos y marca la orden como `pagado`.
- La base de datos se inicializa automáticamente al arrancar la app si no existe.
- Las imágenes de eventos se almacenan en `static/img/eventos/`.


**El Paraíso** — Montería, Colombia 🇨🇴  
*La rumba no para.*

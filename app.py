import os
import pymysql
pymysql.install_as_MySQLdb()

import re
from datetime import datetime, date
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY']                = os.getenv('SECRET_KEY', 'dev-secret-key')
db_url = os.getenv('DATABASE_URL', 'sqlite:///elparaiso.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI']   = db_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']             = 'static/img/eventos'
app.config['WTF_CSRF_TIME_LIMIT']       = None
app.config['SESSION_COOKIE_SAMESITE']   = 'Lax'
app.config['REMEMBER_COOKIE_HTTPONLY']  = True
# En Render la página va por HTTPS: las cookies solo viajan cifradas
app.config['SESSION_COOKIE_SECURE']     = bool(os.getenv('RENDER'))
app.config['REMEMBER_COOKIE_SECURE']    = bool(os.getenv('RENDER'))

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf          = CSRFProtect(app)
limiter       = Limiter(get_remote_address, app=app, storage_uri='memory://')

# Flask-Mail es opcional: instala con  pip install flask-mail  y configura
# MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD en tu .env
try:
    from flask_mail import Mail, Message as MailMessage
    mail = Mail(app)
except ImportError:
    mail = None
login_manager.login_view         = 'login'
login_manager.login_message      = 'Inicia sesión para acceder.'
login_manager.login_message_category = 'warning'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ── Constantes ────────────────────────────────────────────────────────────────
TIPOS_ENTRADA       = {'general', 'vip', 'palco', 'backstage', 'king'}
ALLOWED_EXTENSIONS  = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
ESTADOS_RESERVA     = {'pendiente', 'confirmada', 'cancelada'}
UBICACION           = 'Calle 9 Mz 15 Lote 10, Montería'

MESAS = [
    {'id': 'G-01', 'zona': 'General',    'capacidad': 4,  'precio': 0},
    {'id': 'G-02', 'zona': 'General',    'capacidad': 4,  'precio': 0},
    {'id': 'G-03', 'zona': 'General',    'capacidad': 6,  'precio': 0},
    {'id': 'V-01', 'zona': 'VIP',        'capacidad': 4,  'precio': 60000},
    {'id': 'V-02', 'zona': 'VIP',        'capacidad': 6,  'precio': 60000},
    {'id': 'V-03', 'zona': 'VIP',        'capacidad': 4,  'precio': 60000},
    {'id': 'P-01', 'zona': 'Palco',      'capacidad': 4,  'precio': 120000},
    {'id': 'P-02', 'zona': 'Palco',      'capacidad': 8,  'precio': 120000},
    {'id': 'B-01', 'zona': 'Backstage',  'capacidad': 6,  'precio': 200000},
    {'id': 'K-01', 'zona': 'King',       'capacidad': 8,  'precio': 350000},
    {'id': 'K-02', 'zona': 'King',       'capacidad': 10, 'precio': 350000},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def allowed_file(filename):
    """Valida que el archivo tenga una extensión permitida."""
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _precio_entrada(evt, tipo):
    """Devuelve el precio del evento según el tipo de entrada."""
    return getattr(evt, f'precio_{tipo}', evt.precio_general)


def _validar_usuario(nombre, email):
    """Devuelve un mensaje de error, o None si los datos son válidos."""
    if not nombre or len(nombre) > 100:
        return 'El nombre es obligatorio (máximo 100 caracteres).'
    if len(email) > 120 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return 'Escribe un email válido.'
    return None


def _cantidad_valida(cantidad):
    """La cantidad debe ser un entero entre 1 y 99."""
    return type(cantidad) is int and 1 <= cantidad <= 99


def _destino_seguro(url):
    """Solo permite redirigir a páginas internas del sitio."""
    return bool(url) and url.startswith('/') and not url.startswith(('//', '/\\'))


# ==================== MODELOS ====================

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    es_admin      = db.Column(db.Boolean, default=False)
    creado_en     = db.Column(db.DateTime, default=datetime.utcnow)
    ordenes       = db.relationship('Orden', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class GeneroMusical(db.Model):
    __tablename__ = 'generos_musicales'
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(50), nullable=False)
    slug        = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    eventos     = db.relationship('Evento', backref='genero', lazy=True)


class Evento(db.Model):
    __tablename__      = 'eventos'
    id                 = db.Column(db.Integer, primary_key=True)
    nombre             = db.Column(db.String(150), nullable=False)
    descripcion        = db.Column(db.Text)
    precio_general     = db.Column(db.Float, nullable=False)
    precio_vip         = db.Column(db.Float, nullable=False)
    precio_palco       = db.Column(db.Float, nullable=False)
    precio_backstage   = db.Column(db.Float, nullable=False)
    precio_king        = db.Column(db.Float, nullable=False)
    cupos              = db.Column(db.Integer, default=500)
    imagen             = db.Column(db.String(200), default='default.jpg')
    genero_id          = db.Column(db.Integer, db.ForeignKey('generos_musicales.id'), nullable=False)
    destacado          = db.Column(db.Boolean, default=False)
    fecha_evento       = db.Column(db.Date, nullable=False)
    hora_evento        = db.Column(db.String(10), default='22:00')
    artista            = db.Column(db.String(100))
    ubicacion          = db.Column(db.String(100), default=UBICACION)
    creado_en          = db.Column(db.DateTime, default=datetime.utcnow)
    items              = db.relationship('ItemOrden', backref='evento', lazy=True)

    @property
    def precio_minimo(self):
        return min(self.precio_general, self.precio_vip, self.precio_palco,
                   self.precio_backstage, self.precio_king)

    @property
    def precio_maximo(self):
        return max(self.precio_general, self.precio_vip, self.precio_palco,
                   self.precio_backstage, self.precio_king)


class ImagenGaleria(db.Model):
    __tablename__ = 'imagenes_galeria'
    id          = db.Column(db.Integer, primary_key=True)
    titulo      = db.Column(db.String(100), nullable=False)
    categoria   = db.Column(db.String(50), default='general')
    imagen_url  = db.Column(db.String(300), nullable=False)
    fecha_evento = db.Column(db.Date)
    orden       = db.Column(db.Integer, default=0)
    activa      = db.Column(db.Boolean, default=True)
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)


class Promocion(db.Model):
    __tablename__           = 'promociones'
    id                      = db.Column(db.Integer, primary_key=True)
    codigo                  = db.Column(db.String(20), unique=True, nullable=False)
    nombre                  = db.Column(db.String(100), nullable=False)
    descripcion             = db.Column(db.Text)
    descuento_porcentaje    = db.Column(db.Integer, default=0)
    descuento_valor         = db.Column(db.Float, default=0)
    tipo_entrada            = db.Column(db.String(20))
    usos_maximos            = db.Column(db.Integer, default=100)
    usos_actuales           = db.Column(db.Integer, default=0)
    fecha_inicio            = db.Column(db.Date, default=date.today)
    fecha_fin               = db.Column(db.Date)
    activa                  = db.Column(db.Boolean, default=True)
    creado_en               = db.Column(db.DateTime, default=datetime.utcnow)


class Licor(db.Model):
    __tablename__ = 'licores'
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio      = db.Column(db.Float, nullable=False)
    categoria   = db.Column(db.String(50), default='whiskey')
    imagen      = db.Column(db.String(300), default='default.jpg')
    disponible  = db.Column(db.Boolean, default=True)
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)
    items       = db.relationship('ItemOrden', backref='licor', lazy=True)


class ReservaMesa(db.Model):
    __tablename__ = 'reservas_mesa'
    id          = db.Column(db.Integer, primary_key=True)
    mesa_id     = db.Column(db.String(20),  nullable=False)
    mesa_zona   = db.Column(db.String(50),  nullable=False)
    mesa_precio = db.Column(db.Float,       nullable=False, default=0)
    fecha       = db.Column(db.Date,        nullable=False)
    personas    = db.Column(db.Integer,     nullable=False, default=1)
    nombre      = db.Column(db.String(100), nullable=False)
    telefono    = db.Column(db.String(30),  nullable=False)
    email       = db.Column(db.String(120), nullable=False)
    notas       = db.Column(db.Text)
    estado      = db.Column(db.String(20),  default='pendiente')  # pendiente | confirmada | cancelada
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':        self.id,
            'mesa_id':   self.mesa_id,
            'mesa_zona': self.mesa_zona,
            'precio':    self.mesa_precio,
            'fecha':     self.fecha.isoformat(),
            'personas':  self.personas,
            'nombre':    self.nombre,
            'telefono':  self.telefono,
            'email':     self.email,
            'notas':     self.notas or '',
            'estado':    self.estado,
            'creado_en': self.creado_en.isoformat(),
        }


class Orden(db.Model):
    __tablename__ = 'ordenes'
    id           = db.Column(db.Integer, primary_key=True)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    total        = db.Column(db.Float, default=0)
    estado       = db.Column(db.String(20), default='pendiente')
    tipo_entrada = db.Column(db.String(20), default='general')
    creado_en    = db.Column(db.DateTime, default=datetime.utcnow)
    items        = db.relationship('ItemOrden', backref='orden', lazy=True, cascade='all, delete-orphan')


class ItemOrden(db.Model):
    __tablename__    = 'items_orden'
    id               = db.Column(db.Integer, primary_key=True)
    orden_id         = db.Column(db.Integer, db.ForeignKey('ordenes.id'), nullable=False)
    # NULL cuando el ítem es una reserva de mesa (no hay evento asociado)
    evento_id        = db.Column(db.Integer, db.ForeignKey('eventos.id'), nullable=True)
    # Solo tiene valor cuando el ítem es un licor
    licor_id         = db.Column(db.Integer, db.ForeignKey('licores.id'), nullable=True)
    cantidad         = db.Column(db.Integer, nullable=False)
    precio_unitario  = db.Column(db.Float, nullable=False)
    tipo_entrada     = db.Column(db.String(20), default='general')


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            flash('Acceso denegado.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== SEGURIDAD ====================

@app.errorhandler(429)
def demasiados_intentos(e):
    flash('Demasiados intentos. Espera un minuto y vuelve a intentar.', 'danger')
    return redirect(url_for('login'))


@app.errorhandler(CSRFError)
def csrf_invalido(e):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': 'Sesión expirada. Recarga la página.'}), 400
    flash('Tu sesión expiró. Intenta de nuevo.', 'warning')
    return redirect(url_for('index'))


@app.after_request
def no_guardar_paginas_privadas(response):
    # Evita que el botón "atrás" muestre páginas privadas después de cerrar sesión
    if current_user.is_authenticated and not request.path.startswith('/static'):
        response.headers['Cache-Control'] = 'no-store'
    return response


# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_globals():
    generos = GeneroMusical.query.all()
    if current_user.is_authenticated:
        orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
        cart_count = sum(i.cantidad for i in orden.items) if orden else 0
    else:
        cart = session.get('carrito', {})
        cart_count = sum(
            v.get('cantidad', 1) if isinstance(v, dict) else v
            for v in cart.values()
        )
    return dict(generos_nav=generos, cart_count=cart_count)


# ==================== RUTAS PÚBLICAS ====================

@app.route('/')
def index():
    hoy = date.today()
    destacados = (Evento.query
                  .filter_by(destacado=True)
                  .filter(Evento.fecha_evento >= hoy)
                  .order_by(Evento.fecha_evento)
                  .limit(6).all())
    proximos   = (Evento.query
                  .filter(Evento.fecha_evento >= hoy)
                  .order_by(Evento.fecha_evento)
                  .limit(4).all())
    generos    = GeneroMusical.query.all()
    return render_template('index.html', destacados=destacados, proximos=proximos, generos=generos)


@app.route('/eventos')
@app.route('/eventos/<string:slug>')
def eventos(slug=None):
    genero = GeneroMusical.query.filter_by(slug=slug).first() if slug else None
    hoy = date.today()
    q = Evento.query.filter(Evento.fecha_evento >= hoy)
    if genero:
        q = q.filter_by(genero_id=genero.id)
    eventos_list = q.order_by(Evento.fecha_evento).all()
    return render_template('eventos.html', eventos=eventos_list, genero_actual=genero)


@app.route('/evento/<int:id>')
def evento(id):
    evt = Evento.query.get_or_404(id)
    relacionados = (Evento.query
                    .filter_by(genero_id=evt.genero_id)
                    .filter(Evento.id != id, Evento.fecha_evento >= date.today())
                    .limit(4).all())
    return render_template('evento.html', evento=evt, relacionados=relacionados)


@app.route('/carrito')
def carrito():
    items = []
    total = 0

    if current_user.is_authenticated:
        orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
        if orden:
            for item in orden.items:
                # ── Licor ─────────────────────────────────────────────────────
                if item.licor_id:
                    subtotal = item.precio_unitario * item.cantidad
                    items.append({
                        'id': f'licor_{item.licor_id}', 'nombre': item.licor.nombre,
                        'precio': item.precio_unitario, 'cantidad': item.cantidad,
                        'imagen': item.licor.imagen, 'tipo_entrada': 'LICOR',
                        'subtotal': subtotal, 'fecha': None,
                        'artista': item.licor.categoria.upper(),
                        'es_licor': True, 'es_reserva': False,
                    })
                    total += subtotal
                    continue

                # ── Reserva de mesa (sin evento asociado) ─────────────────────
                if item.tipo_entrada == 'reserva' or item.evento_id is None:
                    subtotal = item.precio_unitario * item.cantidad
                    items.append({
                        'id': item.id, 'nombre': 'Reserva de Mesa',
                        'precio': item.precio_unitario, 'cantidad': item.cantidad,
                        'imagen': 'default.jpg', 'tipo_entrada': 'RESERVA',
                        'subtotal': subtotal, 'fecha': None, 'artista': '',
                        'es_licor': False, 'es_reserva': True,
                    })
                else:
                    # ── Entrada de evento ─────────────────────────────────────
                    subtotal = item.precio_unitario * item.cantidad
                    items.append({
                        'id': item.evento.id, 'nombre': item.evento.nombre,
                        'precio': item.precio_unitario, 'cantidad': item.cantidad,
                        'imagen': item.evento.imagen, 'tipo_entrada': item.tipo_entrada,
                        'subtotal': subtotal, 'fecha': item.evento.fecha_evento,
                        'artista': item.evento.artista,
                        'es_licor': False, 'es_reserva': False,
                    })
                total += subtotal

    else:
        cart = session.get('carrito', {})
        for pid, data in cart.items():
            if isinstance(data, dict):
                cantidad   = data.get('cantidad', 1)
                tipo       = data.get('tipo', 'general')
                licor_id   = data.get('licor_id')
                es_reserva = (tipo == 'reserva')
            else:
                cantidad, tipo, licor_id, es_reserva = data, 'general', None, False

            # ── Reserva en sesión ─────────────────────────────────────────────
            if es_reserva:
                res = data.get('reserva', {})
                precio = res.get('precio', 0)
                items.append({
                    'id': pid,
                    'nombre': f"Mesa {res.get('mesa_id', '')} — {res.get('mesa_zona', '')}",
                    'precio': precio, 'cantidad': 1,
                    'imagen': 'default.jpg', 'tipo_entrada': 'RESERVA',
                    'subtotal': precio, 'fecha': res.get('fecha'),
                    'artista': f"{res.get('personas', '')} personas",
                    'es_licor': False, 'es_reserva': True,
                })
                total += precio
                continue

            # ── Licor en sesión ───────────────────────────────────────────────
            if licor_id:
                licor = Licor.query.get(int(licor_id))
                if licor:
                    subtotal = licor.precio * cantidad
                    items.append({
                        'id': f'licor_{licor.id}', 'nombre': licor.nombre,
                        'precio': licor.precio, 'cantidad': cantidad,
                        'imagen': licor.imagen, 'tipo_entrada': 'LICOR',
                        'subtotal': subtotal, 'fecha': None,
                        'artista': licor.categoria.upper(),
                        'es_licor': True, 'es_reserva': False,
                    })
                    total += subtotal
                continue

            # ── Evento en sesión ──────────────────────────────────────────────
            try:
                evt = Evento.query.get(int(pid))
            except (ValueError, TypeError):
                continue

            if evt:
                precio   = _precio_entrada(evt, tipo)
                subtotal = precio * cantidad
                items.append({
                    'id': evt.id, 'nombre': evt.nombre,
                    'precio': precio, 'cantidad': cantidad,
                    'imagen': evt.imagen, 'tipo_entrada': tipo,
                    'subtotal': subtotal, 'fecha': evt.fecha_evento,
                    'artista': evt.artista,
                    'es_licor': False, 'es_reserva': False,
                })
                total += subtotal

    return render_template('carrito.html', items=items, total=total)


@app.route('/api/carrito/agregar', methods=['POST'])
def agregar_carrito():
    data         = request.get_json()
    evento_id    = data.get('evento_id')
    cantidad     = data.get('cantidad', 1)
    tipo_entrada = data.get('tipo_entrada', 'general')

    if tipo_entrada not in TIPOS_ENTRADA:
        return jsonify({'success': False,
                        'message': f'Tipo inválido. Válidos: {", ".join(TIPOS_ENTRADA)}'}), 400
    if not _cantidad_valida(cantidad):
        return jsonify({'success': False, 'message': 'Cantidad inválida'}), 400

    evt = Evento.query.get_or_404(evento_id)
    if evt.cupos < cantidad:
        return jsonify({'success': False, 'message': 'Cupos insuficientes'}), 400

    precio = _precio_entrada(evt, tipo_entrada)

    if current_user.is_authenticated:
        orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
        if not orden:
            orden = Orden(usuario_id=current_user.id, total=0, tipo_entrada=tipo_entrada)
            db.session.add(orden)
            db.session.flush()

        item = ItemOrden.query.filter_by(
            orden_id=orden.id, evento_id=evento_id, tipo_entrada=tipo_entrada
        ).first()
        if item:
            item.cantidad += cantidad
        else:
            db.session.add(ItemOrden(
                orden_id=orden.id, evento_id=evento_id,
                cantidad=cantidad, precio_unitario=precio, tipo_entrada=tipo_entrada
            ))

        orden.total = sum(i.precio_unitario * i.cantidad for i in orden.items)
        db.session.commit()
        count = sum(i.cantidad for i in orden.items)
    else:
        cart = session.get('carrito', {})
        key  = str(evento_id)
        if key in cart and isinstance(cart[key], dict):
            cart[key]['cantidad'] = cart[key].get('cantidad', 0) + cantidad
            cart[key]['tipo']     = tipo_entrada
        else:
            cart[key] = {'cantidad': cantidad, 'tipo': tipo_entrada}
        session['carrito'] = cart
        session.modified = True
        count = sum(v.get('cantidad', 1) if isinstance(v, dict) else v for v in cart.values())

    return jsonify({'success': True, 'cart_count': count})


@app.route('/api/carrito/eliminar', methods=['POST'])
def eliminar_carrito():
    """
    Elimina un ítem del carrito.

    Modo A — Evento:                   { "evento_id": 12 }
    Licor:                             { "licor_id": 3 }
    Modo B — Reserva autenticada:      { "item_id": 7 }   (ItemOrden.id)
    Modo C — Reserva en sesión anónima:{ "session_key": "reserva_G-01_2026-05-20" }
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({'success': False, 'message': 'Datos inválidos'}), 400

    evento_id   = payload.get('evento_id')
    licor_id    = payload.get('licor_id')
    item_id     = payload.get('item_id')
    session_key = payload.get('session_key')
    eliminado   = False

    if current_user.is_authenticated:
        orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
        if orden:
            if item_id is not None:
                item = ItemOrden.query.filter_by(id=int(item_id), orden_id=orden.id).first()
            elif licor_id is not None:
                item = ItemOrden.query.filter_by(orden_id=orden.id, licor_id=int(licor_id)).first()
            elif evento_id is not None:
                item = ItemOrden.query.filter_by(orden_id=orden.id, evento_id=int(evento_id)).first()
            else:
                item = None

            if item:
                db.session.delete(item)
                db.session.flush()
                orden.total = sum(i.precio_unitario * i.cantidad for i in orden.items)
                db.session.commit()
                eliminado = True
    else:
        cart = session.get('carrito', {})
        if licor_id is not None:
            key = f'licor_{licor_id}'
        else:
            key = session_key if session_key else (str(evento_id) if evento_id is not None else None)
        if key and key in cart:
            cart.pop(key)
            eliminado = True
        session['carrito'] = cart
        session.modified = True

    return jsonify({'success': True, 'eliminado': eliminado})


@app.route('/api/carrito/actualizar', methods=['POST'])
def actualizar_carrito():
    data         = request.get_json()
    evento_id    = data.get('evento_id')
    cantidad     = data.get('cantidad')
    tipo_entrada = data.get('tipo_entrada', 'general')

    if type(cantidad) is not int or cantidad > 99:
        return jsonify({'success': False, 'message': 'Cantidad inválida'}), 400

    if cantidad < 1:
        # Reutiliza la lógica de eliminar enviando el mismo payload
        return eliminar_carrito()

    evt = Evento.query.get_or_404(evento_id)
    if evt.cupos < cantidad:
        return jsonify({'success': False, 'message': 'Cupos insuficientes'}), 400

    if current_user.is_authenticated:
        orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
        if orden:
            item = ItemOrden.query.filter_by(
                orden_id=orden.id, evento_id=evento_id, tipo_entrada=tipo_entrada
            ).first()
            if item:
                item.cantidad = cantidad
                orden.total   = sum(i.precio_unitario * i.cantidad for i in orden.items)
                db.session.commit()
    else:
        cart = session.get('carrito', {})
        key  = str(evento_id)
        if key in cart and isinstance(cart[key], dict):
            cart[key]['cantidad'] = cantidad
        else:
            cart[key] = {'cantidad': cantidad, 'tipo': tipo_entrada}
        session['carrito'] = cart
        session.modified = True

    return jsonify({'success': True})


@app.route('/api/carrito/licor/agregar', methods=['POST'])
def agregar_licor_carrito():
    data     = request.get_json(silent=True) or {}
    cantidad = data.get('cantidad', 1)

    if not _cantidad_valida(cantidad):
        return jsonify({'success': False, 'message': 'Cantidad inválida'}), 400
    try:
        licor_id = int(data.get('licor_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Licor inválido'}), 400

    licor = Licor.query.filter_by(id=licor_id, disponible=True).first()
    if not licor:
        return jsonify({'success': False, 'message': 'Licor no disponible'}), 404

    if current_user.is_authenticated:
        orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
        if not orden:
            orden = Orden(usuario_id=current_user.id, total=0, tipo_entrada='licor')
            db.session.add(orden)
            db.session.flush()

        item = ItemOrden.query.filter_by(orden_id=orden.id, licor_id=licor.id).first()
        if item:
            item.cantidad += cantidad
        else:
            db.session.add(ItemOrden(
                orden_id=orden.id, licor_id=licor.id, cantidad=cantidad,
                precio_unitario=licor.precio, tipo_entrada='licor'
            ))
            db.session.flush()

        orden.total = sum(i.precio_unitario * i.cantidad for i in orden.items)
        db.session.commit()
        count = sum(i.cantidad for i in orden.items)
    else:
        cart = session.get('carrito', {})
        key  = f'licor_{licor.id}'
        if key in cart:
            cart[key]['cantidad'] += cantidad
        else:
            cart[key] = {'cantidad': cantidad, 'tipo': 'licor', 'licor_id': licor.id}
        session['carrito'] = cart
        session.modified = True
        count = sum(v.get('cantidad', 1) if isinstance(v, dict) else v for v in cart.values())

    return jsonify({'success': True, 'cart_count': count})


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
    if not orden or not orden.items:
        flash('Tu carrito está vacío.', 'info')
        return redirect(url_for('carrito'))

    if request.method == 'POST':
        orden.estado = 'pagado'
        for item in orden.items:
            # Solo descontar cupos de eventos reales (evento_id no nulo)
            if item.evento_id is not None:
                item.evento.cupos -= item.cantidad
        db.session.commit()
        flash('¡Entradas compradas con éxito! Te esperamos en El Paraíso.', 'success')
        return redirect(url_for('index'))

    total = sum(i.precio_unitario * i.cantidad for i in orden.items)
    return render_template('checkout.html', orden=orden, total=total)


@app.route('/mis_ordenes')
@login_required
def mis_ordenes():
    ordenes = Orden.query.filter_by(usuario_id=current_user.id).order_by(Orden.creado_en.desc()).all()
    return render_template('mis_ordenes.html', ordenes=ordenes)


# ==================== AUTH ====================

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'],
               key_func=lambda: request.form.get('email', '').strip().lower() or 'sin-email')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = Usuario.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=True)

            # Migrar carrito de sesión a la BD
            cart = session.get('carrito', {})
            if cart:
                orden = Orden.query.filter_by(usuario_id=user.id, estado='pendiente').first()
                if not orden:
                    orden = Orden(usuario_id=user.id, total=0)
                    db.session.add(orden)
                    db.session.flush()

                for pid, data in cart.items():
                    if isinstance(data, dict):
                        cantidad = data.get('cantidad', 1)
                        tipo     = data.get('tipo', 'general')
                    else:
                        cantidad, tipo = data, 'general'

                    # Licores del carrito anónimo
                    licor_id = data.get('licor_id') if isinstance(data, dict) else None
                    if licor_id:
                        item = ItemOrden.query.filter_by(orden_id=orden.id, licor_id=licor_id).first()
                        licor = Licor.query.get(licor_id)
                        if item:
                            item.cantidad += cantidad
                        elif licor:
                            db.session.add(ItemOrden(
                                orden_id=orden.id, licor_id=licor.id, cantidad=cantidad,
                                precio_unitario=licor.precio, tipo_entrada='licor'
                            ))
                            db.session.flush()
                        continue

                    # Ignorar reservas en la migración (no tienen evento_id válido)
                    if tipo in ('reserva',) or not pid.isdigit():
                        continue

                    evt = Evento.query.get(int(pid))
                    if evt:
                        precio = _precio_entrada(evt, tipo)
                        item   = ItemOrden.query.filter_by(
                            orden_id=orden.id, evento_id=evt.id, tipo_entrada=tipo
                        ).first()
                        if item:
                            item.cantidad += cantidad
                        else:
                            db.session.add(ItemOrden(
                                orden_id=orden.id, evento_id=evt.id,
                                cantidad=cantidad, precio_unitario=precio, tipo_entrada=tipo
                            ))

                orden.total = sum(i.precio_unitario * i.cantidad for i in orden.items)
                db.session.commit()
                session.pop('carrito', None)

            flash(f'Bienvenido a El Paraíso, {user.nombre}!', 'success')
            destino = request.args.get('next')
            return redirect(destino if _destino_seguro(destino) else url_for('index'))

        flash('Credenciales incorrectas.', 'danger')

    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        error = _validar_usuario(nombre, email)
        if not error and len(password) < 8:
            error = 'La contraseña debe tener mínimo 8 caracteres.'
        if error:
            flash(error, 'danger')
            return redirect(url_for('registro'))

        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('registro'))

        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'danger')
            return redirect(url_for('registro'))

        user = Usuario(nombre=nombre, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Cuenta creada. Inicia sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('carrito', None)
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('index'))


# ==================== PÁGINAS ESTÁTICAS ====================

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/politica')
def politica():
    return render_template('politica.html')

@app.route('/terminos')
def terminos():
    return render_template('terminos.html')


# ==================== LICORES ====================

@app.route('/licores')
def licores():
    licores_list = Licor.query.filter_by(disponible=True).all()
    return render_template('licores.html', licores=licores_list)

@app.route('/api/licores')
def api_licores():
    return jsonify([{
        'id': l.id, 'nombre': l.nombre, 'descripcion': l.descripcion,
        'precio': l.precio, 'categoria': l.categoria, 'imagen': l.imagen
    } for l in Licor.query.filter_by(disponible=True).all()])

@app.route('/admin/licores')
@login_required
@admin_required
def admin_licores():
    licores_list = Licor.query.order_by(Licor.categoria, Licor.nombre).all()
    return render_template('admin/licores.html', licores=licores_list)

@app.route('/admin/licores/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_licor():
    if request.method == 'POST':
        imagen = 'https://images.unsplash.com/photo-1514362545857-3bc16c4c7d1b?auto=format&fit=crop&w=400'
        if 'imagen' in request.files:
            file = request.files['imagen']
            if file.filename and allowed_file(file.filename):
                filename    = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'licores')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                imagen = f'/static/img/eventos/licores/{filename}'
            elif file.filename:
                flash('Tipo de archivo no permitido. Solo: jpg, jpeg, png, gif, webp', 'danger')

        db.session.add(Licor(
            nombre      = request.form.get('nombre'),
            descripcion = request.form.get('descripcion'),
            precio      = float(request.form.get('precio', 0)),
            categoria   = request.form.get('categoria', 'whiskey'),
            imagen      = imagen,
            disponible  = bool(request.form.get('disponible')),
        ))
        db.session.commit()
        flash('Licor agregado.', 'success')
        return redirect(url_for('admin_licores'))

    return render_template('admin/crear_licor.html')

@app.route('/admin/licores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_licor(id):
    licor = Licor.query.get_or_404(id)
    if request.method == 'POST':
        licor.nombre      = request.form.get('nombre')
        licor.descripcion = request.form.get('descripcion')
        licor.precio      = float(request.form.get('precio', 0))
        licor.categoria   = request.form.get('categoria', 'whiskey')
        licor.disponible  = bool(request.form.get('disponible'))

        if 'imagen' in request.files:
            file = request.files['imagen']
            if file.filename and allowed_file(file.filename):
                filename    = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'licores')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                licor.imagen = f'/static/img/eventos/licores/{filename}'
            elif file.filename:
                flash('Tipo de archivo no permitido. Solo: jpg, jpeg, png, gif, webp', 'danger')

        db.session.commit()
        flash('Licor actualizado.', 'success')
        return redirect(url_for('admin_licores'))

    return render_template('admin/editar_licor.html', licor=licor)

@app.route('/admin/licores/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_licor(id):
    licor = Licor.query.get_or_404(id)
    if licor.items:
        flash('Este licor ya tiene ventas. Márcalo como no disponible en vez de eliminarlo.', 'warning')
        return redirect(url_for('admin_licores'))
    db.session.delete(licor)
    db.session.commit()
    flash('Licor eliminado.', 'success')
    return redirect(url_for('admin_licores'))


# ==================== GALERÍA ====================

@app.route('/galeria')
def galeria():
    imagenes = ImagenGaleria.query.filter_by(activa=True).order_by(ImagenGaleria.orden).all()
    return render_template('galeria.html', imagenes=imagenes)

@app.route('/admin/galeria')
@login_required
@admin_required
def admin_galeria():
    imagenes = ImagenGaleria.query.order_by(ImagenGaleria.orden).all()
    return render_template('admin/galeria.html', imagenes=imagenes)

@app.route('/admin/galeria/subir', methods=['POST'])
@login_required
@admin_required
def subir_imagen_galeria():
    titulo      = request.form.get('titulo')
    categoria   = request.form.get('categoria', 'general')
    fecha_str   = request.form.get('fecha_evento')
    fecha       = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
    orden       = int(request.form.get('orden', 0))
    imagen_url  = ''

    if 'imagen' in request.files:
        file = request.files['imagen']
        if file.filename and allowed_file(file.filename):
            filename    = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], 'galeria')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            imagen_url = f'/static/img/eventos/galeria/{filename}'
        elif file.filename:
            flash('Tipo de archivo no permitido. Solo: jpg, jpeg, png, gif, webp', 'danger')

    imagen_url = imagen_url or request.form.get('imagen_url', '')

    if imagen_url:
        db.session.add(ImagenGaleria(
            titulo=titulo, categoria=categoria, imagen_url=imagen_url,
            fecha_evento=fecha, orden=orden
        ))
        db.session.commit()
        flash('Imagen agregada a la galería.', 'success')
    else:
        flash('Debes subir una imagen o proporcionar una URL.', 'danger')

    return redirect(url_for('admin_galeria'))

@app.route('/admin/galeria/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_imagen_galeria(id):
    img = ImagenGaleria.query.get_or_404(id)
    if request.method == 'POST':
        fecha_str     = request.form.get('fecha_evento')
        img.titulo    = request.form.get('titulo')
        img.categoria = request.form.get('categoria', 'general')
        img.fecha_evento = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
        img.orden     = int(request.form.get('orden', 0))
        img.activa    = bool(request.form.get('activa'))
        db.session.commit()
        flash('Imagen actualizada.', 'success')
        return redirect(url_for('admin_galeria'))

    return render_template('admin/editar_imagen.html', img=img)

@app.route('/admin/galeria/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_imagen_galeria(id):
    img = ImagenGaleria.query.get_or_404(id)
    db.session.delete(img)
    db.session.commit()
    flash('Imagen eliminada.', 'success')
    return redirect(url_for('admin_galeria'))


# ==================== PROMOCIONES ====================

@app.route('/admin/promociones')
@login_required
@admin_required
def admin_promociones():
    promos = Promocion.query.order_by(Promocion.creado_en.desc()).all()
    return render_template('admin/promociones.html', promociones=promos)

@app.route('/admin/promociones/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_promocion():
    if request.method == 'POST':
        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str    = request.form.get('fecha_fin')
        codigo           = request.form.get('codigo', '').upper().strip()
        if Promocion.query.filter_by(codigo=codigo).first():
            flash('Ya existe una promoción con ese código.', 'danger')
            return redirect(url_for('crear_promocion'))
        db.session.add(Promocion(
            codigo               = codigo,
            nombre               = request.form.get('nombre'),
            descripcion          = request.form.get('descripcion'),
            descuento_porcentaje = int(request.form.get('descuento_porcentaje', 0)),
            descuento_valor      = float(request.form.get('descuento_valor', 0)),
            tipo_entrada         = request.form.get('tipo_entrada') or None,
            usos_maximos         = int(request.form.get('usos_maximos', 100)),
            fecha_inicio         = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else date.today(),
            fecha_fin            = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else None,
        ))
        db.session.commit()
        flash('Promoción creada.', 'success')
        return redirect(url_for('admin_promociones'))

    return render_template('admin/crear_promocion.html')

@app.route('/admin/promociones/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_promocion(id):
    promo = Promocion.query.get_or_404(id)
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').upper().strip()
        otra   = Promocion.query.filter_by(codigo=codigo).first()
        if otra and otra.id != promo.id:
            flash('Ya existe una promoción con ese código.', 'danger')
            return redirect(url_for('editar_promocion', id=promo.id))

        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str    = request.form.get('fecha_fin')
        promo.codigo               = codigo
        promo.nombre               = request.form.get('nombre')
        promo.descripcion          = request.form.get('descripcion')
        promo.descuento_porcentaje = int(request.form.get('descuento_porcentaje', 0))
        promo.descuento_valor      = float(request.form.get('descuento_valor', 0))
        promo.tipo_entrada         = request.form.get('tipo_entrada') or None
        promo.usos_maximos         = int(request.form.get('usos_maximos', 100))
        promo.fecha_inicio         = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else promo.fecha_inicio
        promo.fecha_fin            = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else None
        promo.activa               = bool(request.form.get('activa'))
        db.session.commit()
        flash('Promoción actualizada.', 'success')
        return redirect(url_for('admin_promociones'))

    return render_template('admin/editar_promocion.html', promo=promo)

@app.route('/admin/promociones/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_promocion(id):
    promo = Promocion.query.get_or_404(id)
    db.session.delete(promo)
    db.session.commit()
    flash('Promoción eliminada.', 'success')
    return redirect(url_for('admin_promociones'))

@app.route('/api/promocion/validar', methods=['POST'])
def validar_promocion():
    data         = request.get_json()
    codigo       = data.get('codigo', '').upper().strip()
    tipo_entrada = data.get('tipo_entrada', 'general')

    promo = Promocion.query.filter_by(codigo=codigo, activa=True).first()
    if not promo:
        return jsonify({'valido': False, 'message': 'Código no válido'}), 400
    if promo.fecha_fin and promo.fecha_fin < date.today():
        return jsonify({'valido': False, 'message': 'Promoción expirada'}), 400
    if promo.usos_actuales >= promo.usos_maximos:
        return jsonify({'valido': False, 'message': 'Cupo de usos agotado'}), 400
    if promo.tipo_entrada and promo.tipo_entrada != tipo_entrada:
        return jsonify({'valido': False, 'message': f'Código solo válido para entrada {promo.tipo_entrada.upper()}'}), 400

    return jsonify({
        'valido': True,
        'nombre': promo.nombre,
        'descuento_porcentaje': promo.descuento_porcentaje,
        'descuento_valor': promo.descuento_valor,
    })


# ==================== RECUPERACIÓN DE CONTRASEÑA ====================

def _generar_token_reset(email):
    return URLSafeTimedSerializer(app.config['SECRET_KEY']).dumps(email, salt='password-reset')

def _verificar_token_reset(token, max_age=1800):
    try:
        return URLSafeTimedSerializer(app.config['SECRET_KEY']).loads(
            token, salt='password-reset', max_age=max_age
        )
    except (SignatureExpired, BadSignature):
        return None


@app.route('/recuperar-password', methods=['GET', 'POST'])
def recuperar_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    enviado = False
    email_enviado = ''

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = Usuario.query.filter_by(email=email).first()
        enviado      = True
        email_enviado = email

        if user:
            token     = _generar_token_reset(email)
            reset_url = url_for('reset_password', token=token, _external=True)
            try:
                if mail is None:
                    raise RuntimeError('flask_mail no instalado')
                mail.send(MailMessage(
                    subject    = 'Restablecer contraseña — El Paraíso',
                    recipients = [email],
                    html       = f'''
                    <div style="font-family:Inter,sans-serif;background:#0a0a0a;color:#e5e5e5;
                                padding:40px;border-radius:12px;max-width:480px;margin:auto">
                        <h2 style="color:#00f0ff;letter-spacing:0.1em;text-transform:uppercase">El Paraíso</h2>
                        <p>Hola <strong>{user.nombre}</strong>,</p>
                        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
                        <p>Haz clic en el siguiente botón (válido 30 minutos):</p>
                        <a href="{reset_url}"
                           style="display:inline-block;padding:14px 32px;background:#00f0ff;
                                  color:#0a0a0a;border-radius:8px;font-weight:700;
                                  text-decoration:none;letter-spacing:0.1em;
                                  text-transform:uppercase;margin:16px 0">
                            Restablecer contraseña
                        </a>
                        <p style="color:#666;font-size:0.8rem">
                            Si no solicitaste esto, ignora este mensaje.<br>
                            El enlace expirará en 30 minutos.
                        </p>
                    </div>'''
                ))
            except Exception:
                if app.debug:
                    app.logger.warning(f'[DEV] Reset URL para {email}: {reset_url}')

    return render_template('recuperar_password.html', enviado=enviado, email_enviado=email_enviado)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    email       = _verificar_token_reset(token)
    token_valido = email is not None

    if request.method == 'POST' and token_valido:
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if len(password) < 8:
            flash('La contraseña debe tener mínimo 8 caracteres.', 'danger')
            return render_template('reset_password.html', token_valido=True, token=token)
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('reset_password.html', token_valido=True, token=token)

        user = Usuario.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('¡Contraseña actualizada! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))

        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('recuperar_password'))

    return render_template('reset_password.html', token_valido=token_valido, token=token)


# ==================== RESERVAS DE MESA ====================

@app.route('/reservas')
def reservas():
    return render_template('reservas.html')


@app.route('/api/reservas/guardar', methods=['POST'])
def guardar_reserva():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({'success': False, 'message': 'Cuerpo de la petición inválido'}), 400

    requeridos = {
        'mesa_id': 'ID de mesa', 'mesa_zona': 'Zona', 'fecha': 'Fecha',
        'personas': 'Número de personas', 'nombre': 'Nombre',
        'telefono': 'Teléfono', 'email': 'Email',
    }
    for campo, etiqueta in requeridos.items():
        if not payload.get(campo):
            return jsonify({'success': False, 'message': f'El campo "{etiqueta}" es obligatorio'}), 400

    try:
        fecha = datetime.strptime(payload['fecha'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Formato de fecha inválido (esperado YYYY-MM-DD)'}), 400

    if fecha < date.today():
        return jsonify({'success': False, 'message': 'La fecha no puede ser en el pasado'}), 400

    # El precio y la zona salen del servidor, no de lo que envía el navegador
    mesa = next((m for m in MESAS if m['id'] == payload['mesa_id']), None)
    if not mesa:
        return jsonify({'success': False, 'message': 'La mesa no existe'}), 400

    precio   = mesa['precio']
    personas = max(1, int(payload.get('personas', 1)))

    try:
        reserva = ReservaMesa(
            mesa_id    = payload['mesa_id'],
            mesa_zona  = mesa['zona'],
            mesa_precio= precio,
            fecha      = fecha,
            personas   = personas,
            nombre     = payload['nombre'].strip(),
            telefono   = payload['telefono'].strip(),
            email      = payload['email'].strip().lower(),
            notas      = payload.get('notas', '').strip(),
            usuario_id = current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(reserva)
        db.session.flush()

        cart_count = 0

        if current_user.is_authenticated:
            orden = Orden.query.filter_by(usuario_id=current_user.id, estado='pendiente').first()
            if not orden:
                orden = Orden(usuario_id=current_user.id, total=0, tipo_entrada='reserva')
                db.session.add(orden)
                db.session.flush()

            # evento_id = None porque las reservas no tienen evento (columna nullable)
            db.session.add(ItemOrden(
                orden_id       = orden.id,
                evento_id      = None,
                cantidad       = 1,
                precio_unitario= precio,
                tipo_entrada   = 'reserva',
            ))
            db.session.flush()
            orden.total = sum(i.precio_unitario * i.cantidad for i in orden.items)
            cart_count  = sum(i.cantidad for i in orden.items)
        else:
            cart = session.get('carrito', {})
            key  = f'reserva_{payload["mesa_id"]}_{payload["fecha"]}'
            cart[key] = {
                'cantidad': 1,
                'tipo':     'reserva',
                'reserva':  {
                    'id':        reserva.id,
                    'mesa_id':   payload['mesa_id'],
                    'mesa_zona': mesa['zona'],
                    'precio':    precio,
                    'fecha':     payload['fecha'],
                    'nombre':    payload['nombre'].strip(),
                    'personas':  personas,
                },
            }
            session['carrito'] = cart
            session.modified = True
            cart_count = sum(
                v.get('cantidad', 1) if isinstance(v, dict) else v for v in cart.values()
            )

        db.session.commit()
        return jsonify({'success': True, 'reserva_id': reserva.id, 'cart_count': cart_count})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error al guardar reserva: {e}')
        return jsonify({'success': False, 'message': 'Error interno al guardar la reserva'}), 500


@app.route('/api/reservas/mesas')
def api_mesas_disponibles():
    """Devuelve mesas con su estado real según reservas en la BD para la fecha dada."""
    fecha_str = request.args.get('fecha')
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
    except ValueError:
        fecha = date.today()

    # Mesas reservadas (confirmadas o pendientes) para esa fecha
    reservadas_ids = {
        r.mesa_id for r in
        ReservaMesa.query.filter(
            ReservaMesa.fecha == fecha,
            ReservaMesa.estado.in_(['pendiente', 'confirmada'])
        ).all()
    }

    mesas = [
        {**m, 'estado': 'ocupada' if m['id'] in reservadas_ids else 'disponible'}
        for m in MESAS
    ]

    return jsonify({'mesas': mesas, 'fecha': fecha.isoformat()})


# ==================== ADMIN ====================

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html',
        total_eventos  = Evento.query.count(),
        total_usuarios = Usuario.query.count(),
        total_ordenes  = Orden.query.count(),
        ordenes_recientes = Orden.query.order_by(Orden.creado_en.desc()).limit(5).all(),
        eventos_proximos  = (Evento.query
                             .filter(Evento.fecha_evento >= date.today())
                             .order_by(Evento.fecha_evento).limit(5).all()),
    )

@app.route('/admin/eventos')
@login_required
@admin_required
def admin_eventos():
    eventos = Evento.query.order_by(Evento.fecha_evento.desc()).all()
    return render_template('admin/eventos.html', eventos=eventos)


def _save_event_image(request_files):
    """Guarda la imagen de un evento y devuelve el nombre del archivo, o None."""
    if 'imagen' not in request_files:
        return None
    file = request_files['imagen']
    if not file.filename:
        return None
    if not allowed_file(file.filename):
        flash('Tipo de archivo no permitido. Solo: jpg, jpeg, png, gif, webp', 'danger')
        return None
    filename = secure_filename(file.filename)
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))
    return filename


def _parse_event_form(form):
    """Extrae y valida los campos comunes del formulario de evento."""
    fecha_str = form.get('fecha_evento', '').strip()
    if not fecha_str:
        return None, 'La fecha del evento es obligatoria.'
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return None, 'Formato de fecha inválido. Usa YYYY-MM-DD.'
    return fecha, None


@app.route('/admin/eventos/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_evento():
    if request.method == 'POST':
        fecha, error = _parse_event_form(request.form)
        if error:
            flash(error, 'danger')
            return redirect(url_for('crear_evento'))

        imagen = _save_event_image(request.files) or 'default.jpg'

        db.session.add(Evento(
            nombre           = request.form.get('nombre'),
            descripcion      = request.form.get('descripcion'),
            precio_general   = float(request.form.get('precio_general', 30000)),
            precio_vip       = float(request.form.get('precio_vip', 60000)),
            precio_palco     = float(request.form.get('precio_palco', 120000)),
            precio_backstage = float(request.form.get('precio_backstage', 200000)),
            precio_king      = float(request.form.get('precio_king', 350000)),
            cupos            = int(request.form.get('cupos', 500)),
            genero_id        = int(request.form.get('genero_id')),
            imagen           = imagen,
            destacado        = bool(request.form.get('destacado')),
            fecha_evento     = fecha,
            hora_evento      = request.form.get('hora_evento', '22:00'),
            artista          = request.form.get('artista', ''),
            ubicacion        = request.form.get('ubicacion', UBICACION),
        ))
        db.session.commit()
        flash('Evento creado.', 'success')
        return redirect(url_for('admin_eventos'))

    return render_template('admin/crear_evento.html', generos=GeneroMusical.query.all())


@app.route('/admin/eventos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_evento(id):
    evt = Evento.query.get_or_404(id)
    if request.method == 'POST':
        fecha, error = _parse_event_form(request.form)
        if error:
            flash(error, 'danger')
            return redirect(url_for('editar_evento', id=evt.id))

        nueva_imagen = _save_event_image(request.files)
        if nueva_imagen:
            evt.imagen = nueva_imagen

        evt.nombre           = request.form.get('nombre')
        evt.descripcion      = request.form.get('descripcion')
        evt.precio_general   = float(request.form.get('precio_general', 30000))
        evt.precio_vip       = float(request.form.get('precio_vip', 60000))
        evt.precio_palco     = float(request.form.get('precio_palco', 120000))
        evt.precio_backstage = float(request.form.get('precio_backstage', 200000))
        evt.precio_king      = float(request.form.get('precio_king', 350000))
        evt.cupos            = int(request.form.get('cupos', 500))
        evt.genero_id        = int(request.form.get('genero_id'))
        evt.destacado        = bool(request.form.get('destacado'))
        evt.fecha_evento     = fecha
        evt.hora_evento      = request.form.get('hora_evento', '22:00')
        evt.artista          = request.form.get('artista', '')
        evt.ubicacion        = request.form.get('ubicacion', UBICACION)
        db.session.commit()
        flash('Evento actualizado.', 'success')
        return redirect(url_for('admin_eventos'))

    return render_template('admin/editar_evento.html', evento=evt, generos=GeneroMusical.query.all())


@app.route('/admin/eventos/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_evento(id):
    evt = Evento.query.get_or_404(id)
    db.session.delete(evt)
    db.session.commit()
    flash('Evento eliminado.', 'success')
    return redirect(url_for('admin_eventos'))


# ==================== ADMIN: USUARIOS ====================

def _guardar_usuario(usuario):
    """Copia el formulario al usuario. Devuelve un mensaje de error o None."""
    nombre   = request.form.get('nombre', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    es_admin = bool(request.form.get('es_admin'))

    error = _validar_usuario(nombre, email)
    if error:
        return error
    otro = Usuario.query.filter_by(email=email).first()
    if otro and otro.id != usuario.id:
        return 'El email ya está registrado.'
    if (password or usuario.id is None) and len(password) < 8:
        return 'La contraseña debe tener mínimo 8 caracteres.'
    if usuario.id == current_user.id and not es_admin:
        return 'No puedes quitarte a ti mismo el rol de administrador.'

    usuario.nombre   = nombre
    usuario.email    = email
    usuario.es_admin = es_admin
    if password:
        usuario.set_password(password)
    return None


@app.route('/admin/usuarios')
@login_required
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.order_by(Usuario.creado_en.desc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@app.route('/admin/usuarios/crear', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    if request.method == 'POST':
        usuario = Usuario()
        error   = _guardar_usuario(usuario)
        if error:
            flash(error, 'danger')
            return redirect(url_for('crear_usuario'))
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario creado.', 'success')
        return redirect(url_for('admin_usuarios'))

    return render_template('admin/form_usuario.html', usuario=None)


@app.route('/admin/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        error = _guardar_usuario(usuario)
        if error:
            flash(error, 'danger')
            return redirect(url_for('editar_usuario', id=usuario.id))
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin_usuarios'))

    return render_template('admin/form_usuario.html', usuario=usuario)


@app.route('/admin/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
    elif usuario.ordenes or ReservaMesa.query.filter_by(usuario_id=usuario.id).first():
        flash('Este usuario tiene órdenes o reservas, no se puede eliminar.', 'warning')
    else:
        db.session.delete(usuario)
        db.session.commit()
        flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin_usuarios'))


# ==================== ADMIN: RESERVAS ====================

@app.route('/admin/reservas')
@login_required
@admin_required
def admin_reservas():
    reservas_list = ReservaMesa.query.order_by(ReservaMesa.fecha.desc()).all()
    return render_template('admin/reservas.html', reservas=reservas_list)


@app.route('/admin/reservas/estado/<int:id>', methods=['POST'])
@login_required
@admin_required
def cambiar_estado_reserva(id):
    reserva = ReservaMesa.query.get_or_404(id)
    estado  = request.form.get('estado')
    if estado in ESTADOS_RESERVA:
        reserva.estado = estado
        db.session.commit()
        flash('Reserva actualizada.', 'success')
    else:
        flash('Estado inválido.', 'danger')
    return redirect(url_for('admin_reservas'))


@app.route('/admin/reservas/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_reserva(id):
    reserva = ReservaMesa.query.get_or_404(id)
    db.session.delete(reserva)
    db.session.commit()
    flash('Reserva eliminada.', 'success')
    return redirect(url_for('admin_reservas'))


# ==================== INICIALIZACIÓN ====================

def init_db():
    with app.app_context():
        db.create_all()

        # Agrega licor_id si la tabla se creó antes de esta versión
        columnas = [c['name'] for c in db.inspect(db.engine).get_columns('items_orden')]
        if 'licor_id' not in columnas:
            db.session.execute(db.text('ALTER TABLE items_orden ADD COLUMN licor_id INTEGER REFERENCES licores(id)'))
            db.session.commit()

        if not GeneroMusical.query.first():
            db.session.add_all([
                GeneroMusical(nombre='Crossover',        slug='crossover',  descripcion='Salsa, Vallenato, Merengue y más en una sola noche'),
                GeneroMusical(nombre='Reggaetón & Urbano',slug='reggaeton',  descripcion='Lo más candente del género urbano'),
                GeneroMusical(nombre='Electrónica',      slug='electronica', descripcion='House, Techno y Latin House'),
                GeneroMusical(nombre='Dembow',           slug='dembow',      descripcion='El ritmo que está rompiendo en toda Colombia'),
                GeneroMusical(nombre='Champeta',         slug='champeta',    descripcion='El sonido autóctono de la Costa Caribe'),
            ])
            db.session.commit()

        if not Usuario.query.filter_by(email='admin@elparaiso.com').first():
            admin = Usuario(nombre='Administrador', email='admin@elparaiso.com', es_admin=True)
            admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()

        if not Evento.query.first():
            from datetime import timedelta
            hoy = date.today()
            # Basados en lo que publica la discoteca en Facebook.
            # Fechas y precios son de ejemplo: se ajustan en /admin/eventos.
            noche = 'https://images.unsplash.com/photo-1740572569816-9c437c4b9c4d?q=80&w=1170&auto=format&fit=crop'
            club  = 'https://images.unsplash.com/photo-1647314620432-7e27193891cb?q=80&w=1169&auto=format&fit=crop'
            db.session.add_all([
                Evento(nombre='Éxitos de la Champeta',
                       descripcion='Disfruta una noche de éxitos de la champeta en Paraíso Club.',
                       precio_general=20000, precio_vip=45000, precio_palco=90000, precio_backstage=160000, precio_king=280000,
                       cupos=300, genero_id=5, imagen=noche,
                       destacado=True, fecha_evento=hoy+timedelta(days=5), hora_evento='21:00', artista='Paraíso Club', ubicacion=UBICACION),
                Evento(nombre='Noche de Locura',
                       descripcion='Llega que sí es para eso: rumba toda la noche en Paraíso Club.',
                       precio_general=30000, precio_vip=60000, precio_palco=120000, precio_backstage=200000, precio_king=350000,
                       cupos=300, genero_id=1, imagen=club,
                       destacado=True, fecha_evento=hoy+timedelta(days=8), hora_evento='22:00', artista='Paraíso Club', ubicacion=UBICACION),
                Evento(nombre='El Clásico Español en Pantalla Gigante',
                       descripcion='Vive el clásico español en pantalla gigante en Paraíso Club.',
                       precio_general=20000, precio_vip=45000, precio_palco=90000, precio_backstage=160000, precio_king=280000,
                       cupos=300, genero_id=1, imagen=club,
                       destacado=True, fecha_evento=hoy+timedelta(days=12), hora_evento='14:00', artista='Pantalla gigante', ubicacion=UBICACION),
                Evento(nombre='Selección Colombia en Pantalla Gigante',
                       descripcion='Vamos todos, apoyemos a la Selección Colombia. Te esperamos en Paraíso Club Montería.',
                       precio_general=20000, precio_vip=45000, precio_palco=90000, precio_backstage=160000, precio_king=280000,
                       cupos=300, genero_id=1, imagen=noche,
                       destacado=True, fecha_evento=hoy+timedelta(days=19), hora_evento='18:00', artista='Pantalla gigante', ubicacion=UBICACION),
            ])
            db.session.commit()

        if not Licor.query.first():
            # Precios y fotos de licoresmedellin.com, consultados el 2026-11-09.
            db.session.add_all([
                Licor(nombre='Aguardiente Antioqueño Tapa Verde 750 ml', categoria='aguardiente', precio=53900,
                      descripcion='Aguardiente colombiano de la Fábrica de Licores de Antioquia, el más vendido del país.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/AGUARDIENTE_ANTIOQUENO_TAPA_VERDE_BOTELLA_750ML.jpg?v=1793051613'),
                Licor(nombre='Aguardiente Antioqueño Tapa Azul 750 ml', categoria='aguardiente', precio=55900,
                      descripcion='Versión sin azúcar del aguardiente de la Fábrica de Licores de Antioquia.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/aguardiente-antioqueno-tapa-azul-botella-750mlaguardiente-antioqueno-tapa-azul-botella-750mlaguardiente-antioquenolicores-medellin-2388907.jpg?v=1759123399'),
                Licor(nombre='Aguardiente Amarillo de Manzanares 750 ml', categoria='aguardiente', precio=57900,
                      descripcion='Aguardiente de la Industria Licorera de Caldas.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/aguardiente-amarillo-de-manzanares-botella-750mlaguardiente-amarillo-de-manzanares-botella-750mlindustria-licorera-de-caldaslicores-medellin-7021712.jpg?v=1765494233'),
                Licor(nombre='Ron Medellín 3 Años Añejo 750 ml', categoria='ron', precio=56900,
                      descripcion='Ron añejo colombiano de la Fábrica de Licores de Antioquia.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/ron-medellin-3-anos-anejo-botella-750mlron-medellin-3-anos-anejo-botella-750mlron-medellinlicores-medellin-8660657.jpg?v=1759123251'),
                Licor(nombre='Ron Viejo de Caldas 3 Años Tradicional 750 ml', categoria='ron', precio=58900,
                      descripcion='Ron colombiano de la Industria Licorera de Caldas.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/ron-viejo-de-caldas-3-anos-tradicional-botella-750mlron-viejo-de-caldas-3-anos-tradicional-botella-750mlron-viejo-de-caldaslicores-medellin-1250736.jpg?v=1759123369'),
                Licor(nombre='Ron Viejo de Caldas 8 Años Carta de Oro 750 ml', categoria='ron', precio=102900,
                      descripcion='Ron colombiano añejado 8 años, de la Industria Licorera de Caldas.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/ron-viejo-de-caldas-8-anos-carta-de-oro-botella-750mlron-viejo-de-caldas-8-anos-carta-de-oro-botella-750mlron-viejo-de-caldaslicores-medellin-8336735.jpg?v=1759123370'),
                Licor(nombre='Whisky Old Parr 12 Años 750 ml', categoria='whiskey', precio=159000,
                      descripcion='Whisky escocés de mezcla, añejado 12 años.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-old-parr-12-anos-botella-750mlwhisky-old-parr-12-anos-botella-750mlold-parrlicores-medellin-1357166.jpg?v=1759122553'),
                Licor(nombre="Whisky Buchanan's Deluxe 12 Años 750 ml", categoria='whiskey', precio=185900,
                      descripcion='Whisky escocés de mezcla, añejado 12 años.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-buchanans-deluxe-12-anos-botella-750mlwhisky-buchanans-deluxe-12-anos-botella-750mlbuchananslicores-medellin-2276071.jpg?v=1765490172'),
                Licor(nombre="Whisky Buchanan's Master 750 ml", categoria='whiskey', precio=217900,
                      descripcion="Whisky escocés de mezcla de la casa Buchanan's.",
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-buchanans-master-botella-750mlwhisky-buchanans-master-botella-750mlbuchananslicores-medellin-3145715.jpg?v=1759122553'),
                Licor(nombre='Whisky Johnnie Walker Red Label 700 ml', categoria='whiskey', precio=79900,
                      descripcion='Whisky escocés de mezcla.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/whisky-johnnie-walker-red-label-botella-700mlwhisky-johnnie-walker-red-label-botella-700mljohnnie-walkerlicores-medellin-9011566.jpg?v=1759122553'),
                Licor(nombre='Whisky Johnnie Walker Black Label 700 ml', categoria='whiskey', precio=172900,
                      descripcion='Whisky escocés de mezcla, añejado 12 años.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/WHISKY_JOHNNIE_WALKER_BLACK_LABEL_BOTELLA_700ML.jpg?v=1764364351'),
                Licor(nombre='Vodka Absolut 700 ml', categoria='vodka', precio=93000,
                      descripcion='Vodka sueco.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/vodka-absolut-botella-700mlvodka-absolut-botella-700mlabsolut-vodkalicores-medellin-2766595.jpg?v=1759122630'),
                Licor(nombre='Vodka Smirnoff N° 21 700 ml', categoria='vodka', precio=111000,
                      descripcion='Vodka clásico de la marca Smirnoff.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/vodka-smirnoff-botella-700mlvodka-smirnoff-botella-700mlsmirnofflicores-medellin-2446150.jpg?v=1759122630'),
                Licor(nombre='Tequila José Cuervo Especial Reposado 750 ml', categoria='tequila', precio=98900,
                      descripcion='Tequila mexicano reposado.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/tequila-jose-cuervo-especial-reposado-botella-750mltequila-jose-cuervo-especial-reposado-botella-750mljose-cuervolicores-medellin-5501636.jpg?v=1776272385'),
                Licor(nombre='Tequila José Cuervo Especial Silver 750 ml', categoria='tequila', precio=98900,
                      descripcion='Tequila mexicano plateado.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/tequila-jose-cuervo-especial-silver-botella-750mltequila-jose-cuervo-especial-silver-botella-750mljose-cuervolicores-medellin-2367928.jpg?v=1759123228'),
                Licor(nombre='Tequila Don Julio Blanco 700 ml', categoria='tequila', precio=271900,
                      descripcion='Tequila mexicano blanco.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/tequila-don-julio-blanco-botella-700mltequila-don-julio-blanco-botella-700mltequila-don-juliolicores-medellin-3471506.jpg?v=1764878992'),
                Licor(nombre='Champagne Moët & Chandon Brut 750 ml', categoria='champagne', precio=563900,
                      descripcion='Champagne francés brut.',
                      imagen='https://cdn.shopify.com/s/files/1/0602/6376/0011/files/champagne-moet-chandon-brut-botella-750mlchampagne-moet-chandon-brut-botella-750mlmoet-hennessylicores-medellin-2709495.jpg?v=1759122554'),
            ])
            db.session.commit()


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes'), port=5000)

// ==================== LENIS SMOOTH SCROLL ====================
const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
});

// Un solo loop — el ticker de GSAP sincroniza Lenis y ScrollTrigger
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);
lenis.on('scroll', ScrollTrigger.update);

// ==================== CUSTOM CURSOR NEON ====================
const cursor = document.querySelector('.cursor');
const follower = document.querySelector('.cursor-follower');

if (cursor && follower) {
    let mouseX = 0, mouseY = 0;
    let cursorX = 0, cursorY = 0;
    let followerX = 0, followerY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animateCursor() {
        cursorX += (mouseX - cursorX) * 0.2;
        cursorY += (mouseY - cursorY) * 0.2;
        followerX += (mouseX - followerX) * 0.1;
        followerY += (mouseY - followerY) * 0.1;
        cursor.style.left = cursorX - 6 + 'px';
        cursor.style.top  = cursorY - 6 + 'px';
        follower.style.left = followerX - 20 + 'px';
        follower.style.top  = followerY - 20 + 'px';
        requestAnimationFrame(animateCursor);
    }
    animateCursor();

    const hoverElements = document.querySelectorAll(
        'a, button, .category-card, .event-card, .cart-item-qty button, .quantity-selector button, .price-option, .gallery-item, .licor-card, .filter-btn'
    );
    hoverElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            follower.style.width       = '60px';
            follower.style.height      = '60px';
            follower.style.borderColor = 'var(--accent)';
            follower.style.background  = 'rgba(0, 240, 255, 0.05)';
            follower.style.boxShadow   = '0 0 20px rgba(0, 240, 255, 0.3)';
        });
        el.addEventListener('mouseleave', () => {
            follower.style.width       = '40px';
            follower.style.height      = '40px';
            follower.style.borderColor = 'var(--accent)';
            follower.style.background  = 'transparent';
            follower.style.boxShadow   = '0 0 10px rgba(0, 240, 255, 0.2)';
        });
    });
}

// ==================== PRELOADER ====================
const currentPath = window.location.pathname;
const isHomePage  = currentPath === '/' || currentPath === '/home' || currentPath === '';
const preloader   = document.getElementById('preloader');

if (preloader && isHomePage) {
    const preloaderLogo    = preloader.querySelectorAll('.preloader-logo span');
    const preloaderCounter = preloader.querySelector('.preloader-counter');

    const maxPreloaderTime = setTimeout(() => hidePreloader(), 2500);

    function hidePreloader() {
        clearTimeout(maxPreloaderTime);
        gsap.to(preloader, {
            yPercent: -100, duration: 0.8, ease: 'power4.inOut',
            onComplete: () => { preloader.style.display = 'none'; initPageAnimations(); }
        });
    }

    if (preloaderLogo.length > 0 && preloaderCounter) {
        const tl = gsap.timeline({ onComplete: hidePreloader });
        tl.from(preloaderLogo, { y: 50, opacity: 0, duration: 0.6, stagger: 0.04, ease: 'power3.out' })
          .to(preloaderCounter, {
              innerText: 100, duration: 1.2, snap: { innerText: 1 }, ease: 'power2.inOut',
              onUpdate: function() {
                  if (preloaderCounter) preloaderCounter.innerText = Math.round(this.targets()[0].innerText) + '%';
              }
          }, 0);
    } else {
        hidePreloader();
    }
} else {
    if (preloader) preloader.style.display = 'none';
    initPageAnimations();
}

// ==================== PAGE ANIMATIONS ====================
function initPageAnimations() {
    gsap.to('.nav-logo-letter', {
        opacity: 1, y: 0, rotateX: 0, duration: 0.6, stagger: 0.08,
        ease: 'back.out(1.7)', delay: 0.3,
        onComplete: () => {
            document.querySelector('.nav-v3-logo')?.classList.add('animated');
            document.querySelectorAll('.nav-logo-letter').forEach(l => l.classList.add('revealed'));
        }
    });
    gsap.fromTo('.nav-v3-logo',
        { filter: 'brightness(2)' },
        { filter: 'brightness(1)', duration: 1.5, ease: 'power2.out', delay: 0.3 }
    );
    gsap.to('.hero-title .line-inner', { y: 0, duration: 1.2, stagger: 0.1, ease: 'power4.out', delay: 0.2 });
    gsap.to('.hero-image', { scale: 1, duration: 1.8, ease: 'power2.out' });
    gsap.from('.hero-label, .hero-desc, .hero-cta', { y: 30, opacity: 0, duration: 1, stagger: 0.15, ease: 'power3.out', delay: 0.5 });
    gsap.to('.hero-marquee', { opacity: 1, duration: 1, delay: 0.8 });
    gsap.utils.toArray('.particle').forEach((p, i) => {
        gsap.to(p, { y: -30 + Math.random()*60, x: -20 + Math.random()*40, duration: 3 + Math.random()*3, repeat: -1, yoyo: true, ease: 'sine.inOut', delay: i * 0.2 });
    });
}

// ==================== NAVIGATION ====================
const navV3 = document.getElementById('navbar');
if (navV3) {
    ScrollTrigger.create({
        start: 'top -50',
        onUpdate: (self) => {
            if (self.scroll() > 50) navV3.classList.add('scrolled');
            else navV3.classList.remove('scrolled');
        }
    });
}

const mobileToggle = document.getElementById('mobile-toggle');
const mobileMenu   = document.getElementById('mobile-menu');
mobileToggle?.addEventListener('click', () => {
    mobileMenu?.classList.toggle('active');
    const spans = mobileToggle.querySelectorAll('span');
    if (mobileMenu?.classList.contains('active')) {
        gsap.to(spans[0], { rotate: 45,  y:  5.5, duration: 0.3 });
        gsap.to(spans[1], { opacity: 0,          duration: 0.3 });
        gsap.to(spans[2], { rotate: -45, y: -5.5, duration: 0.3 });
    } else {
        gsap.to(spans[0], { rotate: 0, y: 0, duration: 0.3 });
        gsap.to(spans[1], { opacity: 1,      duration: 0.3 });
        gsap.to(spans[2], { rotate: 0, y: 0, duration: 0.3 });
    }
});

const waBtn = document.querySelector('.whatsapp-float');
if (waBtn) {
    waBtn.addEventListener('mouseenter', () => gsap.to(waBtn, { scale: 1.15, duration: 0.3, ease: 'back.out(2)' }));
    waBtn.addEventListener('mouseleave', () => gsap.to(waBtn, { scale: 1,    duration: 0.3 }));
}

// ==================== SCROLL REVEALS ====================
gsap.utils.toArray('.section-header').forEach(h => {
    gsap.from(h.children, { scrollTrigger: { trigger: h, start: 'top 85%' }, y: 30, opacity: 0, duration: 0.8, stagger: 0.1, ease: 'power3.out' });
});
gsap.utils.toArray('.category-card').forEach((c, i) => {
    gsap.from(c, { scrollTrigger: { trigger: c, start: 'top 90%' }, y: 40, opacity: 0, duration: 0.8, delay: i * 0.08, ease: 'power3.out' });
});
gsap.utils.toArray('.event-card').forEach((c, i) => {
    gsap.from(c, { scrollTrigger: { trigger: c, start: 'top 90%' }, y: 30, opacity: 0, duration: 0.6, delay: i * 0.05, ease: 'power3.out' });
});
gsap.utils.toArray('.process-item').forEach((item, i) => {
    gsap.from(item, { scrollTrigger: { trigger: item, start: 'top 90%' }, y: 30, opacity: 0, duration: 0.6, delay: i * 0.08, ease: 'power3.out' });
});
gsap.from('.testimonial-quote', { scrollTrigger: { trigger: '.testimonial', start: 'top 85%' }, y: 30, opacity: 0, duration: 0.8, ease: 'power3.out' });
gsap.from('.cta-title, .cta-btn', { scrollTrigger: { trigger: '.cta', start: 'top 85%' }, y: 30, opacity: 0, duration: 0.8, stagger: 0.15, ease: 'power3.out' });
gsap.from('.footer-grid > div', { scrollTrigger: { trigger: '.footer', start: 'top 90%' }, y: 20, opacity: 0, duration: 0.6, stagger: 0.08, ease: 'power3.out' });
gsap.utils.toArray('.gallery-item').forEach((item, i) => {
    gsap.from(item, { scrollTrigger: { trigger: item, start: 'top 90%' }, y: 20, opacity: 0, duration: 0.5, delay: i * 0.03, ease: 'power3.out' });
});
gsap.utils.toArray('.licor-card').forEach((c, i) => {
    gsap.from(c, { scrollTrigger: { trigger: c, start: 'top 90%' }, y: 20, opacity: 0, duration: 0.5, delay: i * 0.05, ease: 'power3.out' });
});

// ==================== FLATPICKR GLOBAL ====================
function initFlatpickr() {
    if (typeof flatpickr === 'undefined') return;
    document.querySelectorAll('.flatpickr-input:not(.flatpickr-initialized)').forEach(input => {
        input.classList.add('flatpickr-initialized');
        try {
            flatpickr(input, {
                locale: 'es', dateFormat: 'Y-m-d', minDate: 'today',
                theme: 'dark', disableMobile: true, allowInput: false,
                appendTo: document.body, animate: true,
                onOpen: (_, __, instance) => {
                    if (instance.calendarContainer) {
                        Object.assign(instance.calendarContainer.style, {
                            background: '#0a0a0a',
                            border: '1px solid rgba(0, 240, 255, 0.2)',
                            borderRadius: '12px',
                            boxShadow: '0 20px 60px rgba(0,0,0,0.6), 0 0 30px rgba(0, 240, 255, 0.1)'
                        });
                    }
                }
            });
        } catch (e) { console.error('flatpickr error:', e); }
    });
}

function initFlatpickrReserva() {
    if (typeof flatpickr === 'undefined') return;
    const input = document.getElementById('res-fecha');
    if (!input || input._flatpickr) return;   // evita duplicados
    try {
        flatpickr(input, {
            locale: 'es', dateFormat: 'Y-m-d', minDate: 'today',
            theme: 'dark', disableMobile: true, allowInput: false,
            appendTo: document.body, animate: true,
            onOpen: (_, __, instance) => {
                if (instance.calendarContainer) {
                    Object.assign(instance.calendarContainer.style, {
                        background: '#0a0a0a',
                        border: '1px solid rgba(0, 240, 255, 0.2)',
                        borderRadius: '12px',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.6), 0 0 30px rgba(0, 240, 255, 0.1)'
                    });
                }
            }
        });
    } catch (e) { console.error('flatpickr reserva error:', e); }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFlatpickr);
} else {
    initFlatpickr();
}

// ==================== GALLERY LIGHTBOX ====================
const galleryItems  = document.querySelectorAll('.gallery-item');
const lightbox      = document.getElementById('lightbox');
const lightboxImg   = document.getElementById('lightbox-img');
const lightboxClose = document.getElementById('lightbox-close');

if (lightbox && lightboxImg) {
    galleryItems.forEach(item => {
        item.addEventListener('click', () => {
            const img = item.querySelector('img');
            if (img) {
                lightboxImg.src = img.src;
                lightbox.classList.add('active');
                gsap.fromTo(lightboxImg, { scale: 0.8, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: 'power2.out' });
            }
        });
    });
    lightboxClose?.addEventListener('click', () => {
        gsap.to(lightboxImg, { scale: 0.8, opacity: 0, duration: 0.3, onComplete: () => lightbox.classList.remove('active') });
    });
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            gsap.to(lightboxImg, { scale: 0.8, opacity: 0, duration: 0.3, onComplete: () => lightbox.classList.remove('active') });
        }
    });
}

document.querySelectorAll('.gallery-filter').forEach(filter => {
    filter.addEventListener('click', () => {
        const category = filter.dataset.filter;
        document.querySelectorAll('.gallery-filter').forEach(f => f.classList.remove('active'));
        filter.classList.add('active');
        document.querySelectorAll('.gallery-item').forEach(item => {
            if (category === 'all' || item.dataset.category === category) {
                gsap.to(item, { opacity: 1, scale: 1, duration: 0.3, display: 'block' });
            } else {
                gsap.to(item, { opacity: 0, scale: 0.9, duration: 0.3, display: 'none' });
            }
        });
    });
});

// ==================== CART FUNCTIONALITY ====================
document.addEventListener('click', function(e) {

    // Agregar evento al carrito
    const addBtn = e.target.closest('.event-add');
    if (addBtn && addBtn.dataset.eventId) {
        e.preventDefault();
        e.stopPropagation();
        addToCart(parseInt(addBtn.dataset.eventId), 1, addBtn.dataset.tipo || 'general');
        return;
    }

    // Agregar desde detalle de evento
    const detailBtn = e.target.closest('#btn-add-detail');
    if (detailBtn && detailBtn.dataset.eventId) {
        e.preventDefault();
        const qty           = parseInt(document.getElementById('qty')?.value || 1);
        const selectedPrice = document.querySelector('.price-option.selected');
        addToCart(parseInt(detailBtn.dataset.eventId), qty, selectedPrice?.dataset.tipo || 'general');
        return;
    }

    // Cambiar cantidad (solo eventos, no reservas)
    const qtyBtn = e.target.closest('.qty-btn');
    if (qtyBtn && qtyBtn.dataset.eventId) {
        e.preventDefault();
        const cartItem = qtyBtn.closest('.cart-item');
        if (cartItem?.dataset.esReserva === 'true') return;  // reservas: ignorar
        const action = qtyBtn.dataset.action;
        if (action === 'increase') updateCartItem(qtyBtn.dataset.eventId, 1);
        else if (action === 'decrease') updateCartItem(qtyBtn.dataset.eventId, -1);
        return;
    }

    // ─── ELIMINAR ÍTEM ─────────────────────────────────────────────────────────
    const removeBtn = e.target.closest('.cart-item-remove');
    if (removeBtn) {
        e.preventDefault();
        removeFromCart({
            eventId:    removeBtn.dataset.eventId    || null,
            itemId:     removeBtn.dataset.itemId     || null,
            sessionKey: removeBtn.dataset.sessionKey || null,
            esReserva:  removeBtn.dataset.esReserva  === 'true',
        });
        return;
    }

    // Seleccionar tipo de precio
    const priceOption = e.target.closest('.price-option');
    if (priceOption) {
        document.querySelectorAll('.price-option').forEach(p => p.classList.remove('selected'));
        priceOption.classList.add('selected');
        return;
    }
});

// Selector de cantidad en detalle de evento
document.addEventListener('click', function(e) {
    const qtyBtn = e.target.closest('.quantity-selector button');
    if (!qtyBtn) return;
    const input = qtyBtn.parentElement.querySelector('input');
    if (!input) return;
    let val = parseInt(input.value) || 1;
    const max = parseInt(input.max) || 99;
    val = (qtyBtn.textContent.includes('−') || qtyBtn.textContent.includes('-'))
        ? Math.max(1, val - 1)
        : Math.min(max, val + 1);
    input.value = val;
});

// ─── addToCart ────────────────────────────────────────────────────────────────
async function addToCart(eventId, quantity = 1, tipoEntrada = 'general') {
    try {
        const res  = await fetch('/api/carrito/agregar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ evento_id: eventId, cantidad: quantity, tipo_entrada: tipoEntrada })
        });
        const data = await res.json();
        if (data.success) {
            updateCartBadge(data.cart_count);
            showNotification('Entrada agregada al carrito', 'success');
        } else {
            showNotification(data.message || 'Error al agregar', 'danger');
        }
    } catch { showNotification('Error de conexión', 'danger'); }
}

// ─── removeFromCart ───────────────────────────────────────────────────────────
async function removeFromCart({ eventId = null, itemId = null, sessionKey = null, esReserva = false } = {}) {
    const body = {};
    if (itemId)          body.item_id     = itemId;
    else if (sessionKey) body.session_key = sessionKey;
    else if (eventId)    body.evento_id   = eventId;
    else return;

    // El data-id del .cart-item coincide con el identificador principal
    const domId = itemId || sessionKey || eventId;

    try {
        const res  = await fetch('/api/carrito/eliminar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await res.json();

        if (data.success) {
            const item = document.querySelector(`.cart-item[data-id="${domId}"]`);
            if (item) {
                gsap.to(item, {
                    x: -50, opacity: 0, duration: 0.4,
                    onComplete: () => {
                        item.remove();
                        if (!document.querySelector('.cart-item')) location.reload();
                    }
                });
            }
            showNotification(esReserva ? 'Reserva eliminada' : 'Entrada eliminada', 'info');
        } else {
            showNotification(data.message || 'Error al eliminar', 'danger');
        }
    } catch { showNotification('Error de conexión', 'danger'); }
}

// ─── updateCartItem ───────────────────────────────────────────────────────────
async function updateCartItem(eventId, delta) {
    const item = document.querySelector(`.cart-item[data-id="${eventId}"]`);
    if (!item || item.dataset.esReserva === 'true') return;

    const qtyEl  = item.querySelector('.qty-value');
    const newQty = parseInt(qtyEl.textContent) + delta;
    if (newQty < 1) { removeFromCart({ eventId }); return; }

    try {
        const res  = await fetch('/api/carrito/actualizar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ evento_id: eventId, cantidad: newQty })
        });
        const data = await res.json();
        if (data.success) location.reload();
        else showNotification(data.message || 'Error', 'danger');
    } catch { showNotification('Error de conexión', 'danger'); }
}

// ─── Utilidades ───────────────────────────────────────────────────────────────
function updateCartBadge(count) {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        gsap.fromTo(badge, { scale: 1.5 }, { scale: 1, duration: 0.4, ease: 'back.out(2)' });
        badge.textContent = count;
    }
}

function showNotification(message, type = 'info') {
    const container = document.querySelector('.flash-messages') || createFlashContainer();
    const flash = document.createElement('div');
    flash.className   = `flash flash-${type}`;
    flash.textContent = message;
    container.appendChild(flash);
    gsap.from(flash, { x: 100, opacity: 0, duration: 0.4 });
    setTimeout(() => {
        gsap.to(flash, { x: 100, opacity: 0, duration: 0.4, onComplete: () => flash.remove() });
    }, 3000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// ==================== OTROS ====================
document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
        if (card.dataset.slug) window.location.href = `/eventos/${card.dataset.slug}`;
    });
});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) lenis.scrollTo(target, { offset: -80 });
    });
});

setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => {
        gsap.to(f, { x: 100, opacity: 0, duration: 0.4, delay: 0.2, onComplete: () => f.remove() });
    });
}, 4000);
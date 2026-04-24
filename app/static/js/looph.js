/* ══════════════════════════════════════════
   LOOPH.CO — Main JavaScript
   Shared across all pages
   ══════════════════════════════════════════ */

/* ── DATA STORE ── */
const LOOPH = {

  products: [
    { id:1,  name:'Linen Relaxed Tee',       cat:'shirts',      price:890,  badge:'new',  rating:4.8, reviews:42, stock:18, sizes:['XS','S','M','L','XL'],
      desc:'Our bestselling relaxed tee in a breathable linen-cotton blend. Slightly oversized with a dropped shoulder — perfect for layering or wearing alone.',
      imgs:['/static/images/cover-pic.jpg','/static/images/home-2.jpg'] },
    { id:2,  name:'Washed Overshirt',         cat:'shirts',      price:1490, badge:null,   rating:4.6, reviews:28, stock:9,  sizes:['S','M','L','XL'],
      desc:'Enzyme-washed overshirt with a lived-in feel straight out the box. Button-through front, chest pockets, relaxed body.',
      imgs:['/static/images/home-2.jpg','/static/images/cover-pic.jpg'] },
    { id:3,  name:'Cargo Trousers',           cat:'pants',       price:1890, badge:'ltd',  rating:4.9, reviews:65, stock:4,  sizes:['28','30','32','34','36'],
      desc:'Six-pocket cargo in sturdy twill. Tapered leg, elasticated waist with drawcord. The kind of pants you\'ll reach for every week.',
      imgs:['/static/images/home-1.jpg','/static/images/model-3.jpg'] },
    { id:4,  name:'Field Jacket',             cat:'jackets',     price:2890, badge:'new',  rating:4.7, reviews:19, stock:11, sizes:['S','M','L','XL','XXL'],
      desc:'Utility-inspired field jacket in a durable ripstop shell. Four exterior pockets, snap buttons, and a clean silhouette that works anywhere.',
      imgs:['/static/images/cover2.jpg','/static/images/model-4.jpg'] },
    { id:5,  name:'Utility Shorts',           cat:'pants',       price:990,  badge:null,   rating:4.5, reviews:33, stock:22, sizes:['28','30','32','34'],
      desc:'Lightweight utility shorts with an easy fit and a 9-inch inseam. Two side pockets plus a hidden zip back pocket.',
      imgs:['/static/images/model-1.jpg','/static/images/home-1.jpg'] },
    { id:6,  name:'Canvas Shoulder Tote',     cat:'accessories', price:490,  badge:'sale', rating:4.4, reviews:87, stock:35, sizes:['ONE SIZE'],
      desc:'Heavy-gauge canvas tote with a reinforced base and interior zip pocket. Wide straps for comfortable carry all day.',
      imgs:['/static/images/model-2.jpg','/static/images/model-3.jpg'] },
    { id:7,  name:'Coach Jacket',             cat:'outerwear',   price:2490, badge:'ltd',  rating:4.8, reviews:24, stock:6,  sizes:['S','M','L','XL'],
      desc:'Snap-front coach jacket in a silky nylon shell. Clean lining, welt pockets, and a slim cut that sits just below the hip.',
      imgs:['/static/images/model-3.jpg','/static/images/cover2.jpg'] },
    { id:8,  name:'Knit Waffle Beanie',       cat:'accessories', price:390,  badge:null,   rating:4.3, reviews:55, stock:41, sizes:['ONE SIZE'],
      desc:'Ribbed waffle-knit beanie in a cotton-acrylic blend. Slightly slouchy fit that works for everyone.',
      imgs:['/static/images/model-4.jpg','/static/images/home-2.jpg'] },
    { id:9,  name:'Boxy Pocket Tee',          cat:'shirts',      price:750,  badge:'new',  rating:4.7, reviews:38, stock:27, sizes:['XS','S','M','L','XL','XXL'],
      desc:'100% cotton boxy tee with a chest pocket detail. Pre-washed for immediate softness. A wardrobe staple.',
      imgs:['/static/images/cover-pic.jpg','/static/images/model-1.jpg'] },
    { id:10, name:'Wide-Leg Linen Pants',     cat:'pants',       price:1690, badge:null,   rating:4.6, reviews:21, stock:13, sizes:['XS','S','M','L','XL'],
      desc:'Relaxed wide-leg silhouette in breathable linen blend. High-rise waist, side slit cuffs, and minimal hardware.',
      imgs:['/static/images/model-2.jpg','/static/images/home-1.jpg'] },
    { id:11, name:'Quilted Liner Jacket',     cat:'outerwear',   price:3290, badge:'new',  rating:4.9, reviews:11, stock:8,  sizes:['S','M','L','XL'],
      desc:'Channel-quilted liner jacket in a matte nylon exterior. Lightweight warmth that layers under a coat or wears alone.',
      imgs:['/static/images/cover2.jpg','/static/images/model-4.jpg'] },
    { id:12, name:'Cord Crossbody',           cat:'accessories', price:650,  badge:'ltd',  rating:4.5, reviews:44, stock:15, sizes:['ONE SIZE'],
      desc:'Mini crossbody in needlecord fabric with a top handle and detachable strap. Just big enough for the essentials.',
      imgs:['/static/images/model-3.jpg','/static/images/model-2.jpg'] },
    { id:13, name:'Ripstop Cargo Jacket',     cat:'jackets',     price:3490, badge:'new',  rating:4.8, reviews:7,  stock:5,  sizes:['S','M','L','XL'],
      desc:'Technical ripstop fabric, multiple cargo pockets, removable hood. Built for unpredictable Manila weather and beyond.',
      imgs:['/static/images/cover2.jpg','/static/images/cover-pic.jpg'] },
    { id:14, name:'Twill Chino',              cat:'pants',       price:1290, badge:null,   rating:4.5, reviews:33, stock:20, sizes:['28','30','32','34','36'],
      desc:'Clean-cut chino in a durable cotton twill. Slim through the thigh with a tapered leg — office-to-weekend effortless.',
      imgs:['/static/images/home-1.jpg','/static/images/model-2.jpg'] },
    { id:15, name:'Mesh Layer Tee',           cat:'shirts',      price:820,  badge:'new',  rating:4.4, reviews:19, stock:30, sizes:['XS','S','M','L','XL'],
      desc:'Dual-layer mesh construction with an inner liner for opacity. Ventilated, lightweight, and surprisingly versatile.',
      imgs:['/static/images/home-2.jpg','/static/images/model-1.jpg'] },
    { id:16, name:'Baseball Cap',             cat:'accessories', price:450,  badge:null,   rating:4.6, reviews:62, stock:50, sizes:['ONE SIZE'],
      desc:'Six-panel structured cap with a curved brim and embroidered Looph wordmark. Adjustable strap at the back.',
      imgs:['/static/images/model-4.jpg','/static/images/cover-pic.jpg'] },
  ],

  // Runtime state
  cart: JSON.parse(localStorage.getItem('looph_cart') || '[]'),
  wishlist: new Set(JSON.parse(localStorage.getItem('looph_wishlist') || '[]')),
  user: JSON.parse(localStorage.getItem('looph_user') || 'null'),
  selectedSize: {},
  currentFilter: 'all',
  currentSort: 'default',
  priceRange: { min: 0, max: 9999 },
  currentProductId: null,

  // Vouchers (admin)
  vouchers: [
    { code:'LOOPH10', type:'percent', value:10, uses:0, active:true },
    { code:'WELCOME', type:'flat',    value:150, uses:0, active:true },
    { code:'SUMMER20',type:'percent', value:20, uses:5, active:false },
  ],

  // Orders mock
  orders: [
    { id:'LPH-001', user:'jdelacruz@email.com', items:2, total:2380, status:'delivered', date:'2024-12-01' },
    { id:'LPH-002', user:'msantos@email.com',   items:1, total:890,  status:'processing',date:'2024-12-05' },
    { id:'LPH-003', user:'areyes@email.com',    items:3, total:5270, status:'shipped',   date:'2024-12-06' },
    { id:'LPH-004', user:'bcruz@email.com',     items:1, total:1490, status:'pending',   date:'2024-12-07' },
    { id:'LPH-005', user:'lcabrera@email.com',  items:4, total:7180, status:'delivered', date:'2024-12-08' },
  ],
};

/* ── UTILS ── */
const fmt = n => '₱' + Number(n).toLocaleString();

function stars(r, lg=false) {
  const sz = lg ? 14 : 11;
  let s = `<span class="stars">`;
  for (let i = 1; i <= 5; i++)
    s += `<svg class="star${i <= Math.round(r) ? '' : ' empty'}" viewBox="0 0 24 24" width="${sz}" height="${sz}"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
  s += `</span>`;
  return s;
}

function saveCart() {
  localStorage.setItem('looph_cart', JSON.stringify(LOOPH.cart));
}
function saveWishlist() {
  localStorage.setItem('looph_wishlist', JSON.stringify([...LOOPH.wishlist]));
}
function saveUser(u) {
  LOOPH.user = u;
  localStorage.setItem('looph_user', JSON.stringify(u));
}

/* ── TOAST ── */
function showToast(msg, type = '') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = `<span class="toast-dot ${type}"></span>${msg}`;
  container.appendChild(t);
  requestAnimationFrame(() => { requestAnimationFrame(() => { t.classList.add('show'); }); });
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 420); }, 3200);
}

/* ── CART ── */
function addToCart(product, size) {
  const sz = size || product.sizes[0];
  const key = `${product.id}-${sz}`;
  const existing = LOOPH.cart.find(i => i.key === key);
  if (existing) { existing.qty++; }
  else { LOOPH.cart.push({ ...product, key, size: sz, qty: 1 }); }
  saveCart();
  updateCartBadge();
  updateCartPanel();
  showToast(`${product.name} added to cart`, 'ok');
}

function removeFromCart(key) {
  LOOPH.cart = LOOPH.cart.filter(i => i.key !== key);
  saveCart();
  updateCartBadge();
  updateCartPanel();
}

function changeQty(key, delta) {
  const item = LOOPH.cart.find(i => i.key === key);
  if (!item) return;
  item.qty += delta;
  if (item.qty <= 0) removeFromCart(key);
  else { saveCart(); updateCartPanel(); }
  updateCartBadge();
}

function updateCartBadge() {
  const total = LOOPH.cart.reduce((s, i) => s + i.qty, 0);
  document.querySelectorAll('.cart-count').forEach(el => el.textContent = total);
}

function updateCartPanel() {
  const body = document.getElementById('cartBody');
  const foot = document.getElementById('cartFooter');
  if (!body) return;
  const subtotal = LOOPH.cart.reduce((s, i) => s + i.price * i.qty, 0);

  if (LOOPH.cart.length === 0) {
    body.innerHTML = `<div class="cart-empty-state">
      <svg viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
      <p>Your cart is empty</p>
    </div>`;
    if (foot) foot.style.display = 'none';
    return;
  }

  body.innerHTML = LOOPH.cart.map(i => `
    <div class="cart-item">
      <div class="ci-thumb"><img src="${i.imgs[0]}" alt="${i.name}" onerror="this.style.opacity=0"></div>
      <div>
        <p class="ci-name">${i.name}</p>
        <p class="ci-meta">Size: ${i.size}</p>
        <div class="ci-qty-row">
          <button class="ci-q-btn" onclick="changeQty('${i.key}',-1)">−</button>
          <span class="ci-q-num">${i.qty}</span>
          <button class="ci-q-btn" onclick="changeQty('${i.key}',1)">+</button>
        </div>
        <button class="ci-rm" onclick="removeFromCart('${i.key}')">Remove</button>
      </div>
      <span class="ci-price">${fmt(i.price * i.qty)}</span>
    </div>`).join('');

  if (foot) {
    foot.style.display = 'block';
    document.getElementById('cartSubtotal').textContent = fmt(subtotal);
    document.getElementById('cartTotal').textContent = fmt(subtotal);
  }
}

function toggleCart() {
  const sidebar = document.getElementById('cartSidebar');
  const overlay = document.getElementById('cartOverlay');
  if (!sidebar) return;
  const open = sidebar.classList.toggle('open');
  overlay && overlay.classList.toggle('open', open);
  document.body.style.overflow = open ? 'hidden' : '';
}

/* ── WISHLIST ── */
function toggleWishlist(id, btn) {
  if (LOOPH.wishlist.has(id)) {
    LOOPH.wishlist.delete(id);
    btn && btn.classList.remove('active');
    showToast('Removed from wishlist');
  } else {
    LOOPH.wishlist.add(id);
    btn && btn.classList.add('active');
    showToast('Saved to wishlist ♥');
  }
  saveWishlist();
}

/* ── PRODUCT CARD RENDERER ── */
function renderProductCard(p, delay = 0) {
  const badgeMap = { new: 'badge-new', ltd: 'badge-ltd', sale: 'badge-sale' };
  const badgeLbl = { new: 'New', ltd: 'Limited', sale: 'Sale' };
  return `<div class="product-card reveal" style="transition-delay:${delay}s" data-id="${p.id}">
    <div class="pc-img">
      <img src="${p.imgs[0]}" alt="${p.name}" loading="lazy" onerror="this.style.opacity=0">
      ${p.badge ? `<span class="pc-badge ${badgeMap[p.badge]}">${badgeLbl[p.badge]}</span>` : ''}
      <button class="pc-wish ${LOOPH.wishlist.has(p.id) ? 'active' : ''}" onclick="event.stopPropagation();toggleWishlist(${p.id},this)" aria-label="Wishlist">
        <svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
      </button>
      <div class="pc-hover">
        <span>${p.name}</span>
        <button class="qv-btn" onclick="event.stopPropagation();openQuickView(${p.id})">Quick View</button>
      </div>
    </div>
    <div class="pc-info">
      <p class="pc-cat">${p.cat}</p>
      <h3 class="pc-name">${p.name}</h3>
      <div class="pc-bottom">
        <span class="pc-price">${fmt(p.price)}</span>
        <div class="pc-rating">
          ${stars(p.rating)}
          <span class="pc-rating-count">(${p.reviews})</span>
        </div>
      </div>
    </div>
  </div>`;
}

/* ── QUICK VIEW MODAL ── */
function openQuickView(id) {
  const p = LOOPH.products.find(x => x.id === id);
  if (!p) return;
  LOOPH.currentProductId = id;
  LOOPH.selectedSize[id] = LOOPH.selectedSize[id] || p.sizes[0];

  document.getElementById('qvCat').textContent = p.cat;
  document.getElementById('qvName').textContent = p.name;
  document.getElementById('qvDesc').textContent = p.desc;
  document.getElementById('qvRating').innerHTML = `${stars(p.rating, true)} <span style="font-size:0.8rem;color:var(--text2)">${p.rating} (${p.reviews} reviews)</span>`;
  const orig = p.badge === 'sale' ? Math.round(p.price * 1.25) : null;
  document.getElementById('qvPriceRow').innerHTML = `<span class="qv-price">${fmt(p.price)}</span>${orig ? `<span class="qv-price-orig">${fmt(orig)}</span>` : ''}`;
  document.getElementById('qvMainImg').src = p.imgs[0];
  document.getElementById('qvMainImg').alt = p.name;
  document.getElementById('qvThumbs').innerHTML = p.imgs.map((img, i) =>
    `<div class="qv-thumb ${i === 0 ? 'active' : ''}" onclick="qvSwitchImg(this,'${img}')"><img src="${img}" alt="" onerror="this.style.opacity=0"></div>`
  ).join('');
  document.getElementById('qvSizes').innerHTML = p.sizes.map(s =>
    `<button class="size-btn ${s === LOOPH.selectedSize[id] ? 'active' : ''}" onclick="qvSelectSize(this,'${s}',${id})">${s}</button>`
  ).join('');

  const overlay = document.getElementById('modalOverlay');
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeQuickView() {
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
  LOOPH.currentProductId = null;
}

function qvSwitchImg(thumb, src) {
  document.getElementById('qvMainImg').src = src;
  document.querySelectorAll('.qv-thumb').forEach(t => t.classList.remove('active'));
  thumb.classList.add('active');
}

function qvSelectSize(btn, size, id) {
  document.querySelectorAll('#qvSizes .size-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  LOOPH.selectedSize[id] = size;
}

function qvAddToCart() {
  const p = LOOPH.products.find(x => x.id === LOOPH.currentProductId);
  if (!p) return;
  const sz = LOOPH.selectedSize[p.id] || p.sizes[0];
  addToCart(p, sz);
  closeQuickView();
}

/* ── SEARCH ── */
function toggleSearch() {
  const overlay = document.getElementById('searchOverlay');
  if (!overlay) return;
  const open = overlay.classList.toggle('open');
  if (open) {
    renderSearchResults(LOOPH.products.slice(0, 6));
    document.getElementById('searchLabel').textContent = 'Trending now';
    document.getElementById('searchInput').value = '';
    setTimeout(() => document.getElementById('searchInput').focus(), 80);
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
}

function liveSearch(q) {
  const label = document.getElementById('searchLabel');
  if (!q.trim()) {
    renderSearchResults(LOOPH.products.slice(0, 6));
    label.textContent = 'Trending now';
    return;
  }
  const ql = q.toLowerCase();
  const res = LOOPH.products.filter(p =>
    p.name.toLowerCase().includes(ql) ||
    p.cat.toLowerCase().includes(ql) ||
    p.desc.toLowerCase().includes(ql)
  );
  renderSearchResults(res);
  label.textContent = `${res.length} result${res.length !== 1 ? 's' : ''} for "${q}"`;
}

function renderSearchResults(items) {
  const grid = document.getElementById('searchGrid');
  if (!grid) return;
  if (!items.length) { grid.innerHTML = '<p style="color:var(--text3);font-size:0.82rem">No results found.</p>'; return; }
  grid.innerHTML = items.slice(0, 6).map(p => `
    <div class="search-result-card" onclick="toggleSearch();openQuickView(${p.id})">
      <div class="search-result-img"><img src="${p.imgs[0]}" alt="${p.name}" onerror="this.style.opacity=0"></div>
      <div class="search-result-info">
        <p>${p.name}</p>
        <p>${fmt(p.price)}</p>
      </div>
    </div>`).join('');
}

function doSearch(tag) {
  document.getElementById('searchInput').value = tag;
  liveSearch(tag);
}

/* ── THEME ── */
function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const next = isDark ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('looph_theme', next);
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = isDark ? '☾ Dark' : '☀ Light';
}

function initTheme() {
  const saved = localStorage.getItem('looph_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = saved === 'dark' ? '☀ Light' : '☾ Dark';
}

/* ── NAV SCROLL ── */
function initNavScroll() {
  const nav = document.getElementById('nav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 30);
  }, { passive: true });
}

/* ── MOBILE MENU ── */
function toggleMenu() {
  const drawer = document.getElementById('mobileDrawer');
  const ham = document.getElementById('hamburger');
  if (!drawer) return;
  const open = drawer.classList.toggle('open');
  ham && ham.classList.toggle('open', open);
  document.body.style.overflow = open ? 'hidden' : '';
}

/* ── REVEAL OBSERVER ── */
function observeReveals() {
  const els = document.querySelectorAll('.reveal:not(.in),.reveal-left:not(.in),.reveal-right:not(.in)');
  if (!els.length) return;
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target); }
    });
  }, { threshold: 0.1 });
  els.forEach(el => obs.observe(el));
}

/* ── CUSTOM CURSOR ── */
function initCursor() {
  const cur = document.getElementById('cursor');
  const ring = document.getElementById('cursorRing');
  if (!cur || !ring) return;
  let mx = 0, my = 0, rx = 0, ry = 0;
  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    cur.style.left = mx + 'px'; cur.style.top = my + 'px';
  }, { passive: true });
  const animRing = () => {
    rx += (mx - rx) * 0.12; ry += (my - ry) * 0.12;
    ring.style.left = rx + 'px'; ring.style.top = ry + 'px';
    requestAnimationFrame(animRing);
  };
  animRing();
  document.querySelectorAll('button,a,.product-card,.search-result-card').forEach(el => {
    el.addEventListener('mouseenter', () => { cur.classList.add('grow'); ring.classList.add('grow'); });
    el.addEventListener('mouseleave', () => { cur.classList.remove('grow'); ring.classList.remove('grow'); });
  });
}

/* ── KEYBOARD SHORTCUTS ── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeQuickView();
    const so = document.getElementById('searchOverlay');
    if (so && so.classList.contains('open')) toggleSearch();
  }
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    toggleSearch();
  }
});

/* ── MODAL CLOSE ON OVERLAY CLICK ── */
document.addEventListener('click', e => {
  const overlay = document.getElementById('modalOverlay');
  if (overlay && e.target === overlay) closeQuickView();
});

/* ── AUTH HELPERS ── */
function isLoggedIn() { return !!LOOPH.user; }
function isAdmin() { return LOOPH.user && LOOPH.user.role === 'admin'; }

function updateNavForUser() {
  const userNav = document.getElementById('navUserArea');
  if (!userNav) return;
  if (isLoggedIn()) {
    userNav.innerHTML = `
      <a class="nav-links-a" href="#" onclick="showPage('profile')" style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--text2);padding:0.5rem 1rem;transition:color 0.3s">Hi, ${LOOPH.user.name.split(' ')[0]}</a>
      ${isAdmin() ? `<a class="nav-links-a" href="#" onclick="showPage('admin')" style="font-size:0.7rem;letter-spacing:0.14em;text-transform:uppercase;color:var(--accent);padding:0.5rem 0.5rem">Admin</a>` : ''}`;
  } else {
    userNav.innerHTML = `
      <li><a onclick="showPage('login')" data-page="login">Login</a></li>
      <li><a onclick="showPage('register')" data-page="register">Register</a></li>`;
  }
}

/* ── INIT ── */
function initShared() {
  initTheme();
  initNavScroll();
  updateCartBadge();
  updateCartPanel();
  setTimeout(() => { observeReveals(); initCursor(); }, 150);

  // Scroll-triggered reveal re-check
  window.addEventListener('scroll', () => observeReveals(), { passive: true });
}

// Auto-run on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initShared);
} else {
  initShared();
}

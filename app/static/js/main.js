/* ═══════════════════════════════════════════════
   LOOPH.CO — MAIN JS
   ═══════════════════════════════════════════════ */

/* ── PRODUCT DATA ── */
const PRODUCTS = Array.isArray(window.SHOP_PRODUCTS) ? window.SHOP_PRODUCTS : [];

/* ── STATE ── */
const STORE_SCOPE = window.CURRENT_USER_ID ? `user_${window.CURRENT_USER_ID}` : 'guest';
const CART_KEY = `looph_cart_${STORE_SCOPE}`;
const WISH_KEY = `looph_wish_${STORE_SCOPE}`;
let cart = JSON.parse(localStorage.getItem(CART_KEY) || '[]');
let wishlist = new Set(JSON.parse(localStorage.getItem(WISH_KEY) || '[]'));
let selectedSizes = {};
let currentProduct = null;
let currentFilter = 'all';
let currentSort = 'default';
let priceRange = { min: 0, max: 9999 };
let adminProductImages = [];

/* ── HELPERS ── */
const fmt = n => '₱' + Number(n).toLocaleString();
const $ = id => document.getElementById(id);
const saveCart = () => localStorage.setItem(CART_KEY, JSON.stringify(cart));
const saveWish = () => localStorage.setItem(WISH_KEY, JSON.stringify([...wishlist]));
function productImage(p) {
  if (Array.isArray(p.images) && p.images.length && p.images[0]) return p.images[0];
  if (Array.isArray(p.imgs) && p.imgs.length && p.imgs[0]) return p.imgs[0];
  if (p.image_url) return p.image_url;
  return '';
}

function starsHTML(r) {
  return Array.from({length:5}, (_,i) =>
    `<svg class="star ${i < Math.round(r) ? 'f' : 'e'}" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`
  ).join('');
}

/* ── PRODUCT CARD HTML ── */
function cardHTML(p, delay = 0) {
  const badgeCls = {new:'b-new',limited:'b-ltd',sale:'b-sale'};
  const badgeLbl = {new:'New',limited:'Limited',sale:'Sale'};
  const isWish = wishlist.has(p.id);
  return `<div class="product-card reveal" style="transition-delay:${delay}s" data-id="${p.id}" onclick="goToProduct(${p.id})">
    <div class="pc-img">
      <div class="pc-inner">
        <img src="${productImage(p)}" alt="${p.name}" loading="lazy" onerror="this.closest('.product-card') && this.closest('.product-card').remove()">
      </div>
      ${p.badge ? `<span class="pc-badge ${badgeCls[p.badge]}">${badgeLbl[p.badge]}</span>` : ''}
      <button class="pc-wish ${isWish?'on':''}" onclick="event.stopPropagation();toggleWishlist(${p.id},this)">
        <svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
      </button>
      <div class="pc-hover">
        <span class="pc-hover-nm">${p.name}</span>
        <button class="qv-btn" onclick="event.stopPropagation();openQV(${p.id})">Quick View</button>
      </div>
    </div>
    <div class="pc-info">
      <p class="pc-cat">${p.category || p.cat || ''}</p>
      <h3 class="pc-name">${p.name}</h3>
      <div class="pc-bot">
        <span class="pc-price">${fmt(p.price)}</span>
        <div class="pc-stars">${starsHTML(p.rating)}<span class="pc-rc">(${p.reviews})</span></div>
      </div>
    </div>
  </div>`;
}

/* ── RENDER HELPERS ── */
function getFiltered() {
  let items = [...PRODUCTS];
  if (currentFilter !== 'all') items = items.filter(p => (p.category || p.cat)?.toLowerCase() === currentFilter?.toLowerCase());
  items = items.filter(p => p.price >= priceRange.min && p.price <= priceRange.max);
  if (currentSort === 'price-asc') items.sort((a,b) => a.price - b.price);
  else if (currentSort === 'price-desc') items.sort((a,b) => b.price - a.price);
  else if (currentSort === 'name') items.sort((a,b) => a.name.localeCompare(b.name));
  else if (currentSort === 'rating') items.sort((a,b) => b.rating - a.rating);
  return items;
}

function renderGrid(containerId, items) {
  const g = $(containerId);
  if (!g) return;
  const validItems = items.filter((p) => !!productImage(p));
  g.innerHTML = validItems.map((p,i) => cardHTML(p, i * 0.045)).join('');
  setTimeout(observeReveals, 60);
}

/* ── SHOP PAGE ── */
function renderShop() {
  const items = getFiltered();
  const validItems = items.filter((p) => !!productImage(p));
  renderGrid('shopGrid', validItems);
  const cnt = $('resCnt');
  if (cnt) cnt.textContent = `${validItems.length} piece${validItems.length!==1?'s':''}`;
}

function filterProducts(btn, cat) {
  document.querySelectorAll('.f-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentFilter = cat;
  renderShop();
}

function sortProducts(val) { currentSort = val; renderShop(); }

function togglePricePanel() {
  const p = $('pricePanel'), b = $('priceBtnEl');
  p && p.classList.toggle('open');
  b && b.classList.toggle('on');
}

function applyPriceFilter() {
  priceRange.min = parseInt($('ppMin').value) || 0;
  priceRange.max = parseInt($('ppMax').value) || 9999;
  renderShop();
  $('pricePanel') && $('pricePanel').classList.remove('open');
  $('priceBtnEl') && $('priceBtnEl').classList.remove('on');
  showToast(`Filter: ${fmt(priceRange.min)} – ${fmt(priceRange.max)}`);
}

/* ── HOME PRODUCTS ── */
function renderHomeProducts() {
  renderGrid('homeProducts', PRODUCTS.filter(p => p.badge === 'new').slice(0, 4));
}

/* ── QUICK VIEW MODAL ── */
function openQV(id) {
  const p = PRODUCTS.find(x => x.id === id);
  if (!p) return;
  currentProduct = p;

  $('qvCat').textContent = p.category || p.cat || '';
  $('qvName').textContent = p.name;
  $('qvDesc').textContent = p.description || p.desc || '';

  const origPrice = p.badge === 'sale' ? Math.round(p.price * 1.2) : null;
  $('qvPriceRow').innerHTML = `<span class="qv-price">${fmt(p.price)}</span>${origPrice ? `<span class="qv-orig">${fmt(origPrice)}</span>` : ''}`;
  $('qvRating').innerHTML = `<div class="pc-stars">${starsHTML(p.rating)}</div><span style="font-size:.78rem;color:var(--text2)">${p.rating} · ${p.reviews} reviews</span>`;

  const images = (Array.isArray(p.images) && p.images.length) ? p.images : (Array.isArray(p.imgs) && p.imgs.length) ? p.imgs : [productImage(p)];
  $('qvMainImg').src = images[0];
  $('qvThumbs').innerHTML = images.map((img, i) =>
    `<div class="qv-thumb ${i===0?'active':''}" onclick="switchQVImg(this,'${img}')"><img src="${img}" alt=""></div>`
  ).join('');

  if ($('qvSizes')) $('qvSizes').innerHTML = '';

  $('qvAddBtn').onclick = () => { addToCart(p); closeQV(); };
  $('qvBuyBtn').onclick = async () => {
    await addToCart(p);
    closeQV();
    goToPage('cart');
  };

  $('qvOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeQV() {
  $('qvOverlay').classList.remove('open');
  document.body.style.overflow = '';
  currentProduct = null;
}

function switchQVImg(thumb, src) {
  $('qvMainImg').src = src;
  document.querySelectorAll('.qv-thumb').forEach(t => t.classList.remove('active'));
  thumb.classList.add('active');
}

function selectSize(btn, size) {
  document.querySelectorAll('#qvSizes .sz-btn, #pdSizes .sz-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (currentProduct) selectedSizes[currentProduct.id] = size;
}

/* ── WISHLIST ── */
async function toggleWishlist(id, btn) {
  if (window.IS_AUTHENTICATED) {
    const res = await fetch(`/wishlist/toggle/${id}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || !data.success) {
      showToast(data.error || 'Wishlist update failed', 'err');
      return;
    }
    btn && btn.classList.toggle('on', data.in_wishlist);
    if (Array.isArray(window.PROFILE_WISHLIST)) {
      if (data.in_wishlist) {
        const match = PRODUCTS.find((p) => p.id === id);
        if (match && !window.PROFILE_WISHLIST.find((p) => p.id === id)) {
          window.PROFILE_WISHLIST.unshift(match);
        }
      } else {
        window.PROFILE_WISHLIST = window.PROFILE_WISHLIST.filter((p) => p.id !== id);
      }
      renderWishlistPage();
    }
    showToast(data.in_wishlist ? 'Added to wishlist ♥' : 'Removed from wishlist', 'ok');
    return;
  }
  if (wishlist.has(id)) {
    wishlist.delete(id);
    btn && btn.classList.remove('on');
    showToast('Removed from wishlist');
  } else {
    wishlist.add(id);
    btn && btn.classList.add('on');
    showToast('Added to wishlist ♥');
  }
  saveWish();
  renderWishlistPage();
}

/* ── CART ── */
async function addToCart(p) {
  if (window.IS_AUTHENTICATED) {
    const res = await fetch('/cart/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: p.id, quantity: 1 })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || 'Failed to add to cart', 'err');
      return;
    }
    await refreshServerCartUI();
    showToast(`${p.name} added to cart`, 'ok');
    return;
  }
  const ex = cart.find(i => i.id === p.id);
  if (ex) ex.qty++;
  else cart.push({ id: p.id, name: p.name, price: p.price, category: p.category || p.cat, qty: 1, img: productImage(p) });
  saveCart();
  updateCartUI();
  showToast(`${p.name} added to cart`, 'ok');
}

function removeFromCart(id) {
  cart = cart.filter(i => i.id !== id);
  saveCart(); updateCartUI(); renderCartPage();
}

function changeQty(id, delta) {
  const item = cart.find(i => i.id === id);
  if (item) { item.qty += delta; if (item.qty <= 0) { cart = cart.filter(i => i.id !== id); } }
  saveCart(); updateCartUI(); renderCartPage();
}

function updateCartUI() {
  if (window.IS_AUTHENTICATED) {
    refreshServerCartUI();
    return;
  }
  const total = cart.reduce((s,i) => s + i.price * i.qty, 0);
  const count = cart.reduce((s,i) => s + i.qty, 0);
  document.querySelectorAll('.cart-badge').forEach(el => el.textContent = count);

  const body = $('cartBody');
  const footer = $('cartFt');
  if (!body) return;

  if (cart.length === 0) {
    body.innerHTML = `<div class="cart-empty-st"><svg viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg><p>Your cart is empty</p><button class="btn btn-p btn-sm" onclick="toggleCart();goToPage('shop')" style="margin-top:.5rem">Browse Collection</button></div>`;
    if (footer) footer.style.display = 'none';
  } else {
    body.innerHTML = cart.map(i => `
      <div class="ci">
        <div class="ci-img"><img src="${i.img || productImage(i)}" alt="${i.name}" onerror="this.style.opacity=0"></div>
        <div>
          <p class="ci-name">${i.name}</p>
          <p class="ci-meta">${i.category || i.cat || ''}</p>
          <div class="ci-qrow">
            <button class="ci-qb" onclick="changeQty(${i.id},-1)">−</button>
            <span class="ci-qn">${i.qty}</span>
            <button class="ci-qb" onclick="changeQty(${i.id},1)">+</button>
          </div>
          <span class="ci-rm" onclick="removeFromCart(${i.id})">Remove</span>
        </div>
        <span class="ci-price">${fmt(i.price * i.qty)}</span>
      </div>`).join('');
    if (footer) {
      footer.style.display = 'block';
      $('cartSubtotal') && ($('cartSubtotal').textContent = fmt(total));
      $('cartTotal') && ($('cartTotal').textContent = fmt(total));
    }
  }
}

async function refreshServerCartUI() {
  try {
    const res = await fetch('/cart/mini');
    if (!res.ok) return;
    const data = await res.json();
    document.querySelectorAll('.cart-badge').forEach(el => el.textContent = data.count || 0);
    const body = $('cartBody');
    const footer = $('cartFt');
    if (!body) return;
    if (!data.items || !data.items.length) {
      body.innerHTML = `<div class="cart-empty-st"><svg viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg><p>Your cart is empty</p></div>`;
      if (footer) footer.style.display = 'none';
      return;
    }
    body.innerHTML = data.items.map(i => `
      <div class="ci">
        <div class="ci-img"><img src="${i.image_url || ''}" alt="${i.name}" onerror="this.style.opacity=0"></div>
        <div>
          <p class="ci-name">${i.name}</p>
          <div class="ci-qrow"><span class="ci-qn">Qty: ${i.quantity}</span></div>
        </div>
        <span class="ci-price">${fmt(i.line_total)}</span>
      </div>`).join('');
    if (footer) {
      footer.style.display = 'block';
      $('cartSubtotal') && ($('cartSubtotal').textContent = fmt(data.total || 0));
      $('cartTotal') && ($('cartTotal').textContent = fmt(data.total || 0));
    }
  } catch (_) {}
}

function toggleCart() {
  $('cartSidebar').classList.toggle('open');
  $('cartOverlay').classList.toggle('open');
  const isOpen = $('cartSidebar').classList.contains('open');
  document.body.style.overflow = isOpen ? 'hidden' : '';
}

/* ── CART PAGE ── */
function renderCartPage() {
  const col = $('cartItemsCol');
  if (!col) return;
  const total = cart.reduce((s,i) => s + i.price * i.qty, 0);

  if (cart.length === 0) {
    col.innerHTML = `<div style="text-align:center;padding:4rem 1rem">
      <p style="font-family:'Cormorant Garamond',serif;font-size:1.8rem;font-weight:300;margin-bottom:1rem">Your cart is empty</p>
      <button class="btn btn-p" onclick="goToPage('shop')">Browse Collection</button>
    </div>`;
    $('cartSumCol') && ($('cartSumCol').style.display = 'none');
    return;
  }

  $('cartSumCol') && ($('cartSumCol').style.display = '');
  col.innerHTML = `
    <h2 class="cart-pg-title">Cart <span style="font-family:'DM Mono',monospace;font-size:1rem;color:var(--text3)">(${cart.reduce((s,i)=>s+i.qty,0)} items)</span></h2>
    <div class="cart-tbl-hd"><span>Product</span><span>Price</span><span>Qty</span><span>Total</span><span></span></div>
    ${cart.map(i => `
      <div class="cart-row">
        <div class="ctr-prod">
          <div class="ctr-thumb"><img src="${i.img || productImage(i)}" alt="${i.name}" onerror="this.style.opacity=0"></div>
          <div><p class="ctr-name">${i.name}</p><p class="ctr-meta">${i.cat || ''}</p></div>
        </div>
        <span class="ctr-price">${fmt(i.price)}</span>
        <div class="ci-qrow">
          <button class="ci-qb" onclick="changeQty(${i.id},-1)">−</button>
          <span class="ci-qn">${i.qty}</span>
          <button class="ci-qb" onclick="changeQty(${i.id},1)">+</button>
        </div>
        <span class="ctr-total">${fmt(i.price * i.qty)}</span>
        <button class="ctr-rm" onclick="removeFromCart(${i.id})">✕</button>
      </div>`).join('')}
    <div class="coupon-row">
      <input class="coupon-in" id="couponInput" placeholder="Coupon code">
      <button class="btn btn-g btn-sm" onclick="applyCoupon()">Apply</button>
    </div>`;

  const smr = $('cartSumCol');
  if (smr) smr.innerHTML = `
    <h3 class="smr-title">Order Summary</h3>
    <div class="smr-row"><span>Subtotal</span><span>${fmt(total)}</span></div>
    <div class="smr-row"><span>Shipping</span><span>Free</span></div>
    <div class="smr-row"><span>Discount</span><span id="discountAmt">—</span></div>
    <div class="smr-row tot"><span>Total</span><span>${fmt(total)}</span></div>
    <button class="checkout-btn" onclick="handleCheckout()">Proceed to Checkout</button>
    <div style="margin-top:1rem;display:flex;flex-direction:column;gap:.5rem">
      <div style="display:flex;align-items:center;gap:.5rem;font-size:.65rem;color:var(--text3)">🔒 SSL encrypted checkout</div>
      <div style="display:flex;align-items:center;gap:.5rem;font-size:.65rem;color:var(--text3)">📦 Free returns within 30 days</div>
      <div style="display:flex;align-items:center;gap:.5rem;font-size:.65rem;color:var(--text3)">💳 GCash, Maya, Credit Card accepted</div>
    </div>`;
}

function applyCoupon() {
  const code = ($('couponInput') || {}).value || '';
  if (code.toUpperCase() === 'LOOPH10') showToast('10% discount applied!', 'ok');
  else if (code.toUpperCase() === 'WELCOME') showToast('Free shipping applied!', 'ok');
  else showToast('Invalid coupon code', 'err');
}

async function quickBuyNow(productId) {
  const product = PRODUCTS.find((x) => x.id === productId);
  if (!product) return;
  await addToCart(product);
  goToPage('cart');
}

function handleCheckout() {
  if (cart.length === 0) { showToast('Your cart is empty', 'err'); return; }
  showToast('Redirecting to checkout…', 'ok');
  setTimeout(() => { cart = []; saveCart(); updateCartUI(); renderCartPage(); showToast('Order placed! Thank you 🎉', 'ok'); }, 1500);
}

/* ── SEARCH ── */
function toggleSearch() {
  const ov = $('searchOverlay');
  ov.classList.toggle('open');
  if (ov.classList.contains('open')) {
    $('searchInput').value = '';
    renderSearchResults(PRODUCTS.slice(0, 6));
    $('searchLbl').textContent = 'Trending now';
    setTimeout(() => $('searchInput').focus(), 100);
    document.body.style.overflow = 'hidden';
  } else { document.body.style.overflow = ''; }
}

function renderSearchResults(items) {
  $('searchGrid').innerHTML = items.slice(0, 6).map(p => `
    <div class="src-card" onclick="toggleSearch();openQV(${p.id})">
      <div class="src-img"><img src="${productImage(p)}" alt="${p.name}" onerror="this.style.opacity=0"></div>
      <div><p class="src-name">${p.name}</p><p class="src-price">${fmt(p.price)}</p></div>
    </div>`).join('');
}

function liveSearch(q) {
  if (!q.trim()) { renderSearchResults(PRODUCTS.slice(0,6)); $('searchLbl').textContent = 'Trending now'; return; }
  const res = PRODUCTS.filter(p => p.name.toLowerCase().includes(q.toLowerCase()) || (p.category || p.cat || '').toLowerCase().includes(q.toLowerCase()) || (p.description || p.desc || '').toLowerCase().includes(q.toLowerCase()));
  renderSearchResults(res);
  $('searchLbl').textContent = `${res.length} result${res.length!==1?'s':''} for "${q}"`;
}

function quickSearch(q) { $('searchInput').value = q; liveSearch(q); }

/* ── NAVIGATION ── */
function goToPage(name) {
  if (window.ROUTES && window.ROUTES[name]) {
    window.location.href = window.ROUTES[name];
    return;
  }
}

function goToProduct(id) {
  window.location.href = `/product/${id}`;
}

async function confirmLogout(event) {
  if (event) event.preventDefault();
  const target = event && event.currentTarget ? event.currentTarget : null;
  const logoutUrl = (target && target.dataset && target.dataset.logoutUrl) ? target.dataset.logoutUrl : '/logout';
  const shouldLogout = await showAppModal({
    title: 'Confirm Logout',
    message: 'Log out of your account now?',
    confirmText: 'Logout',
    cancelText: 'Stay Signed In',
    variant: 'confirm'
  });
  if (!shouldLogout) return;
  try {
    const res = await fetch(logoutUrl, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!res.ok) {
      window.location.href = logoutUrl;
      return;
    }
    window.location.href = '/?toast=logout';
  } catch (_) {
    window.location.href = logoutUrl;
  }
}

/* ── PRODUCT DETAIL PAGE ── */
function renderProductDetail(id) {
  const p = PRODUCTS.find(x => x.id === id);
  if (!p) return;
  currentProduct = p;
  const wrap = $('pdWrap');
  if (!wrap) return;

  const origPrice = p.badge === 'sale' ? Math.round(p.price * 1.2) : null;
  const images = (Array.isArray(p.images) && p.images.length) ? p.images : (Array.isArray(p.imgs) && p.imgs.length) ? p.imgs : [productImage(p)];
  const reviews = [
    {author:'Alex R.',date:'Mar 2024',rating:5,text:'Great quality, fits perfectly. The fabric is soft and breathable — exactly what I needed for everyday wear.',verified:true},
    {author:'Sam T.',date:'Feb 2024',rating:4,text:'Love the design and the fit is great. Shipping was fast. Would definitely order again.',verified:true},
    {author:'Jamie L.',date:'Jan 2024',rating:5,text:'Looph never disappoints. This piece is incredibly versatile — I wear it almost every day.',verified:false},
  ];

  wrap.innerHTML = `
    <div class="pd-grid">
      <div class="pd-imgs">
        <img class="pd-main-img" id="pdMainImg" src="${images[0]}" alt="${p.name}" onerror="this.style.opacity=0">
        <div class="pd-thumb-strip">
          ${images.map((img, i) => `<div class="pd-thumb ${i===0?'active':''}" onclick="switchPDImg(this,'${img}')"><img src="${img}" alt=""></div>`).join('')}
        </div>
      </div>
      <div class="pd-info">
        <div class="pd-bc">
          <span onclick="goToPage('landing')">Home</span><span class="sep">›</span>
          <span onclick="goToPage('shop')">Shop</span><span class="sep">›</span>
          <span style="color:var(--text2)">${p.name}</span>
        </div>
        ${p.badge ? `<span class="pc-badge b-${p.badge}" style="align-self:flex-start">${{new:'New Arrival',ltd:'Limited Stock',sale:'On Sale'}[p.badge]}</span>` : ''}
        <h1 class="pd-name">${p.name}</h1>
        <div class="pd-price-box">
          <span class="pd-price">${fmt(p.price)}</span>
          ${origPrice ? `<span class="pd-orig">${fmt(origPrice)}</span>` : ''}
        </div>
        <div class="pd-rat-box">
          <div class="pc-stars">${starsHTML(p.rating)}</div>
          <span style="font-size:.8rem;color:var(--text2)">${p.rating} · ${p.reviews} verified reviews</span>
          <span style="font-size:.7rem;color:${p.stock < 5 ? 'var(--red)' : 'var(--green)'}">· ${p.stock < 5 ? `Only ${p.stock} left!` : 'In stock'}</span>
        </div>
        <p class="pd-desc">${p.description || p.desc || ''}</p>
        <div class="pd-qty-row">
          <span class="pd-qty-lbl">Qty</span>
          <div class="qty-ctrl">
            <button class="qty-b" onclick="changePDQty(-1)">−</button>
            <span class="qty-n" id="pdQty">1</span>
            <button class="qty-b" onclick="changePDQty(1)">+</button>
          </div>
        </div>
        <div class="pd-ctas">
          <button class="btn btn-p" onclick="addToCart(PRODUCTS.find(x=>x.id===${p.id}))">
            <svg viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            Add to Cart
          </button>
          <button class="btn btn-g" onclick="quickBuyNow(${p.id})">Buy Now</button>
        </div>
        <div class="acc">
          ${[
            ['Details & Materials','100% premium cotton. Machine wash cold. Tumble dry low. Do not bleach. Imported.'],
            ['Sizing & Fit','Model is 5\'11" wearing a Medium. Relaxed fit — size down for a more tailored look.'],
            ['Shipping & Returns','Free shipping on orders over ₱2,000. Returns accepted within 30 days of delivery. Items must be unworn and in original condition.'],
          ].map(([title, body]) => `
            <div class="acc-item">
              <div class="acc-hd" onclick="toggleAcc(this)">${title}<svg viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></div>
              <div class="acc-body"><div class="acc-inner">${body}</div></div>
            </div>`).join('')}
        </div>
        <div style="padding-top:1rem;display:flex;gap:1.25rem;flex-wrap:wrap">
          <span style="font-size:.65rem;color:var(--text3);display:flex;align-items:center;gap:.35rem"><span style="color:var(--green)">✓</span> Free shipping over ₱2,000</span>
          <span style="font-size:.65rem;color:var(--text3);display:flex;align-items:center;gap:.35rem"><span style="color:var(--green)">✓</span> 30-day returns</span>
          <span style="font-size:.65rem;color:var(--text3);display:flex;align-items:center;gap:.35rem"><span style="color:var(--green)">✓</span> Secure checkout</span>
        </div>
      </div>
    </div>
    <div class="pd-reviews">
      <h3 style="font-family:'Cormorant Garamond',serif;font-size:1.8rem;font-weight:300;margin-bottom:.4rem">Customer Reviews</h3>
      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem">
        <div class="pc-stars">${starsHTML(p.rating)}</div>
        <span style="font-size:.82rem;color:var(--text2)">${p.rating} average · ${p.reviews} reviews</span>
      </div>
      <div class="reviews-grid">
        ${reviews.map(r => `<div class="rv-card">
          <div class="rv-hd"><div><p class="rv-author">${r.author}</p><div class="pc-stars" style="margin-top:.2rem">${starsHTML(r.rating)}</div></div><p class="rv-date">${r.date}</p></div>
          <p class="rv-text">${r.text}</p>
          ${r.verified ? '<p class="rv-verified">✓ Verified Purchase</p>' : ''}
        </div>`).join('')}
      </div>
    </div>`;
}

let pdQtyVal = 1;
function changePDQty(d) {
  pdQtyVal = Math.max(1, pdQtyVal + d);
  const el = $('pdQty'); if (el) el.textContent = pdQtyVal;
}
function switchPDImg(thumb, src) {
  $('pdMainImg') && ($('pdMainImg').src = src);
  document.querySelectorAll('.pd-thumb').forEach(t => t.classList.remove('active'));
  thumb.classList.add('active');
}

/* ── ACCORDION ── */
function toggleAcc(hd) {
  const body = hd.nextElementSibling;
  const isOpen = hd.classList.contains('open');
  document.querySelectorAll('.acc-hd').forEach(h => { h.classList.remove('open'); h.nextElementSibling.classList.remove('open'); });
  if (!isOpen) { hd.classList.add('open'); body.classList.add('open'); }
}

/* ── ADMIN PAGES ── */
let adminDashboardState = { revenue: null, transactions: [] };
let dashboardOrdersFilterStatus = 'all';
let dashboardOrdersFilterPayment = 'all';
let dashboardOrdersFilterPaymentState = 'all';
let adminCustomersState = [];
let posAmountPaid = '';
function statusMeta(rawStatus) {
  const status = String(rawStatus || 'processing').toLowerCase();
  if (status === 'cancelled') return { cls: 's-can', label: 'CANCELLED' };
  if (status === 'shipped') return { cls: 's-ship', label: 'SHIPPED' };
  if (status === 'delivered' || status === 'completed') return { cls: 's-del', label: status.toUpperCase() };
  return { cls: 's-proc', label: 'PROCESSING' };
}
function formatVoucherType(type) {
  const map = {
    min_spend_discount: 'Min Spend',
    product_discount: 'Product Discount',
    free_delivery: 'Free Delivery',
    bogo: 'BOGO'
  };
  return map[type] || String(type || '').replaceAll('_', ' ');
}
function formatStatusSelect(status, id) {
  const value = String(status || 'processing').toLowerCase();
  const options = ['processing', 'shipped', 'delivered', 'completed', 'cancelled']
    .map((s) => `<option value="${s}" ${s === value ? 'selected' : ''}>${s.replace('_', ' ').toUpperCase()}</option>`)
    .join('');
  return `<select class="admin-input" style="max-width:160px;padding:.3rem .45rem;font-size:.65rem" onchange="updateAdminOrderStatus(${id}, this.value)">${options}</select>`;
}
function closeAllActionMenus() {
  document.querySelectorAll('.menu-pop.open').forEach((menu) => menu.classList.remove('open'));
}
function toggleActionMenu(menuId, event) {
  if (event) event.stopPropagation();
  const menu = document.getElementById(menuId);
  if (!menu) return;
  const willOpen = !menu.classList.contains('open');
  closeAllActionMenus();
  if (willOpen) menu.classList.add('open');
}
function actionMenuHTML(menuId, items) {
  return `<div class="menu-wrap">
    <button class="meatball-btn" onclick="toggleActionMenu('${menuId}', event)" aria-label="Actions">⋯</button>
    <div class="menu-pop" id="${menuId}">
      ${items.map((item) => `<button class="menu-item ${item.danger ? 'danger' : ''}" onclick="closeAllActionMenus();${item.onClick}">${item.label}</button>`).join('')}
    </div>
  </div>`;
}
function renderAdminDashboard() {
  Promise.all([
    fetch('/admin/revenue').then(r => r.json()),
    fetch('/admin/orders?limit=10').then(r => r.json()),
    fetch('/admin/revenue/history?months=2').then(r => r.json())
  ]).then(([revenueData, ordersData, historyData]) => {
    const rev = (revenueData && revenueData.success) ? revenueData.revenue : null;
    const txns = (ordersData && ordersData.success) ? (ordersData.transactions || []) : [];
    adminDashboardState = { revenue: rev, transactions: txns };
    const kpiEl = $('kpiGrid');
    if (kpiEl && rev) {
      const customerCount = new Set(
        txns
          .filter((t) => t.record_type === 'customer_order' && (t.customer_email || t.customer_name))
          .map((t) => (t.customer_email || t.customer_name || '').toLowerCase())
      ).size;
      const kpis = [
        {key:'revenue',label:'Revenue',val:fmt(rev.total || 0)},
        {key:'orders',label:'Orders',val:String((rev.orders_count || 0) + (rev.pos_count || 0))},
        {key:'customers',label:'Customers',val:String(customerCount)},
        {key:'avg',label:'Avg Order',val:fmt(rev.avg_order_value || 0)}
      ];
      const history = (historyData && historyData.success ? historyData.history : []) || [];
      const latest = history.length ? history[history.length - 1] : null;
      const previous = history.length > 1 ? history[history.length - 2] : null;
      const pct = (curr, prev) => {
        if (!prev || prev === 0) return curr > 0 ? 100 : 0;
        return ((curr - prev) / prev) * 100;
      };
      const deltas = {
        revenue: pct(latest ? latest.total || 0 : rev.total || 0, previous ? previous.total || 0 : 0),
        orders: pct(
          latest ? (latest.orders_count || 0) + (latest.pos_count || 0) : (rev.orders_count || 0) + (rev.pos_count || 0),
          previous ? (previous.orders_count || 0) + (previous.pos_count || 0) : 0
        ),
        customers: pct(
          new Set((txns || []).filter(t => t.record_type === 'customer_order').map(t => (t.customer_email || t.customer_name || '').toLowerCase())).size,
          previous ? (previous.orders_count || 0) : 0
        ),
        avg: pct(latest ? ((latest.total || 0) / Math.max(1, (latest.orders_count || 0) + (latest.pos_count || 0))) : (rev.avg_order_value || 0),
          previous ? ((previous.total || 0) / Math.max(1, (previous.orders_count || 0) + (previous.pos_count || 0))) : 0)
      };
      kpiEl.innerHTML = kpis.map(k => {
        const d = Number(deltas[k.key] || 0);
        const cls = d >= 0 ? 'kpi-ch' : 'kpi-ch neg';
        const sign = d >= 0 ? '+' : '';
        return `<div class="kpi-card reveal clickable" onclick="openDashboardMetricModal('${k.key}')"><p class="kpi-lbl">${k.label}</p><p class="kpi-val">${k.val}</p><p class="${cls}">${sign}${d.toFixed(1)}% vs previous month</p></div>`;
      }).join('');
    }
    const ordTbl = $('dashOrdersTable');
    if (ordTbl && ordersData && ordersData.success) {
      ordTbl.innerHTML = txns.map(o => {
        const meta = statusMeta(o.status);
        const rowMenu = o.record_type === 'customer_order'
          ? actionMenuHTML(`order-menu-${o.id}`, [
              { label: 'Set Processing', onClick: `updateAdminOrderStatus(${o.id}, 'processing')` },
              { label: 'Set Shipped', onClick: `updateAdminOrderStatus(${o.id}, 'shipped')` },
              { label: 'Set Delivered', onClick: `updateAdminOrderStatus(${o.id}, 'delivered')` },
              { label: 'Set Completed', onClick: `updateAdminOrderStatus(${o.id}, 'completed')` },
              { label: 'Set Cancelled', onClick: `updateAdminOrderStatus(${o.id}, 'cancelled')`, danger: true }
            ])
          : actionMenuHTML(`order-menu-${o.reference}`, [
              { label: 'View Details', onClick: `openOrderDetailsModal(${JSON.stringify(o.reference)})` }
            ]);
        return `<tr>
          <td>${o.reference || '#' + o.id}</td>
          <td>${o.customer_name || 'Walk-in'}</td>
          <td>${(o.items || []).length}</td>
          <td style="font-family:'DM Mono',monospace;color:var(--accent)">${fmt(o.total_amount || 0)}</td>
          <td><span class="o-status ${meta.cls}">${meta.label}</span></td>
          <td>${o.created_at_display || ''}</td>
          <td style="text-align:right">${rowMenu}</td>
        </tr>`;
      }).join('');
    }
    setTimeout(observeReveals, 60);
  }).catch(() => showToast('Failed to load dashboard data', 'err'));
}
async function updateAdminOrderStatus(orderId, status) {
  const res = await fetch(`/admin/orders/${orderId}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  const data = await res.json();
  if (!res.ok || !data.success) {
    showToast(data.error || 'Failed to update status', 'err');
    return;
  }
  showToast('Order status updated', 'ok');
  renderAdminDashboard();
}
function openDashboardMetricModal(metricKey) {
  const overlay = $('dashboardMetricOverlay');
  const title = $('dashboardMetricTitle');
  const body = $('dashboardMetricBody');
  if (!overlay || !title || !body) return;
  const txns = Array.isArray(adminDashboardState.transactions) ? adminDashboardState.transactions : [];
  const revenue = adminDashboardState.revenue || {};
  const customerTxns = txns.filter((t) => t.record_type === 'customer_order');
  if (metricKey === 'revenue') {
    title.textContent = 'Revenue Breakdown';
    fetch('/admin/revenue/history?months=6').then(r => r.json()).then(historyData => {
      const rows = (historyData && historyData.success ? historyData.history : []) || [];
      body.innerHTML = `
        <p style="margin-bottom:.4rem">Current Total Revenue: <strong>${fmt(revenue.total || 0)}</strong></p>
        <p style="margin-bottom:.7rem">Orders: ${fmt(revenue.from_orders || 0)} · POS: ${fmt(revenue.from_pos || 0)}</p>
        <div class="admin-tbl-wrap" style="margin-top:.6rem">
          <table class="admin-tbl">
            <thead><tr><th>Period</th><th>Orders</th><th>POS</th><th>Total</th></tr></thead>
            <tbody>${rows.map((h) => `<tr><td>${h.period_label}</td><td>${fmt(h.from_orders || 0)}</td><td>${fmt(h.from_pos || 0)}</td><td>${fmt(h.total || 0)}</td></tr>`).join('')}</tbody>
          </table>
        </div>
      `;
    }).catch(() => {
      body.innerHTML = `<p>Total Revenue: <strong>${fmt(revenue.total || 0)}</strong></p>`;
    });
  } else if (metricKey === 'orders') {
    title.textContent = 'Orders Breakdown';
    const renderOrdersDetail = () => {
      const statusFilter = dashboardOrdersFilterStatus;
      const paymentFilter = dashboardOrdersFilterPayment;
      const paymentStateFilter = dashboardOrdersFilterPaymentState;
      const filtered = txns.filter((o) => {
        const status = String(o.status || 'processing').toLowerCase();
        const payment = String(o.payment_method || '').toLowerCase();
        const isPaid = ['gcash', 'card', 'cash', 'credit_card', 'paypal', 'bank_transfer'].includes(payment) || ['delivered', 'completed'].includes(status);
        const paymentState = isPaid ? 'paid' : 'pending';
        const statusOk = statusFilter === 'all' || status === statusFilter;
        const paymentOk = paymentFilter === 'all' || payment === paymentFilter;
        const paymentStateOk = paymentStateFilter === 'all' || paymentState === paymentStateFilter;
        return statusOk && paymentOk && paymentStateOk;
      });
      const rowsHtml = filtered.map((o) => {
        const itemNames = (o.items || []).map((i) => i.product_name || `Item ${i.product_id || ''}`).join(', ') || '—';
        return `<tr>
          <td>${o.reference || '#' + o.id}</td>
          <td>${o.customer_name || 'Walk-in'}</td>
          <td>${itemNames}</td>
          <td>${String(o.status || 'processing').replaceAll('_', ' ').toUpperCase()}</td>
          <td>${String(o.payment_method || '').toUpperCase()}</td>
        </tr>`;
      }).join('');
      body.innerHTML = `
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.8rem">
          <select class="admin-input" id="ordersFilterStatus" style="max-width:220px" onchange="dashboardOrdersFilterStatus=this.value;openDashboardMetricModal('orders')">
            <option value="all" ${statusFilter === 'all' ? 'selected' : ''}>All Status</option>
            <option value="processing" ${statusFilter === 'processing' ? 'selected' : ''}>Processing</option>
            <option value="shipped" ${statusFilter === 'shipped' ? 'selected' : ''}>Shipped</option>
            <option value="delivered" ${statusFilter === 'delivered' ? 'selected' : ''}>Delivered</option>
            <option value="completed" ${statusFilter === 'completed' ? 'selected' : ''}>Completed</option>
            <option value="cancelled" ${statusFilter === 'cancelled' ? 'selected' : ''}>Cancelled</option>
          </select>
          <select class="admin-input" id="ordersFilterPayment" style="max-width:220px" onchange="dashboardOrdersFilterPayment=this.value;openDashboardMetricModal('orders')">
            <option value="all" ${paymentFilter === 'all' ? 'selected' : ''}>All Payments</option>
            <option value="cod" ${paymentFilter === 'cod' ? 'selected' : ''}>COD</option>
            <option value="gcash" ${paymentFilter === 'gcash' ? 'selected' : ''}>GCash</option>
            <option value="cash" ${paymentFilter === 'cash' ? 'selected' : ''}>Cash</option>
            <option value="card" ${paymentFilter === 'card' ? 'selected' : ''}>Card</option>
          </select>
          <select class="admin-input" id="ordersFilterPaymentState" style="max-width:220px" onchange="dashboardOrdersFilterPaymentState=this.value;openDashboardMetricModal('orders')">
            <option value="all" ${paymentStateFilter === 'all' ? 'selected' : ''}>All Payment States</option>
            <option value="paid" ${paymentStateFilter === 'paid' ? 'selected' : ''}>Paid</option>
            <option value="pending" ${paymentStateFilter === 'pending' ? 'selected' : ''}>Pending</option>
          </select>
        </div>
        <div class="admin-tbl-wrap">
          <table class="admin-tbl">
            <thead><tr><th>Order</th><th>Customer</th><th>Purchased Items</th><th>Status</th><th>Payment</th></tr></thead>
            <tbody>${rowsHtml || '<tr><td colspan="5" style="text-align:center;color:var(--text3)">No orders found for filters.</td></tr>'}</tbody>
          </table>
        </div>
      `;
    };
    renderOrdersDetail();
  } else if (metricKey === 'customers') {
    title.textContent = 'Customers Breakdown';
    fetch('/admin/customers').then(r => r.json()).then(data => {
      const customers = (data && data.success ? data.customers : []) || [];
      adminCustomersState = customers;
      body.innerHTML = `
        <p style="margin-bottom:.5rem">Total customers: <strong>${customers.length}</strong></p>
        <div class="admin-tbl-wrap">
          <table class="admin-tbl">
            <thead><tr><th>Name</th><th>Email</th><th>Joined</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody>
              ${customers.map((c) => `<tr>
                <td>${c.full_name || c.username}</td>
                <td>${c.email}</td>
                <td>${c.created_at_display || ''}</td>
                <td style="text-align:right">
                  ${actionMenuHTML(`customer-menu-${c.id}`, [{ label: 'Delete Customer', onClick: `deleteCustomer(${c.id})`, danger: true }])}
                </td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>
      `;
    }).catch(() => {
      body.innerHTML = '<p>Failed to load customers.</p>';
    });
  } else {
    title.textContent = 'Average Order Value';
    body.innerHTML = `
      <p>Average Order Value: <strong>${fmt(revenue.avg_order_value || 0)}</strong></p>
      <p>Computed from total revenue divided by customer orders and POS sales.</p>
    `;
  }
  overlay.classList.add('open');
}
function openOrderDetailsModal(reference) {
  const title = $('dashboardMetricTitle');
  const body = $('dashboardMetricBody');
  const overlay = $('dashboardMetricOverlay');
  if (!title || !body || !overlay) return;
  const order = (adminDashboardState.transactions || []).find((t) => String(t.reference) === String(reference));
  if (!order) return;
  const items = (order.items || []).map((i) => `<li>${(i.product_name || 'Item')} x${i.quantity || 0} — ${fmt((i.price || 0) * (i.quantity || 0))}</li>`).join('');
  title.textContent = `Order ${order.reference}`;
  body.innerHTML = `
    <p><strong>Customer:</strong> ${order.customer_name || 'Walk-in'}</p>
    <p><strong>Email:</strong> ${order.customer_email || '—'}</p>
    <p><strong>Address:</strong> ${order.customer_address || '—'}</p>
    <p><strong>Processed By:</strong> ${order.processed_by || '—'}</p>
    <p><strong>Date/Time:</strong> ${order.created_at_display || '—'}</p>
    <p><strong>Status:</strong> ${String(order.status || 'processing').replaceAll('_', ' ').toUpperCase()}</p>
    <p><strong>Payment:</strong> ${String(order.payment_method || '').toUpperCase()}</p>
    <p><strong>Total:</strong> ${fmt(order.total_amount || 0)}</p>
    <p style="margin-top:.6rem"><strong>Items</strong></p>
    <ul style="padding-left:1rem">${items || '<li>No items.</li>'}</ul>
  `;
  overlay.classList.add('open');
}
async function deleteCustomer(customerId) {
  closeAllActionMenus();
  const ok = await showAppModal({
    title: 'Delete Customer',
    message: 'This will permanently remove the customer account and related data.',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    variant: 'confirm'
  });
  if (!ok) return;
  const res = await fetch(`/admin/customers/${customerId}`, { method: 'DELETE' });
  const data = await res.json();
  if (!res.ok || !data.success) {
    showToast(data.error || 'Failed to delete customer', 'err');
    return;
  }
  showToast('Customer deleted', 'ok');
  openDashboardMetricModal('customers');
}
function closeDashboardMetricModal() {
  const overlay = $('dashboardMetricOverlay');
  if (overlay) overlay.classList.remove('open');
}
function exportDashboardReport() {
  window.location.href = '/admin/dashboard/report/pdf';
}

function renderAdminInventory() {
  const products = Array.isArray(window.ADMIN_PRODUCTS) ? window.ADMIN_PRODUCTS : [];
  const invTbl = $('invTable');
  if (!invTbl) return;
  invTbl.innerHTML = products.map(p => `<tr>
    <td>${p.id}</td>
    <td><div style="display:flex;align-items:center;gap:.65rem"><div style="width:36px;height:44px;border-radius:2px;overflow:hidden;background:var(--bg3);flex-shrink:0">${p.image_url ? `<img src="${p.image_url}" alt="" style="width:100%;height:100%;object-fit:cover;opacity:.8" onerror="this.style.opacity=0">` : ''}</div>${p.name}</div></td>
    <td>${p.category || ''}</td>
    <td style="font-family:'DM Mono',monospace;color:var(--accent)">${fmt(p.price || 0)}</td>
    <td style="font-family:'DM Mono',monospace">${p.stock || 0}</td>
    <td>${p.badge || '—'}</td>
    <td style="text-align:right">${actionMenuHTML(`inventory-menu-${p.id}`, [
      { label: 'Edit Product', onClick: `openAdminProductModal(${p.id})` },
      { label: 'Delete Product', onClick: `deleteAdminProduct(${p.id})`, danger: true }
    ])}</td>
  </tr>`).join('');
  initAdminCategoryOptions();
}

function initAdminCategoryOptions() {
  const select = $('adminProductCategory');
  if (!select) return;
  const defaults = ['Shirts', 'Jackets', 'Pants', 'Accessories', 'Outerwear'];
  const fromProducts = (Array.isArray(window.ADMIN_PRODUCTS) ? window.ADMIN_PRODUCTS : [])
    .map((p) => (p.category || '').trim())
    .filter(Boolean);
  const options = [...new Set([...defaults, ...fromProducts])].sort((a, b) => a.localeCompare(b));
  const current = select.value;
  select.innerHTML = '<option value="">Select Category</option>' + options.map((c) => `<option value="${c}">${c}</option>`).join('');
  select.value = current || '';
}

function openAdminProductModal(productId) {
  const modal = $('adminProductModal');
  if (!modal) return;
  const p = (Array.isArray(window.ADMIN_PRODUCTS) ? window.ADMIN_PRODUCTS : []).find(x => x.id === productId);
  $('adminProductModalTitle').textContent = p ? 'Edit Product' : 'Add Product';
  $('adminProductId').value = p ? p.id : '';
  $('adminProductName').value = p ? (p.name || '') : '';
  $('adminProductDescription').value = p ? (p.description || '') : '';
  $('adminProductPrice').value = p ? (p.price || 0) : '';
  $('adminProductStock').value = p ? (p.stock || 0) : '';
  $('adminProductCategory').value = p ? (p.category || '') : '';
  $('adminProductImageUrl').value = p ? (p.image_url || '') : '';
  adminProductImages = p ? (Array.isArray(p.image_urls) && p.image_urls.length ? [...p.image_urls] : (p.image_url ? [p.image_url] : [])) : [];
  const urlsInput = $('adminProductImageUrls');
  if (urlsInput) urlsInput.value = adminProductImages.join('\n');
  if ($('adminProductImagePreview')) $('adminProductImagePreview').src = p ? (p.image_url || '') : '';
  $('adminProductBadge').value = p ? (p.badge || '') : '';
  const imageUrlInput = $('adminProductImageUrl');
  if (imageUrlInput && !imageUrlInput.dataset.boundPreview) {
    imageUrlInput.dataset.boundPreview = '1';
    imageUrlInput.addEventListener('input', () => {
      if ($('adminProductImagePreview')) $('adminProductImagePreview').src = imageUrlInput.value.trim();
    });
  }
  initAdminCategoryOptions();
  modal.style.display = 'flex';
}
function clearAdminProductImages() {
  adminProductImages = [];
  if ($('adminProductImageUrls')) $('adminProductImageUrls').value = '';
  if ($('adminProductImageUrl')) $('adminProductImageUrl').value = '';
  if ($('adminProductImagePreview')) $('adminProductImagePreview').src = '';
  showToast('Images cleared', 'ok');
}

function closeAdminProductModal() {
  const modal = $('adminProductModal');
  if (modal) modal.style.display = 'none';
}

async function saveAdminProduct() {
  const id = $('adminProductId').value;
  const manualUrls = (($('adminProductImageUrls') && $('adminProductImageUrls').value) || '')
    .split('\n').map((v) => v.trim()).filter(Boolean);
  const primaryImage = $('adminProductImageUrl').value.trim() || manualUrls[0] || adminProductImages[0] || '';
  const finalImages = [...new Set([primaryImage, ...adminProductImages, ...manualUrls].filter(Boolean))];
  const payload = {
    name: $('adminProductName').value.trim(),
    description: $('adminProductDescription').value.trim(),
    price: parseFloat($('adminProductPrice').value || 0),
    stock: parseInt($('adminProductStock').value || 0, 10),
    category: $('adminProductCategory').value.trim(),
    image_url: primaryImage,
    image_urls: finalImages,
    badge: $('adminProductBadge').value,
    tags: $('adminProductBadge').value ? [$('adminProductBadge').value] : []
  };
  const url = id ? `/admin/products/update/${id}` : '/admin/products/add';
  const method = id ? 'PUT' : 'POST';
  const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const data = await res.json();
  if (!res.ok || !data.success) { showToast(data.error || 'Failed to save product', 'err'); return; }
  showToast('Product saved', 'ok');
  window.location.reload();
}

async function uploadAdminProductImage() {
  const fileInput = $('adminProductImageFile');
  const files = fileInput && fileInput.files ? Array.from(fileInput.files) : [];
  if (!files.length) {
    showToast('Choose an image file first', 'err');
    return;
  }
  let uploaded = 0;
  for (const file of files) {
    const form = new FormData();
    form.append('image', file);
    const res = await fetch('/admin/products/upload-image', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok || !data.success) {
      showToast(data.error || 'Upload failed', 'err');
      continue;
    }
    uploaded += 1;
    adminProductImages.push(data.image_url || '');
  }
  adminProductImages = [...new Set(adminProductImages.filter(Boolean))];
  if (!$('adminProductImageUrl').value && adminProductImages.length) $('adminProductImageUrl').value = adminProductImages[0];
  if ($('adminProductImageUrls')) $('adminProductImageUrls').value = adminProductImages.join('\n');
  const preview = $('adminProductImagePreview');
  if (preview) preview.src = $('adminProductImageUrl').value || adminProductImages[0] || '';
  showToast(uploaded ? `${uploaded} image(s) uploaded` : 'No image uploaded', uploaded ? 'ok' : 'err');
}

async function deleteAdminProduct(productId) {
  const shouldDelete = await showAppModal({
    title: 'Delete Product',
    message: 'This will permanently remove the product. Continue?',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    variant: 'confirm'
  });
  if (!shouldDelete) return;
  const res = await fetch(`/admin/products/delete/${productId}`, { method: 'DELETE' });
  const data = await res.json();
  if (!res.ok || !data.success) { showToast(data.error || 'Delete failed', 'err'); return; }
  showToast('Product deleted', 'ok');
  window.location.reload();
}

function renderAdminPOS() {
  const source = Array.isArray(window.POS_PRODUCTS) && window.POS_PRODUCTS.length ? window.POS_PRODUCTS : [];
  const grid = $('posGrid');
  if (!grid) return;
  if (!source.length) {
    grid.innerHTML = '<p style="color:var(--text3);padding:.75rem">No products yet. Add products in Inventory first.</p>';
    return;
  }
  grid.innerHTML = source.map(p => `
    <div class="pos-tile" onclick="posAddItem(${p.id})">
      <div class="pos-tile-img">${p.image_url ? `<img src="${p.image_url}" alt="${p.name}" onerror="this.style.opacity=0">` : ''}</div>
      <p class="pos-tile-name">${p.name}</p>
      <p class="pos-tile-price">${fmt(p.price || 0)}</p>
    </div>`).join('');
}

let posItems = [];
let posPaymentMethod = 'cash';
let posManualDiscount = 0;
let posVoucherCode = '';
function posAddItem(id) {
  const source = Array.isArray(window.POS_PRODUCTS) ? window.POS_PRODUCTS : [];
  const p = source.find(x => x.id === id);
  if (!p) return;
  const ex = posItems.find(i => i.id === id);
  if (ex) ex.qty++;
  else posItems.push({ ...p, qty: 1 });
  renderPOSReceipt();
  showToast(`${p.name} added`);
}
function posChangeQty(id, d) {
  const item = posItems.find(i => i.id === id);
  if (item) { item.qty += d; if (item.qty <= 0) posItems = posItems.filter(i => i.id !== id); }
  renderPOSReceipt();
}
function posSetQty(id, value) {
  const item = posItems.find(i => i.id === id);
  if (!item) return;
  const qty = parseInt(value, 10);
  if (Number.isNaN(qty) || qty <= 0) {
    posItems = posItems.filter(i => i.id !== id);
  } else {
    item.qty = qty;
  }
  renderPOSReceipt();
}
async function applyPosVoucher() {
  const codeInput = $('posVoucherCodeInput');
  const code = (codeInput && codeInput.value ? codeInput.value : '').trim().toUpperCase();
  if (!code) {
    posVoucherCode = '';
    showToast('Voucher cleared', 'ok');
    renderPOSReceipt();
    return;
  }
  const subtotal = posItems.reduce((s, i) => s + i.price * i.qty, 0);
  const res = await fetch('/cart/voucher/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, subtotal, delivery_fee: 0 })
  });
  const data = await res.json();
  if (!res.ok || !data.valid) {
    showToast(data.error || 'Invalid voucher', 'err');
    return;
  }
  posVoucherCode = code;
  showToast('Voucher applied', 'ok');
  renderPOSReceipt();
}

function posSummary() {
  const subtotal = posItems.reduce((s, i) => s + i.price * i.qty, 0);
  let voucherDiscount = 0;
  if (posVoucherCode) {
    // UI estimate only; backend remains source of truth.
    voucherDiscount = 0;
  }
  const discount = Math.max(0, Number(posManualDiscount || 0)) + voucherDiscount;
  const finalTotal = Math.max(0, subtotal - discount);
  const paidInput = $('posAmountPaidInput');
  if (paidInput && paidInput.value !== posAmountPaid) posAmountPaid = paidInput.value;
  const amountPaid = parseFloat(posAmountPaid || 0) || 0;
  const change = Math.max(0, amountPaid - finalTotal);
  return { subtotal, discount, finalTotal, amountPaid, change };
}

function renderPOSReceipt() {
  const receipt = $('posReceipt');
  if (!receipt) return;
  const summary = posSummary();
  const itemsHTML = posItems.length === 0
    ? '<p style="color:var(--text3);font-size:.8rem;text-align:center;padding:1rem">No items added</p>'
    : posItems.map(i => `<div class="pos-item-row">
        <span class="pos-item-nm">${i.name}</span>
        <div class="pos-item-ctrl">
          <button onclick="posChangeQty(${i.id},-1)">−</button>
          <input
            type="number"
            min="1"
            step="1"
            inputmode="numeric"
            value="${i.qty}"
            style="width:58px;text-align:center;background:var(--bg3);border:1px solid var(--border);color:var(--text);font-family:'DM Mono',monospace;font-size:.75rem;padding:.2rem .3rem;border-radius:2px"
            onchange="posSetQty(${i.id}, this.value)"
          >
          <button onclick="posChangeQty(${i.id},1)">+</button>
        </div>
        <span class="pos-item-price">${fmt(i.price * i.qty)}</span>
      </div>`).join('');
  receipt.innerHTML = `
    <p class="pos-receipt-title">Current Order</p>
    <div style="min-height:120px">${itemsHTML}</div>
    <div class="pos-tot-row"><span>Subtotal</span><span>${fmt(summary.subtotal)}</span></div>
    <div class="pos-tot-row"><span>Discount</span><span>${fmt(summary.discount)}</span></div>
    <div class="pos-tot-row"><span>Final Total</span><span>${fmt(summary.finalTotal)}</span></div>
    <div style="display:flex;gap:.5rem;margin-top:.65rem">
      <input id="posDiscountInput" class="admin-input" type="number" min="0" step="0.01" placeholder="Manual discount (₱)" value="${posManualDiscount || ''}" oninput="posManualDiscount=parseFloat(this.value||0);renderPOSReceipt()">
      <input id="posVoucherCodeInput" class="admin-input" type="text" placeholder="Voucher code" value="${posVoucherCode || ''}">
      <button class="btn btn-g btn-sm" onclick="applyPosVoucher()">Apply</button>
    </div>
    <div style="display:flex;gap:.5rem;margin-top:.65rem;align-items:center">
      <input id="posAmountPaidInput" class="admin-input" type="number" min="0" step="0.01" placeholder="Amount paid (₱)" value="${posAmountPaid || ''}" oninput="posAmountPaid=this.value;updatePosChangeOnly()">
      <div style="font-size:.75rem;color:var(--text2);min-width:120px">Change: <strong id="posChangeValue" style="color:var(--accent)">${fmt(summary.change)}</strong></div>
    </div>
    <div style="display:flex;gap:.5rem;margin-top:.85rem">
      <button class="btn btn-p" style="flex:1;justify-content:center;padding:.75rem" onclick="processSale()">Process Sale</button>
      <button class="btn btn-g btn-sm" onclick="posItems=[];renderPOSReceipt()">Clear</button>
    </div>
    <div style="margin-top:.85rem;display:flex;gap:.5rem">
      <button class="btn btn-g btn-sm" style="flex:1;justify-content:center;${posPaymentMethod === 'gcash' ? 'border-color:var(--accent);color:var(--accent);' : ''}" onclick="setPosPayment('gcash')">GCash</button>
      <button class="btn btn-g btn-sm" style="flex:1;justify-content:center;${posPaymentMethod === 'card' ? 'border-color:var(--accent);color:var(--accent);' : ''}" onclick="setPosPayment('card')">Card</button>
      <button class="btn btn-g btn-sm" style="flex:1;justify-content:center;${posPaymentMethod === 'cash' ? 'border-color:var(--accent);color:var(--accent);' : ''}" onclick="setPosPayment('cash')">Cash</button>
    </div>`;
}
function updatePosChangeOnly() {
  const summary = posSummary();
  const el = $('posChangeValue');
  if (el) el.textContent = fmt(summary.change);
}
function setPosPayment(method) {
  posPaymentMethod = method;
  renderPOSReceipt();
}
async function processSale() {
  if (posItems.length === 0) {
    await showAppModal({
      title: 'Current Order Empty',
      message: 'Add at least one item before processing a sale.',
      confirmText: 'Got It',
      variant: 'alert'
    });
    return;
  }
  const method = posPaymentMethod === 'card' ? 'cash' : posPaymentMethod;
  const summary = posSummary();
  if (summary.amountPaid < summary.finalTotal) {
    await showAppModal({
      title: 'Insufficient Payment',
      message: 'Amount paid must be equal to or higher than the final total.',
      confirmText: 'OK',
      variant: 'alert'
    });
    return;
  }
  const payload = {
    items: posItems.map(i => ({ product_id: i.id, quantity: i.qty, price: i.price })),
    payment_method: method,
    discount_type: posVoucherCode ? 'voucher' : 'none',
    voucher_code: posVoucherCode,
    manual_discount_amount: posManualDiscount || 0,
    amount_paid: summary.amountPaid
  };
  const res = await fetch('/admin/sales/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  const data = await res.json();
  if (!res.ok || !data.success) { showToast(data.error || 'Failed to process sale', 'err'); return; }
  showToast(`Sale processed (${fmt(data.final_total || summary.finalTotal)})`, 'ok');
  if (data.sale_id) window.open(`/admin/receipt/${data.sale_id}`, '_blank');
  posItems = [];
  posManualDiscount = 0;
  posVoucherCode = '';
  posAmountPaid = '';
  renderPOSReceipt();
  setTimeout(() => window.location.reload(), 500);
}

function renderAdminVouchers() {
  const vouchers = Array.isArray(window.ADMIN_VOUCHERS) ? window.ADMIN_VOUCHERS : [];
  const tbl = $('voucherTable');
  if (!tbl) return;
  tbl.innerHTML = vouchers.map(v => `<tr>
    <td><span class="vchr-code" style="font-size:.85rem;padding:.4rem 1rem" onclick="copyCode('${v.code}')">${v.code}</span></td>
    <td>${formatVoucherType(v.voucher_type)}</td>
    <td style="font-family:'DM Mono',monospace">${v.uses || 0}/${v.max_uses || 0}</td>
    <td>${v.end_at ? new Date(v.end_at).toLocaleDateString() : 'No Expiry'}</td>
    <td><span class="vchr-chip ${v.is_active ? 'vc-act' : 'vc-exp'}">${v.is_active ? 'active' : 'inactive'}</span></td>
    <td style="text-align:right">${actionMenuHTML(`voucher-menu-${v.id}`, [
      { label: v.is_active ? 'Disable Voucher' : 'Enable Voucher', onClick: `toggleVoucherActive(${v.id}, ${!v.is_active})` }
    ])}</td>
  </tr>`).join('');
  const form = $('voucherCreateForm');
  if (form && !form.dataset.bound) {
    form.dataset.bound = '1';
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      const payload = {
        code: $('voucherCodeInput').value.trim().toUpperCase(),
        voucher_type: $('voucherTypeInput').value,
        discount_value: parseFloat($('voucherDiscountInput').value || 0),
        max_uses: parseInt($('voucherMaxUsesInput').value || 1, 10),
        min_purchase: parseFloat($('voucherMinPurchaseInput').value || 0),
        end_at: $('voucherEndAtInput') ? $('voucherEndAtInput').value : ''
      };
      const res = await fetch('/admin/vouchers/create', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok || !data.success) { showToast(data.error || 'Failed to create voucher', 'err'); return; }
      showToast('Voucher created', 'ok');
      if (data.voucher) {
        window.ADMIN_VOUCHERS = [data.voucher, ...window.ADMIN_VOUCHERS];
        renderAdminVouchers();
      } else {
        window.location.reload();
      }
      form.reset();
      closeVoucherModal();
    });
  }
}
function openVoucherModal() {
  const overlay = $('voucherCreateOverlay');
  const form = $('voucherCreateForm');
  if (form) form.reset();
  if (overlay) overlay.classList.add('open');
}
function closeVoucherModal() {
  const overlay = $('voucherCreateOverlay');
  if (overlay) overlay.classList.remove('open');
}

function copyCode(code) { navigator.clipboard.writeText(code).then(() => showToast(`Code "${code}" copied!`, 'ok')); }
async function toggleVoucherActive(id, isActive) {
  const res = await fetch(`/admin/vouchers/${id}/update`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ is_active: isActive }) });
  const data = await res.json();
  if (!res.ok || !data.success) { showToast(data.error || 'Failed to update voucher', 'err'); return; }
  window.ADMIN_VOUCHERS = (window.ADMIN_VOUCHERS || []).map((v) => v.id === id ? { ...v, is_active: !!isActive } : v);
  renderAdminVouchers();
  showToast('Voucher updated', 'ok');
}

/* ── PROFILE ── */
function renderProfileOrders() {
  const tbl = $('profileOrders');
  if (!tbl) return;
  const orders = Array.isArray(window.PROFILE_ORDERS) ? window.PROFILE_ORDERS : [];
  if (!orders.length) {
    tbl.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text3)">No orders yet.</td></tr>';
    return;
  }
  tbl.innerHTML = orders.map((o) => {
    const status = statusMeta(o.status);
    const itemNames = (o.items_data || []).map((i) => i.product_name || 'Item').join(', ') || '—';
    return `<tr>
      <td style="font-family:'DM Mono',monospace">#${o.id}</td>
      <td>${o.created_at_display || ''}</td>
      <td style="color:var(--text2)">${itemNames}</td>
      <td style="font-family:'DM Mono',monospace;color:var(--accent)">${fmt(o.total_amount || 0)}</td>
      <td><span class="o-status ${status.cls}">${status.label}</span></td>
      <td><button class="tbl-btn" onclick="showToast('Order #${o.id} loaded', 'ok')">View</button></td>
    </tr>`;
  }).join('');
}

function renderWishlistPage() {
  const grid = $('wishlistGrid');
  if (!grid) return;
  const items = window.IS_AUTHENTICATED
    ? (Array.isArray(window.PROFILE_WISHLIST) ? window.PROFILE_WISHLIST : [])
    : PRODUCTS.filter(p => wishlist.has(p.id));
  if (items.length === 0) {
    grid.innerHTML = '<p style="color:var(--text3);font-size:.85rem">Nothing saved yet. Browse the collection!</p>';
    return;
  }
  grid.innerHTML = items.map((p,i) => cardHTML(p, i * 0.06)).join('');
  setTimeout(observeReveals, 60);
}

function showProfileSection(name, btn) {
  document.querySelectorAll('.profile-section').forEach(s => s.style.display = 'none');
  const sec = $(name);
  if (sec) sec.style.display = 'block';
  document.querySelectorAll('.profile-nav li a').forEach(a => a.classList.remove('active'));
  btn && btn.classList.add('active');
  if (name === 'wishSection') renderWishlistPage();
}

/* ── THEME ── */
function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
  const btn = $('themeToggle');
  if (btn) btn.textContent = isDark ? '☾ Dark' : '☀ Light';
  localStorage.setItem('looph_theme', isDark ? 'light' : 'dark');
}

/* ── NAV SCROLL ── */
window.addEventListener('scroll', () => {
  $('main-nav') && $('main-nav').classList.toggle('scrolled', scrollY > 30);
}, { passive: true });

/* ── MOBILE MENU ── */
function toggleMenu() {
  const d = $('mobileDrawer'), h = $('hamburger');
  d && d.classList.toggle('open');
  h && h.classList.toggle('open');
  document.body.style.overflow = (d && d.classList.contains('open')) ? 'hidden' : '';
}

/* ── TOAST ── */
function showToast(msg, type = '') {
  const wrap = $('toastWrap');
  if (!wrap) return;
  const t = document.createElement('div');
  t.className = 'toast';
  t.innerHTML = `<span class="t-dot ${type}"></span>${msg}`;
  wrap.appendChild(t);
  setTimeout(() => t.classList.add('show'), 10);
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 3000);
}

function showAppModal({ title = 'Notice', message = '', confirmText = 'OK', cancelText = 'Cancel', variant = 'alert' }) {
  const overlay = $('appModalOverlay');
  const titleEl = $('appModalTitle');
  const msgEl = $('appModalMessage');
  const cancelBtn = $('appModalCancelBtn');
  const confirmBtn = $('appModalConfirmBtn');
  if (!overlay || !titleEl || !msgEl || !confirmBtn || !cancelBtn) {
    return Promise.resolve(variant === 'alert');
  }
  return new Promise((resolve) => {
    let closed = false;
    const done = (result) => {
      if (closed) return;
      closed = true;
      overlay.classList.remove('open');
      overlay.removeEventListener('click', onOverlayClick);
      confirmBtn.removeEventListener('click', onConfirm);
      cancelBtn.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onEsc);
      resolve(result);
    };
    const onConfirm = () => done(true);
    const onCancel = () => done(false);
    const onOverlayClick = (e) => { if (e.target === overlay) done(false); };
    const onEsc = (e) => { if (e.key === 'Escape') done(false); };

    titleEl.textContent = title;
    msgEl.textContent = message;
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;
    cancelBtn.style.display = variant === 'confirm' ? 'inline-flex' : 'none';
    overlay.classList.add('open');
    confirmBtn.focus();

    overlay.addEventListener('click', onOverlayClick);
    confirmBtn.addEventListener('click', onConfirm);
    cancelBtn.addEventListener('click', onCancel);
    document.addEventListener('keydown', onEsc);
  });
}

/* ── CURSOR ── */
function initCursor() {
  const cur = $('cursor'), ring = $('cursorRing');
  if (!cur || !ring) return;
  let mx = 0, my = 0, rx = 0, ry = 0;
  document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; cur.style.left = mx + 'px'; cur.style.top = my + 'px'; }, { passive: true });
  (function animRing() { rx += (mx-rx)*.12; ry += (my-ry)*.12; ring.style.left = rx+'px'; ring.style.top = ry+'px'; requestAnimationFrame(animRing); })();
  document.addEventListener('mouseover', e => {
    if (e.target.matches('button,a,[onclick],[data-id]')) { cur.classList.add('grow'); ring.classList.add('grow'); }
    else { cur.classList.remove('grow'); ring.classList.remove('grow'); }
  });
}

/* ── REVEAL ANIMATIONS ── */
function observeReveals() {
  const els = document.querySelectorAll('.reveal:not(.in),.reveal-l:not(.in),.reveal-r:not(.in)');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); obs.unobserve(e.target); } });
  }, { threshold: 0.1 });
  els.forEach(el => obs.observe(el));
}

/* ── HERO UNDERLINE ── */
function initHeroUnderline() {
  const el = document.querySelector('.ua');
  if (el) setTimeout(() => el.classList.add('in'), 700);
}

/* ── KEYBOARD ── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeQV();
    if ($('searchOverlay').classList.contains('open')) toggleSearch();
  }
});


/* ── CAROUSEL (stub - full impl in landing.html) ── */
function initCarousel() {
  if (typeof window._initCarousel === 'function') window._initCarousel();
}

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('looph_theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    const btn = $('themeToggle');
    if (btn) btn.textContent = saved === 'light' ? '☾ Dark' : '☀ Light';
  }
  initCursor();
  updateCartUI();
  renderSearchResults(PRODUCTS.slice(0, 6));
  renderHomeProducts();
  setTimeout(() => { observeReveals(); initHeroUnderline(); }, 200);

  // QV overlay close on backdrop click
  $('qvOverlay') && $('qvOverlay').addEventListener('click', e => { if (e.target === $('qvOverlay')) closeQV(); });
  $('dashboardMetricOverlay') && $('dashboardMetricOverlay').addEventListener('click', e => {
    if (e.target === $('dashboardMetricOverlay')) closeDashboardMetricModal();
  });
  $('voucherCreateOverlay') && $('voucherCreateOverlay').addEventListener('click', e => {
    if (e.target === $('voucherCreateOverlay')) closeVoucherModal();
  });
  document.addEventListener('click', () => closeAllActionMenus());
  initProfileRealtime();
});

async function syncProfileOrders() {
  const profilePage = $('page-profile');
  if (!profilePage || !profilePage.classList.contains('active')) return;
  try {
    const res = await fetch('/profile/orders/data');
    const data = await res.json();
    if (!res.ok || !data.success) return;
    const oldMap = new Map((window.PROFILE_ORDERS || []).map(o => [o.id, String(o.status || '').toLowerCase()]));
    window.PROFILE_ORDERS = data.orders || [];
    renderProfileOrders();
    (window.PROFILE_ORDERS || []).forEach((order) => {
      const prev = oldMap.get(order.id);
      const curr = String(order.status || '').toLowerCase();
      if (prev && prev !== curr) {
        showToast(`Order #${order.id} is now ${curr.replace('_', ' ')}`, 'ok');
      }
      if (!prev && curr === 'processing') {
        showToast(`Payment confirmed for order #${order.id}`, 'ok');
      }
    });
  } catch (_) {}
}

function initProfileRealtime() {
  const profilePage = $('page-profile');
  if (!profilePage || !profilePage.classList.contains('active')) return;
  syncProfileOrders();
  setInterval(() => {
    if (document.visibilityState === 'visible') syncProfileOrders();
  }, 12000);
}

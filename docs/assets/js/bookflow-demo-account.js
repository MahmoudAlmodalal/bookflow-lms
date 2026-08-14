(() => {
  const USER_KEY = "bookflow-demo-user";
  const USERS_KEY = "bookflow-demo-users";
  const GUEST_CART_KEY = "bookflow-demo-cart";

  const parse = (value, fallback) => {
    try { return JSON.parse(value) ?? fallback; } catch { return fallback; }
  };
  const normaliseEmail = value => String(value || "").trim().toLowerCase();
  const normaliseName = value => String(value || "").trim().replace(/\s+/g, " ");
  const getUsers = () => parse(localStorage.getItem(USERS_KEY), []);
  const saveUsers = users => localStorage.setItem(USERS_KEY, JSON.stringify(users));
  const getUser = () => parse(localStorage.getItem(USER_KEY), null);
  const userCartKey = () => {
    const user = getUser();
    return user ? `${GUEST_CART_KEY}:${user.id}` : GUEST_CART_KEY;
  };
  const getCart = () => parse(localStorage.getItem(userCartKey()), []);
  const saveCart = cart => {
    localStorage.setItem(userCartKey(), JSON.stringify([...new Set(cart.map(Number).filter(Number.isInteger))]));
    updateUI();
  };
  const getGuestCart = () => parse(localStorage.getItem(GUEST_CART_KEY), []);
  const mergeGuestCart = () => {
    const user = getUser();
    if (!user) return;
    const guestCart = getGuestCart();
    if (!guestCart.length) return;
    const accountCart = getCart();
    localStorage.setItem(`${GUEST_CART_KEY}:${user.id}`, JSON.stringify([...new Set([...accountCart, ...guestCart])]));
    localStorage.removeItem(GUEST_CART_KEY);
  };
  const renderAuthSlot = slot => {
    const user = getUser();
    slot.innerHTML = user
      ? `<div class="demo-user"><span class="demo-avatar">${escapeHtml(user.name.slice(0, 1).toUpperCase())}</span><div><strong>${escapeHtml(user.name)}</strong><small>حساب محلي نشط</small></div><button type="button" data-demo-logout>تسجيل الخروج</button></div>`
      : `<a href="auth.html" class="demo-auth-link">تسجيل الدخول</a><a href="auth.html?mode=register" class="demo-auth-link demo-auth-primary">إنشاء حساب</a>`;
  };
  const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[char]));
  const updateUI = () => {
    const user = getUser();
    document.querySelectorAll("[data-demo-auth-slot]").forEach(renderAuthSlot);
    document.querySelectorAll("[data-demo-user-name]").forEach(element => {
      element.textContent = user ? user.name : "زائر";
    });
    document.querySelectorAll("[data-demo-cart-count]").forEach(element => {
      element.textContent = getCart().length;
    });
    document.querySelectorAll("[data-demo-authenticated]").forEach(element => {
      element.hidden = !user;
    });
    document.querySelectorAll("[data-demo-guest]").forEach(element => {
      element.hidden = Boolean(user);
    });
    document.querySelectorAll("[data-demo-logout]").forEach(button => {
      button.onclick = () => {
        localStorage.removeItem(USER_KEY);
        updateUI();
        window.location.href = "index.html";
      };
    });
  };
  const register = ({ name, email }) => {
    const cleanName = normaliseName(name);
    const cleanEmail = normaliseEmail(email);
    if (cleanName.length < 2 || !/^\S+@\S+\.\S+$/.test(cleanEmail)) {
      return { ok: false, message: "أدخل اسماً واضحاً وبريداً إلكترونياً بصيغة صحيحة." };
    }
    const users = getUsers();
    if (users.some(user => user.email === cleanEmail)) {
      return { ok: false, message: "يوجد حساب تجريبي بهذا البريد. استخدم تسجيل الدخول بدلاً من ذلك." };
    }
    const user = { id: `u${Date.now()}${Math.random().toString(16).slice(2, 6)}`, name: cleanName, email: cleanEmail };
    saveUsers([...users, user]);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    mergeGuestCart();
    updateUI();
    return { ok: true, user };
  };
  const login = ({ email }) => {
    const cleanEmail = normaliseEmail(email);
    const user = getUsers().find(candidate => candidate.email === cleanEmail);
    if (!user) return { ok: false, message: "لم نجد حساباً تجريبياً بهذا البريد. أنشئ حساباً جديداً أولاً." };
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    mergeGuestCart();
    updateUI();
    return { ok: true, user };
  };

  window.BookFlowDemo = { getUser, getCart, saveCart, register, login, updateUI, escapeHtml };
  document.addEventListener("DOMContentLoaded", updateUI);
})();

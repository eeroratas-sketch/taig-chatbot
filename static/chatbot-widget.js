(function() {
  'use strict';

  // Seadistus
  const SCRIPT_SRC = document.currentScript && document.currentScript.src;
  const AUTO_URL = SCRIPT_SRC ? SCRIPT_SRC.replace(/\/static\/chatbot-widget\.js.*$/, '').replace(/\/widget\.js.*$/, '') : '';
  const API_URL = window.TAIG_CHATBOT_URL || AUTO_URL || 'http://localhost:8100';
  const WIDGET_TITLE = 'Taig Abi';

  // Auto-open seadistus
  const AUTO_OPEN_DELAY = 15000; // 15 sek pärast lehe laadimist
  const BUBBLE_DELAY = 5000;     // 5 sek pärast ilmub teate-mull
  const BUBBLE_DISMISS_TIME = 12000; // Mull kaob 12 sek pärast

  // === BRAUSERI KEELE TUVASTAMINE ===
  function detectVisitorLang() {
    const lang = (navigator.language || navigator.userLanguage || 'et').toLowerCase();
    if (lang.startsWith('ru')) return 'ru';
    if (lang.startsWith('fi')) return 'fi';
    if (lang.startsWith('lv')) return 'lv';
    if (lang.startsWith('lt')) return 'lt';
    if (lang.startsWith('en')) return 'en';
    if (lang.startsWith('et')) return 'et';
    // Muu keel → inglise
    return 'en';
  }

  const VISITOR_LANG = detectVisitorLang();

  // Mitmekeelsed tekstid
  const I18N = {
    et: {
      placeholder: 'Kirjuta siia...',
      subtitle: 'taig.ee müügiassistent • vastab kohe',
      powered: 'Powered by AI ✨',
      homeGreeting: 'Tere tulemast taig.ee poodi! 👋 Kuidas saan teid aidata?',
      homeGreetingReturn: 'Tere tulemast tagasi! 😊 Tore teid jälle näha. Kuidas saan täna aidata?',
      checkoutGreeting: 'Näen, et olete ostmas! 🛒 Kas teadsite, et koodiga TAIG10 saate 10% soodsamalt? Kas saan millegagi aidata?',
      productGreeting: 'Tere! 👋 Kas teil on selle toote kohta küsimusi? Aitan hea meelega!',
      productGreetingReturn: 'Tere tulemast tagasi! 😊 Kas teil on selle toote kohta küsimusi?',
      schoolGreeting: 'Koolitarvete valik on meil lai! 📚 Kas otsite midagi konkreetset – pliiatseid, vihikuid, värve?',
      officeGreeting: 'Kontoritarbed mugavalt kohale! 🏢 Kas otsite midagi konkreetset?',
      exitIntent: 'Ärge lahkuge! 👋 Kasutage koodi <strong>TAIG10</strong> ja saate <strong>10% soodsamalt!</strong>',
    },
    en: {
      placeholder: 'Type here...',
      subtitle: 'taig.ee sales assistant • replies instantly',
      powered: 'Powered by AI ✨',
      homeGreeting: 'Welcome to taig.ee! 👋 We have 5000+ products: school supplies, office supplies, Thule luggage & Case Logic bags. How can I help you?',
      checkoutGreeting: 'Ready to order! 🛒 Use code TAIG10 for 10% off! Need any help?',
      productGreeting: 'Any questions about this product? 🤔 I\'m happy to help!',
      schoolGreeting: 'Looking for school supplies? 📚 We have a great selection!',
      officeGreeting: 'Office supplies delivered to your door! 🏢 What do you need?',
      exitIntent: 'Wait! 👋 Use code <strong>TAIG10</strong> for <strong>10% off</strong> your order!',
    },
    ru: {
      placeholder: 'Напишите здесь...',
      subtitle: 'taig.ee помощник • отвечает сразу',
      powered: 'Powered by AI ✨',
      homeGreeting: 'Добро пожаловать в taig.ee! 👋 У нас 5000+ товаров: школьные принадлежности, канцтовары, чемоданы Thule и сумки Case Logic. Чем могу помочь?',
      checkoutGreeting: 'Оформляете заказ! 🛒 Код TAIG10 даёт скидку 10%! Нужна помощь?',
      productGreeting: 'Есть вопросы по этому товару? 🤔 С радостью помогу!',
      schoolGreeting: 'Ищете школьные принадлежности? 📚 У нас большой выбор!',
      officeGreeting: 'Канцтовары с доставкой! 🏢 Что вам нужно?',
      exitIntent: 'Подождите! 👋 Код <strong>TAIG10</strong> даёт <strong>скидку 10%</strong> на весь заказ!',
    },
    fi: {
      placeholder: 'Kirjoita tähän...',
      subtitle: 'taig.ee myyntiavustaja • vastaa heti',
      powered: 'Powered by AI ✨',
      homeGreeting: 'Tervetuloa taig.ee-kauppaan! 👋 Meillä on yli 5000 tuotetta: koulutarvikkeet, toimistotarvikkeet, Thule-matkalaukut. Miten voin auttaa?',
      checkoutGreeting: 'Olet tekemässä tilausta! 🛒 Koodilla TAIG10 saat 10% alennuksen!',
      productGreeting: 'Onko kysyttävää tästä tuotteesta? 🤔 Autan mielelläni!',
      schoolGreeting: 'Etsitkö koulutarvikkeita? 📚 Meillä on laaja valikoima!',
      officeGreeting: 'Toimistotarvikkeet kotiin! 🏢 Mitä tarvitset?',
      exitIntent: 'Odota! 👋 Käytä koodia <strong>TAIG10</strong> ja saat <strong>10% alennuksen!</strong>',
    },
    lv: {
      placeholder: 'Rakstiet šeit...',
      subtitle: 'taig.ee palīgs • atbild uzreiz',
      powered: 'Powered by AI ✨',
      homeGreeting: 'Laipni lūdzam taig.ee veikalā! 👋 Mums ir 5000+ produktu: skolas piederumi, biroja preces, Thule koferi. Kā varu palīdzēt?',
      checkoutGreeting: 'Gatavojaties pasūtīt! 🛒 Ar kodu TAIG10 saņemiet 10% atlaidi!',
      productGreeting: 'Vai jums ir jautājumi par šo produktu? 🤔 Labprāt palīdzēšu!',
      schoolGreeting: 'Meklējat skolas piederumus? 📚 Mums ir liela izvēle!',
      officeGreeting: 'Biroja preces ar piegādi! 🏢 Ko jūs meklējat?',
      exitIntent: 'Pagaidiet! 👋 Izmantojiet kodu <strong>TAIG10</strong> un saņemiet <strong>10% atlaidi!</strong>',
    },
    lt: {
      placeholder: 'Rašykite čia...',
      subtitle: 'taig.ee padėjėjas • atsako iškart',
      powered: 'Powered by AI ✨',
      homeGreeting: 'Sveiki atvykę į taig.ee! 👋 Turime 5000+ prekių: mokyklinės reikmenys, biuro prekės, Thule lagaminai. Kuo galiu padėti?',
      checkoutGreeting: 'Ruošiatės užsakyti! 🛒 Su kodu TAIG10 gaunate 10% nuolaidą!',
      productGreeting: 'Turite klausimų apie šią prekę? 🤔 Mielai padėsiu!',
      schoolGreeting: 'Ieškote mokyklinių reikmenų? 📚 Turime didelį pasirinkimą!',
      officeGreeting: 'Biuro prekės su pristatymu! 🏢 Ko jums reikia?',
      exitIntent: 'Palaukite! 👋 Naudokite kodą <strong>TAIG10</strong> ir gaukite <strong>10% nuolaidą!</strong>',
    },
  };

  function t(key) {
    return (I18N[VISITOR_LANG] && I18N[VISITOR_LANG][key]) || I18N.en[key] || I18N.et[key];
  }

  const PLACEHOLDER = t('placeholder');

  // Sessioon
  let sessionId = localStorage.getItem('taig_chat_session') || '';
  let isOpen = false;
  let isLoading = false;
  let autoOpenDone = sessionStorage.getItem('taig_auto_opened') === 'true';
  let bubbleDismissed = sessionStorage.getItem('taig_bubble_dismissed') === 'true';

  // === LEHE KONTEKSTI LUGEMINE (DOM) ===
  function readPageContext() {
    const path = window.location.pathname.toLowerCase();
    const context = {
      url: window.location.href,
      page_type: 'other',
    };

    // Toote leht
    const productMain = document.querySelector('.product-info-main');
    if (productMain || path.match(/\.html$/)) {
      context.page_type = 'product';
      const nameEl = document.querySelector('.product-info-main .page-title, .page-title-wrapper .page-title');
      if (nameEl) context.product_name = nameEl.textContent.trim();
      const skuEl = document.querySelector('.product.attribute.sku .value, [itemprop="sku"]');
      if (skuEl) context.product_sku = skuEl.textContent.trim();
      const priceEl = document.querySelector('.price-wrapper .price, [data-price-type="finalPrice"] .price');
      if (priceEl) context.product_price = priceEl.textContent.trim();
      const imgEl = document.querySelector('.gallery-placeholder img, .product-image-photo');
      if (imgEl) context.product_image = imgEl.src;
    }

    // Kategooria leht
    if (!productMain && document.querySelector('.catalog-category-view, .page-products')) {
      context.page_type = 'category';
      const catEl = document.querySelector('.page-title');
      if (catEl) context.category_name = catEl.textContent.trim();
    }

    // Ostukorv / kassaleht
    if (path.includes('/checkout') || path.includes('/cart')) {
      context.page_type = path.includes('/checkout') ? 'checkout' : 'cart';
      try {
        const mageCache = localStorage.getItem('mage-cache-storage');
        if (mageCache) {
          const parsed = JSON.parse(mageCache);
          if (parsed && parsed.cart && parsed.cart.items) {
            context.cart_items = parsed.cart.items.map(function(item) {
              return {
                name: item.product_name,
                qty: item.qty,
                price: item.product_price,
              };
            });
            context.cart_total = parsed.cart.subtotalAmount;
          }
        }
      } catch (e) { /* ignore */ }
    }

    return context;
  }

  // === TAGASITULEVA KLIENDI TUVASTUS ===
  function isReturningVisitor() {
    var visited = localStorage.getItem('taig_visited');
    if (visited) {
      return true;
    }
    localStorage.setItem('taig_visited', new Date().toISOString());
    return false;
  }
  var returningVisitor = isReturningVisitor();

  // Külastuste loendur (püsikliendi tuvastamiseks)
  var visitCount = parseInt(localStorage.getItem('taig_visit_count') || '0') + 1;
  localStorage.setItem('taig_visit_count', visitCount.toString());

  // === SIRVIMISAJALOO SALVESTAMINE ===
  function saveViewedProduct() {
    var pc = readPageContext();
    if (pc.product_name) {
      try {
        var history = JSON.parse(localStorage.getItem('taig_viewed') || '[]');
        // Ära lisa duplikaate
        if (history.length === 0 || history[0].name !== pc.product_name) {
          history.unshift({
            name: pc.product_name,
            price: pc.product_price || '',
            url: window.location.href,
            time: new Date().toISOString()
          });
          // Hoia ainult viimased 10
          if (history.length > 10) history = history.slice(0, 10);
          localStorage.setItem('taig_viewed', JSON.stringify(history));
        }
      } catch(e) {}
    }
  }
  saveViewedProduct();

  function getViewedProducts() {
    try {
      return JSON.parse(localStorage.getItem('taig_viewed') || '[]');
    } catch(e) { return []; }
  }

  // === TASUTA TARNE PROGRESSIRIBA ===
  function getCartTotal() {
    try {
      var mageCache = localStorage.getItem('mage-cache-storage');
      if (mageCache) {
        var parsed = JSON.parse(mageCache);
        if (parsed && parsed.cart) {
          return parseFloat(parsed.cart.subtotalAmount || 0);
        }
      }
    } catch(e) {}
    return 0;
  }

  function renderShippingBar() {
    var FREE_SHIPPING = 50;
    var total = getCartTotal();
    if (total <= 0) return null;

    var pct = Math.min(100, Math.round(total / FREE_SHIPPING * 100));
    var remaining = Math.max(0, FREE_SHIPPING - total).toFixed(2);
    var isComplete = total >= FREE_SHIPPING;

    var bar = document.createElement('div');
    bar.className = 'taig-shipping-bar' + (isComplete ? ' complete' : '');

    if (isComplete) {
      bar.innerHTML = '<div class="bar-text"><span>🎉 TASUTA tarne!</span><span>' + total.toFixed(2) + '€</span></div>' +
        '<div class="bar-track"><div class="bar-fill" style="width:100%"></div></div>';
    } else {
      bar.innerHTML = '<div class="bar-text"><span>🚚 Veel <strong>' + remaining + '€</strong> tasuta tarneni!</span><span>' + total.toFixed(2) + '€ / ' + FREE_SHIPPING + '€</span></div>' +
        '<div class="bar-track"><div class="bar-fill" style="width:' + pct + '%"></div></div>';
    }
    return bar;
  }

  function greetingKey(base) {
    if (returningVisitor) {
      var returnKey = base + 'Return';
      // Kasuta tagasituleva kliendi tervitust kui see on tõlgitud, muidu tavalist
      var val = (I18N[VISITOR_LANG] && I18N[VISITOR_LANG][returnKey]) || I18N.et[returnKey];
      if (val) return returnKey;
    }
    return base;
  }

  // === KONTEKSTITUVASTUS (greetings) ===
  function detectPageContext() {
    const path = window.location.pathname.toLowerCase();
    const title = document.title.toLowerCase();

    // Avaleht - kontrolli ESIMESENA (path on / või /et/ vms)
    var isHomePage = path === '/' || path.match(/^\/[a-z]{2}\/?$/);
    if (isHomePage) {
      return { type: 'home', greeting: t(greetingKey('homeGreeting')) };
    }

    if (path.includes('/checkout') || path.includes('/cart')) {
      return { type: 'checkout', greeting: t('checkoutGreeting') };
    }
    // Toote leht - kontrolli ENNE brändi/kategooria tuvastust!
    if (path.match(/\.html$/) || document.querySelector('.product-info-main')) {
      return { type: 'product', greeting: t(greetingKey('productGreeting')) };
    }
    // Brändi/kategooria lehed (ainult kui POLE toote leht)
    if (path.includes('thule') || title.includes('thule')) {
      return { type: 'thule', greeting: t(greetingKey('homeGreeting')) };
    }
    if (path.includes('case-logic') || title.includes('case logic')) {
      return { type: 'caselogic', greeting: t(greetingKey('homeGreeting')) };
    }
    if (path.includes('kooli') || path.includes('school')) {
      return { type: 'school', greeting: t(greetingKey('homeGreeting')) };
    }
    if (path.includes('kontori') || path.includes('office')) {
      return { type: 'office', greeting: t(greetingKey('homeGreeting')) };
    }
    if (path.includes('kirjutus') || title.includes('kirjutus') || title.includes('pliiats') || title.includes('pastakas')) {
      return { type: 'writing', greeting: t(greetingKey('homeGreeting')) };
    }
    // Üldine
    return { type: 'home', greeting: t(greetingKey('homeGreeting')) };
  }

  // === QUICK-ACTION NUPUD (mitmekeelne) ===
  const QUICK_ACTIONS_I18N = {
    et: {
      home: [
        { label: '🔍 Otsin toodet', query: 'Aita mul leida sobiv toode' },
        { label: '🧳 Thule tooted', query: 'Näita Thule kohvreid ja kotte' },
        { label: '💼 Arvutikotid', query: 'Näita arvutikotte ja seljakotte' },
        { label: '🏷️ Soodustused', query: 'Mis soodustused teil praegu on?' },
      ],
      school: [
        { label: '✏️ Pliiatsid', query: 'Näita pliiatseid ja pastakaid kooli' },
        { label: '🎨 Värvid', query: 'Näita guašše ja akvarellvärve' },
        { label: '📓 Vihikud', query: 'Näita vihikuid' },
        { label: '🎒 Kooli stardipakk', query: '__school_wizard__' },
        { label: '🏷️ TAIG10 -10%', query: 'Kuidas saan allahindlust?' },
      ],
      checkout: [
        { label: '🏷️ Kasuta TAIG10', query: 'Kuidas kasutada kupongikoodi?' },
        { label: '🚚 Tarne info', query: 'Mis on tarnevõimalused ja hinnad?' },
        { label: '💳 Makse info', query: 'Mis makseviisid on?' },
      ],
      product: [
        { label: '📏 Mõõdud?', query: 'Mis on selle toote mõõdud?' },
        { label: '📦 Saadavus?', query: 'Kas see toode on laos?' },
        { label: '🏷️ Allahindlus?', query: 'Kas saan allahindlust?' },
        { label: '🔄 Alternatiivid', query: 'Mis alternatiive on sellele tootele?' },
      ],
    },
    en: {
      home: [
        { label: '🔍 Find product', query: 'Help me find a product' },
        { label: '🧳 Thule luggage', query: 'Show Thule suitcases and bags' },
        { label: '💼 Laptop bags', query: 'Show laptop bags and backpacks' },
        { label: '🏷️ Discounts', query: 'What discounts are available?' },
      ],
      product: [
        { label: '📏 Dimensions?', query: 'What are the dimensions of this product?' },
        { label: '📦 In stock?', query: 'Is this product in stock?' },
        { label: '🏷️ Discount?', query: 'How to get a discount?' },
        { label: '🔄 Alternatives', query: 'What alternatives do you have?' },
      ],
    },
    ru: {
      home: [
        { label: '📚 Школьные', query: 'Покажите школьные принадлежности' },
        { label: '✏️ Ручки', query: 'Какие ручки и карандаши у вас есть?' },
        { label: '🧳 Thule', query: 'Покажите чемоданы и сумки Thule' },
        { label: '🏷️ Скидки', query: 'Какие скидки сейчас есть?' },
      ],
      product: [
        { label: '📏 Размеры?', query: 'Какие размеры у этого товара?' },
        { label: '🔄 Аналоги', query: 'Какие есть аналоги?' },
        { label: '🏷️ TAIG10 -10%', query: 'Как получить скидку?' },
      ],
    },
    fi: {
      home: [
        { label: '📚 Koulutarvikkeet', query: 'Näytä suosittuja koulutarvikkeita' },
        { label: '✏️ Kynät', query: 'Mitä kyniä teillä on?' },
        { label: '🧳 Thule', query: 'Näytä Thule-matkalaukut' },
        { label: '🏷️ Alennukset', query: 'Mitä alennuksia on?' },
      ],
    },
    lv: {
      home: [
        { label: '📚 Skolas preces', query: 'Parādiet skolas piederumus' },
        { label: '✏️ Pildspalvas', query: 'Kādas pildspalvas jums ir?' },
        { label: '🧳 Thule', query: 'Parādiet Thule koferi un somas' },
        { label: '🏷️ Atlaides', query: 'Kādas atlaides ir pieejamas?' },
      ],
    },
    lt: {
      home: [
        { label: '📚 Mokyklinės', query: 'Parodykite mokyklinius reikmenis' },
        { label: '✏️ Rašikliai', query: 'Kokius rašiklius turite?' },
        { label: '🧳 Thule', query: 'Parodykite Thule lagaminus' },
        { label: '🏷️ Nuolaidos', query: 'Kokios nuolaidos galimos?' },
      ],
    },
  };

  function getQuickActions(pageType) {
    const langActions = QUICK_ACTIONS_I18N[VISITOR_LANG] || QUICK_ACTIONS_I18N.en;
    // Proovi leida täpne lehetüüp, muidu kasuta home
    return langActions[pageType] || langActions.home || QUICK_ACTIONS_I18N.et[pageType] || QUICK_ACTIONS_I18N.et.home;
  }

  // === STIILID ===
  const styles = `
    #taig-chat-btn {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #2563eb, #1e40af);
      color: white;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(37,99,235,0.4);
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.3s, box-shadow 0.3s;
      font-size: 28px;
      animation: taig-pulse 3s infinite;
    }
    #taig-chat-btn:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 25px rgba(37,99,235,0.6);
      animation: none;
    }
    #taig-chat-btn.no-pulse { animation: none; }
    @keyframes taig-pulse {
      0%, 100% { box-shadow: 0 4px 15px rgba(37,99,235,0.4); }
      50% { box-shadow: 0 4px 25px rgba(37,99,235,0.7); }
    }
    #taig-chat-btn.has-dot::after {
      content: '';
      position: absolute;
      top: 2px;
      right: 2px;
      width: 16px;
      height: 16px;
      background: #ef4444;
      border-radius: 50%;
      border: 2px solid white;
      animation: taig-dot-pulse 2s infinite;
    }
    @keyframes taig-dot-pulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.2); }
    }

    /* Teate-mull (bubble) */
    #taig-chat-bubble {
      position: fixed;
      bottom: 88px;
      right: 20px;
      background: white;
      color: #1e293b;
      padding: 12px 16px;
      border-radius: 16px 16px 4px 16px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      z-index: 99998;
      max-width: 260px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      line-height: 1.4;
      cursor: pointer;
      display: none;
      animation: taig-bubble-in 0.4s ease-out;
    }
    #taig-chat-bubble.show { display: block; }
    #taig-chat-bubble:hover { background: #f8fafc; }
    #taig-chat-bubble .bubble-close {
      position: absolute;
      top: -8px;
      right: -8px;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: #64748b;
      color: white;
      border: 2px solid white;
      cursor: pointer;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    @keyframes taig-bubble-in {
      from { opacity: 0; transform: translateY(10px) scale(0.9); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    #taig-chat-window {
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 380px;
      height: 560px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.18);
      z-index: 99998;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      animation: taig-window-in 0.3s ease-out;
    }
    @keyframes taig-window-in {
      from { opacity: 0; transform: translateY(20px) scale(0.95); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    #taig-chat-window.open { display: flex; }

    .taig-chat-header {
      background: linear-gradient(135deg, #2563eb, #1e40af);
      color: white;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    .taig-chat-header h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
    .taig-chat-header .subtitle {
      font-size: 12px;
      opacity: 0.8;
      margin-top: 2px;
    }
    .taig-chat-header .online-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      background: #4ade80;
      border-radius: 50%;
      margin-right: 6px;
      animation: taig-online 2s infinite;
    }
    @keyframes taig-online {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    .taig-chat-close {
      background: none;
      border: none;
      color: white;
      font-size: 22px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: 8px;
    }
    .taig-chat-close:hover { background: rgba(255,255,255,0.2); }

    .taig-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    /* Quick action nupud */
    .taig-quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }
    .taig-quick-btn {
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      padding: 6px 14px;
      font-size: 13px;
      cursor: pointer;
      color: #2563eb;
      font-family: inherit;
      transition: all 0.2s;
    }
    .taig-quick-btn:hover {
      background: #2563eb;
      color: white;
      border-color: #2563eb;
    }
    .taig-quick-btn.school-wizard-btn {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: white;
      border-color: transparent;
      font-weight: 600;
    }
    .taig-quick-btn.school-wizard-btn:hover {
      background: linear-gradient(135deg, #d97706, #b45309);
    }

    .taig-msg {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 16px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
    }
    .taig-msg.bot {
      background: #f1f5f9;
      color: #1e293b;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
    }
    .taig-msg.user {
      background: linear-gradient(135deg, #2563eb, #1e40af);
      color: white;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    .taig-msg a {
      color: #2563eb;
      text-decoration: underline;
    }
    .taig-msg.user a { color: #bfdbfe; }
    .taig-msg strong { font-weight: 600; }

    /* Bot sõnumi konteiner (msg + feedback) */
    .taig-bot-msg-wrap {
      align-self: flex-start;
      display: flex;
      flex-direction: column;
      gap: 4px;
      max-width: 90%;
    }

    /* Feedback nupud */
    .taig-feedback {
      display: flex;
      gap: 6px;
      padding-left: 4px;
    }
    .taig-feedback-btn {
      background: none;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 2px 8px;
      font-size: 14px;
      cursor: pointer;
      color: #94a3b8;
      font-family: inherit;
      transition: all 0.2s;
      line-height: 1.4;
    }
    .taig-feedback-btn:hover {
      background: #f1f5f9;
      border-color: #cbd5e1;
      color: #475569;
    }
    .taig-feedback-btn.voted {
      background: #f0fdf4;
      border-color: #86efac;
      color: #16a34a;
      cursor: default;
    }
    .taig-feedback-btn.voted-down {
      background: #fef2f2;
      border-color: #fca5a5;
      color: #dc2626;
    }

    /* Toote kaardid - !important vajalik Magento CSS ülekirjutamise vastu */
    .taig-products-row {
      display: flex !important;
      gap: 10px !important;
      overflow-x: auto !important;
      overflow-y: hidden !important;
      padding: 4px 2px 8px 2px !important;
      align-self: flex-start !important;
      max-width: 100% !important;
      min-height: 180px !important;
      height: auto !important;
      scrollbar-width: thin;
      scrollbar-color: #cbd5e1 transparent;
    }
    .taig-products-row::-webkit-scrollbar {
      height: 4px;
    }
    .taig-products-row::-webkit-scrollbar-track {
      background: transparent;
    }
    .taig-products-row::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 2px;
    }
    .taig-product-card {
      background: white !important;
      border: 1px solid #e2e8f0 !important;
      border-radius: 12px !important;
      padding: 10px !important;
      min-width: 150px !important;
      max-width: 160px !important;
      flex-shrink: 0 !important;
      display: flex !important;
      flex-direction: column !important;
      gap: 6px !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
      transition: box-shadow 0.2s, transform 0.2s !important;
      height: auto !important;
      min-height: 160px !important;
    }
    .taig-product-card:hover {
      box-shadow: 0 4px 16px rgba(37,99,235,0.15) !important;
      transform: translateY(-2px) !important;
    }
    .taig-product-img {
      width: 100% !important;
      height: 80px !important;
      object-fit: contain !important;
      border-radius: 6px !important;
      background: #f8fafc !important;
      display: block !important;
    }
    .taig-product-img-placeholder {
      width: 100% !important;
      height: 80px !important;
      background: #f1f5f9 !important;
      border-radius: 6px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      font-size: 28px !important;
    }
    .taig-product-name {
      font-size: 12px !important;
      font-weight: 600 !important;
      color: #1e293b !important;
      line-height: 1.3 !important;
      display: -webkit-box !important;
      -webkit-line-clamp: 2 !important;
      -webkit-box-orient: vertical !important;
      overflow: hidden !important;
      min-height: 28px !important;
    }
    .taig-product-price {
      font-size: 13px !important;
      font-weight: 700 !important;
      color: #2563eb !important;
    }
    .taig-product-btn {
      display: block !important;
      text-align: center !important;
      background: linear-gradient(135deg, #2563eb, #1e40af) !important;
      color: white !important;
      text-decoration: none !important;
      border-radius: 8px !important;
      padding: 5px 10px !important;
      font-size: 12px !important;
      font-weight: 600 !important;
      transition: opacity 0.2s !important;
      font-family: inherit !important;
    }
    .taig-product-btn:hover {
      opacity: 0.85 !important;
      color: white !important;
      text-decoration: none !important;
    }
    .taig-cart-btn {
      background: linear-gradient(135deg, #16a34a, #15803d) !important;
      border: none !important;
      cursor: pointer !important;
      color: white !important;
    }
    .taig-cart-btn:disabled {
      opacity: 0.6 !important;
      cursor: wait !important;
    }
    .taig-add-all-btn {
      background: linear-gradient(135deg, #16a34a, #15803d);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 8px 16px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
      font-family: inherit;
    }
    .taig-add-all-btn:hover { opacity: 0.85; }
    .taig-add-all-btn:disabled { opacity: 0.6; cursor: wait; }

    /* Low stock badge */
    .taig-low-stock {
      display: inline-block;
      background: #ef4444;
      color: white;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 10px;
      margin-left: 6px;
      vertical-align: middle;
      animation: taig-stock-pulse 2s infinite;
    }
    @keyframes taig-stock-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }

    /* Tasuta tarne progressiriba */
    .taig-shipping-bar {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 8px;
      padding: 8px 12px;
      margin: 8px 0;
      font-size: 12px;
    }
    .taig-shipping-bar .bar-track {
      background: #e5e7eb;
      border-radius: 4px;
      height: 6px;
      margin-top: 4px;
      overflow: hidden;
    }
    .taig-shipping-bar .bar-fill {
      background: linear-gradient(90deg, #22c55e, #16a34a);
      height: 100%;
      border-radius: 4px;
      transition: width 0.5s ease;
    }
    .taig-shipping-bar.complete {
      background: #dcfce7;
      border-color: #86efac;
    }
    .taig-shipping-bar .bar-text {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* Püsikliendi badge */
    .taig-loyalty-msg {
      background: linear-gradient(135deg, #fef3c7, #fde68a);
      border: 1px solid #fbbf24;
      border-radius: 8px;
      padding: 8px 12px;
      margin: 8px 0;
      font-size: 12px;
      text-align: center;
    }

    /* Kooli stardipakk viisard */
    .taig-wizard {
      background: linear-gradient(135deg, #fef3c7, #fde68a);
      border: 1px solid #fbbf24;
      border-radius: 12px;
      padding: 12px;
      align-self: flex-start;
      max-width: 90%;
    }
    .taig-wizard-title {
      font-weight: 700;
      font-size: 14px;
      color: #92400e;
      margin-bottom: 8px;
    }
    .taig-wizard-question {
      font-size: 13px;
      color: #78350f;
      margin-bottom: 8px;
    }
    .taig-wizard-options {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .taig-wizard-opt {
      background: white;
      border: 1px solid #fbbf24;
      border-radius: 16px;
      padding: 5px 12px;
      font-size: 12px;
      cursor: pointer;
      color: #92400e;
      font-family: inherit;
      font-weight: 600;
      transition: all 0.2s;
    }
    .taig-wizard-opt:hover {
      background: #f59e0b;
      color: white;
      border-color: #f59e0b;
    }

    .taig-typing {
      align-self: flex-start;
      padding: 10px 14px;
      background: #f1f5f9;
      border-radius: 16px;
      border-bottom-left-radius: 4px;
      display: none;
    }
    .taig-typing.show { display: block; }
    .taig-typing span {
      display: inline-block;
      width: 8px;
      height: 8px;
      background: #94a3b8;
      border-radius: 50%;
      margin: 0 2px;
      animation: taig-bounce 1.2s infinite;
    }
    .taig-typing span:nth-child(2) { animation-delay: 0.2s; }
    .taig-typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes taig-bounce {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-6px); }
    }

    .taig-chat-input-wrap {
      padding: 12px 16px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      gap: 8px;
      flex-shrink: 0;
    }
    .taig-chat-input {
      flex: 1;
      padding: 10px 14px;
      border: 1px solid #e2e8f0;
      border-radius: 24px;
      font-size: 14px;
      outline: none;
      font-family: inherit;
    }
    .taig-chat-input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
    .taig-chat-send {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, #2563eb, #1e40af);
      color: white;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
      transition: transform 0.2s;
    }
    .taig-chat-send:hover { transform: scale(1.1); }
    .taig-chat-send:disabled { background: #94a3b8; cursor: not-allowed; transform: none; }

    .taig-powered {
      text-align: center;
      padding: 6px;
      font-size: 11px;
      color: #94a3b8;
      flex-shrink: 0;
    }

    @media (max-width: 480px) {
      #taig-chat-window {
        bottom: 0;
        right: 0;
        width: 100%;
        height: 100%;
        border-radius: 0;
      }
      #taig-chat-btn { bottom: 16px; right: 16px; }
      #taig-chat-bubble { bottom: 84px; right: 16px; max-width: 220px; }
      .taig-product-card { min-width: 130px; max-width: 140px; }
    }
  `;

  // === TOOTE KAARTIDE PARSIMINE ===
  // Formaat: [PRODUCT:nimi|hind|pilt_url|toote_url|sku]
  function parseProducts(text) {
    const products = [];
    // Eemaldame reavahetused PRODUCT tagide seest (Claude võib murda pikki URL-e)
    var cleaned = text.replace(/\[PRODUCT:([\s\S]*?)\]/g, function(match, inner) {
      return '[PRODUCT:' + inner.replace(/\n/g, '') + ']';
    });
    const regex = /\[PRODUCT:([^\]]+)\]/g;
    let match;
    while ((match = regex.exec(cleaned)) !== null) {
      const parts = match[1].split('|');
      if (parts.length >= 2) {
        products.push({
          name: (parts[0] || '').trim(),
          price: (parts[1] || '').trim(),
          image: (parts[2] || '').trim(),
          url: (parts[3] || '').trim(),
          sku: (parts[4] || '').trim(),
          raw: match[0],
        });
      }
    }
    return products;
  }

  // === OSTUKORVI LISAMINE (Magento 2) ===
  function addToCart(sku, qty, btnEl) {
    if (!sku) return;
    qty = qty || 1;

    // Näita loading olekut
    var origText = btnEl.textContent;
    btnEl.textContent = '⏳ Lisan...';
    btnEl.disabled = true;

    // Magento form_key
    var formKey = '';
    try {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var c = cookies[i].trim();
        if (c.indexOf('form_key=') === 0) {
          formKey = c.substring('form_key='.length);
        }
      }
      if (!formKey && window.FORM_KEY) formKey = window.FORM_KEY;
      if (!formKey) {
        var fkInput = document.querySelector('input[name="form_key"]');
        if (fkInput) formKey = fkInput.value;
      }
    } catch(e) {}

    // Kasuta Magento customer-data REST API (guest)
    // Kõigepealt otsi toote ID SKU järgi, siis lisa korvi
    var baseUrl = window.location.origin;

    // Variant 1: Kasuta Magento add-to-cart URL-i (lihtsam ja töökindlam)
    fetch(baseUrl + '/rest/V1/products/' + encodeURIComponent(sku), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
    .then(function(resp) { return resp.json(); })
    .then(function(product) {
      var productId = product.id;
      if (!productId) throw new Error('Toote ID ei leitud');

      // Lisa ostukorvi kasutades Magento standard URL
      var formData = new FormData();
      formData.append('product', productId);
      formData.append('qty', qty);
      formData.append('form_key', formKey);

      return fetch(baseUrl + '/checkout/cart/add/product/' + productId + '/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });
    })
    .then(function(resp) {
      if (resp.ok || resp.redirected) {
        btnEl.textContent = '✅ Lisatud!';
        btnEl.style.background = '#16a34a';

        // Näita progressiriba chatbotis
        setTimeout(function() {
          var shippingBar = renderShippingBar();
          if (shippingBar) {
            var messages = document.getElementById('taig-messages');
            if (messages) {
              messages.appendChild(shippingBar);
              messages.scrollTop = messages.scrollHeight;
            }
          }
        }, 1500);

        // Uuenda Magento mini-cart
        try {
          require(['Magento_Customer/js/customer-data'], function(customerData) {
            var sections = ['cart'];
            customerData.invalidate(sections);
            customerData.reload(sections, true);
          });
        } catch(e) {
          // Fallback: reload sections via AJAX
          fetch(baseUrl + '/customer/section/load/?sections=cart&force_new_section_timestamp=true', {
            credentials: 'same-origin'
          }).catch(function(){});
        }

        setTimeout(function() {
          btnEl.textContent = '🛒 Lisa korvi';
          btnEl.style.background = '';
          btnEl.disabled = false;
        }, 2000);
      } else {
        throw new Error('HTTP ' + resp.status);
      }
    })
    .catch(function(err) {
      console.error('Ostukorvi lisamine ebaõnnestus:', err);
      btnEl.textContent = '❌ Viga';
      btnEl.style.background = '#dc2626';
      setTimeout(function() {
        btnEl.textContent = origText;
        btnEl.style.background = '';
        btnEl.disabled = false;
      }, 2000);
    });
  }

  function addMultipleToCart(products, btnEl) {
    var origText = btnEl.textContent;
    btnEl.textContent = '⏳ Lisan ' + products.length + ' toodet...';
    btnEl.disabled = true;
    var added = 0;
    var errors = 0;

    products.forEach(function(p, idx) {
      if (!p.sku) { errors++; return; }
      setTimeout(function() {
        var baseUrl = window.location.origin;
        fetch(baseUrl + '/rest/V1/products/' + encodeURIComponent(p.sku), {
          headers: { 'Content-Type': 'application/json' },
        })
        .then(function(r) { return r.json(); })
        .then(function(product) {
          var formKey = window.FORM_KEY || '';
          try {
            var fkInput = document.querySelector('input[name="form_key"]');
            if (fkInput) formKey = fkInput.value;
          } catch(e) {}
          var fd = new FormData();
          fd.append('product', product.id);
          fd.append('qty', 1);
          fd.append('form_key', formKey);
          return fetch(baseUrl + '/checkout/cart/add/product/' + product.id + '/', {
            method: 'POST', body: fd, credentials: 'same-origin'
          });
        })
        .then(function() { added++; })
        .catch(function() { errors++; })
        .finally(function() {
          if (added + errors >= products.filter(function(x){return x.sku;}).length) {
            btnEl.textContent = '✅ ' + added + ' toodet lisatud!';
            btnEl.style.background = '#16a34a';
            try {
              require(['Magento_Customer/js/customer-data'], function(cd) {
                cd.invalidate(['cart']); cd.reload(['cart'], true);
              });
            } catch(e) {
              fetch(baseUrl + '/customer/section/load/?sections=cart&force_new_section_timestamp=true', {
                credentials: 'same-origin'
              }).catch(function(){});
            }
            setTimeout(function() {
              btnEl.textContent = origText;
              btnEl.style.background = '';
              btnEl.disabled = false;
            }, 3000);
          }
        });
      }, idx * 500); // 500ms vahe iga toote vahel, et mitte üle koormata
    });
  }

  // Eemalda toote tag tekstist (ka mitmerealised)
  function stripProductTags(text) {
    return text.replace(/\[PRODUCT:[\s\S]*?\]/g, '').trim();
  }

  // Parsi [LOW_STOCK:N] tag
  function parseLowStock(text) {
    const match = text.match(/\[LOW_STOCK:(\d+)\]/);
    return match ? parseInt(match[1], 10) : null;
  }

  function stripLowStockTag(text) {
    return text.replace(/\[LOW_STOCK:\d+\]/g, '').trim();
  }

  // Parsi [IMG:url] (lihtne pildi kuvamine teksti sees)
  function parseImgTags(text) {
    return text.replace(/\[IMG:([^\]]+)\]/g, '<img src="$1" style="max-width:100%;border-radius:8px;margin-top:6px;display:block;" alt="Toote pilt">');
  }

  // === TOOTE KAARDI RENDERDAMINE ===
  function renderProductCards(products) {
    const row = document.createElement('div');
    row.className = 'taig-products-row';

    products.forEach(function(p) {
      const card = document.createElement('div');
      card.className = 'taig-product-card';

      // Pilt
      if (p.image) {
        const img = document.createElement('img');
        img.className = 'taig-product-img';
        img.src = p.image;
        img.alt = p.name;
        img.onerror = function() {
          const ph = document.createElement('div');
          ph.className = 'taig-product-img-placeholder';
          ph.textContent = '🛍️';
          img.parentNode.replaceChild(ph, img);
        };
        card.appendChild(img);
      } else {
        const ph = document.createElement('div');
        ph.className = 'taig-product-img-placeholder';
        ph.textContent = '🛍️';
        card.appendChild(ph);
      }

      // Nimi
      const name = document.createElement('div');
      name.className = 'taig-product-name';
      name.textContent = p.name;
      card.appendChild(name);

      // Hind
      if (p.price) {
        const price = document.createElement('div');
        price.className = 'taig-product-price';
        price.textContent = p.price;
        card.appendChild(price);
      }

      // Nupud
      const btnWrap = document.createElement('div');
      btnWrap.style.cssText = 'display:flex; flex-direction:column; gap:4px; margin-top:auto;';

      if (p.url) {
        const viewBtn = document.createElement('a');
        viewBtn.className = 'taig-product-btn';
        viewBtn.href = p.url;
        viewBtn.target = '_blank';
        viewBtn.rel = 'noopener';
        viewBtn.textContent = 'Vaata →';
        btnWrap.appendChild(viewBtn);
      }

      if (p.sku) {
        const cartBtn = document.createElement('button');
        cartBtn.className = 'taig-product-btn taig-cart-btn';
        cartBtn.textContent = '🛒 Lisa korvi';
        cartBtn.setAttribute('data-sku', p.sku);
        cartBtn.onclick = function(e) {
          e.preventDefault();
          addToCart(p.sku, 1, cartBtn);
        };
        btnWrap.appendChild(cartBtn);
      }

      card.appendChild(btnWrap);
      row.appendChild(card);
    });

    // "Lisa kõik korvi" nupp kui rohkem kui 1 toodet
    var productsWithSku = products.filter(function(p) { return p.sku; });
    if (productsWithSku.length > 1) {
      const addAllBtn = document.createElement('button');
      addAllBtn.className = 'taig-add-all-btn';
      addAllBtn.textContent = '🛒 Lisa kõik ' + productsWithSku.length + ' toodet korvi';
      addAllBtn.onclick = function(e) {
        e.preventDefault();
        addMultipleToCart(productsWithSku, addAllBtn);
      };
      const addAllWrap = document.createElement('div');
      addAllWrap.style.cssText = 'width:100%; margin-top:8px; text-align:center;';
      addAllWrap.appendChild(addAllBtn);
      row.appendChild(addAllWrap);
    }

    return row;
  }

  // === FEEDBACK ===
  function addFeedbackButtons(msgId) {
    const wrap = document.createElement('div');
    wrap.className = 'taig-feedback';

    const upBtn = document.createElement('button');
    upBtn.className = 'taig-feedback-btn';
    upBtn.title = 'Kasulik vastus';
    upBtn.textContent = '👍';

    const downBtn = document.createElement('button');
    downBtn.className = 'taig-feedback-btn';
    downBtn.title = 'Vastus ei aidanud';
    downBtn.textContent = '👎';

    function sendFeedback(score) {
      upBtn.disabled = true;
      downBtn.disabled = true;
      upBtn.classList.remove('voted', 'voted-down');
      downBtn.classList.remove('voted', 'voted-down');
      if (score > 0) {
        upBtn.classList.add('voted');
        upBtn.textContent = '👍 Aitäh!';
      } else {
        downBtn.classList.add('voted', 'voted-down');
        downBtn.textContent = '👎 Täname!';
      }

      fetch(API_URL + '/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message_id: msgId,
          score: score,
        }),
      }).catch(function(e) { /* ignore */ });
    }

    upBtn.onclick = function() { sendFeedback(1); };
    downBtn.onclick = function() { sendFeedback(-1); };

    wrap.appendChild(upBtn);
    wrap.appendChild(downBtn);
    return wrap;
  }

  // === HTML ===
  function createWidget() {
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);

    // Chat button
    const btn = document.createElement('button');
    btn.id = 'taig-chat-btn';
    btn.innerHTML = '💬';
    btn.className = 'has-dot';
    btn.title = 'Küsi abi!';
    btn.onclick = toggleChat;
    document.body.appendChild(btn);

    // Teate-mull (proaktiivne)
    const bubble = document.createElement('div');
    bubble.id = 'taig-chat-bubble';
    const ctx = detectPageContext();
    bubble.innerHTML = `
      <div class="bubble-close" onclick="event.stopPropagation(); this.parentElement.classList.remove('show'); sessionStorage.setItem('taig_bubble_dismissed','true');">✕</div>
      ${ctx.greeting}
    `;
    bubble.onclick = function() {
      bubble.classList.remove('show');
      sessionStorage.setItem('taig_bubble_dismissed', 'true');
      if (!isOpen) toggleChat();
    };
    document.body.appendChild(bubble);

    // Chat window
    const win = document.createElement('div');
    win.id = 'taig-chat-window';
    win.innerHTML = `
      <div class="taig-chat-header">
        <div>
          <h3><span class="online-dot"></span>${WIDGET_TITLE}</h3>
          <div class="subtitle">${t('subtitle')}</div>
        </div>
        <button class="taig-chat-close" onclick="document.getElementById('taig-chat-btn').click()">✕</button>
      </div>
      <div class="taig-chat-messages" id="taig-messages"></div>
      <div class="taig-typing" id="taig-typing"><span></span><span></span><span></span></div>
      <div class="taig-chat-input-wrap">
        <input class="taig-chat-input" id="taig-input" type="text" placeholder="${PLACEHOLDER}" autocomplete="off">
        <button class="taig-chat-send" id="taig-send" onclick="window._taigSend()">➤</button>
      </div>
      <div class="taig-powered">${t('powered')}</div>
    `;
    document.body.appendChild(win);

    // Enter key
    document.getElementById('taig-input').addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        window._taigSend();
      }
    });

    // Proaktiivne teate-mull
    if (!bubbleDismissed && !autoOpenDone) {
      setTimeout(function() {
        if (!isOpen && !bubbleDismissed) {
          bubble.classList.add('show');
          // Mull kaob automaatselt
          setTimeout(function() {
            if (bubble.classList.contains('show')) {
              bubble.classList.remove('show');
            }
          }, BUBBLE_DISMISS_TIME);
        }
      }, BUBBLE_DELAY);
    }

    // Exit-intent tuvastus (hiir lahkub aknast ülevalt)
    document.addEventListener('mouseout', function(e) {
      if (e.clientY < 5 && !isOpen && !autoOpenDone && !sessionStorage.getItem('taig_exit_shown')) {
        sessionStorage.setItem('taig_exit_shown', 'true');

        // Kontrolli kas toode on juba soodushinnaga - siis ÄRA paku allahindlust
        var isAlreadyDiscounted = false;
        var oldPriceEl = document.querySelector('.old-price, .price-wrapper .old-price, [data-price-type="oldPrice"]');
        if (oldPriceEl) isAlreadyDiscounted = true;

        var exitMsg = '';
        if (isAlreadyDiscounted) {
          // Toode on juba soodushinnaga - paku abi, mitte allahindlust
          exitMsg = VISITOR_LANG === 'et' ? 'Ärge lahkuge! 👋 Kas teil on küsimusi? Aitan hea meelega!' :
                    VISITOR_LANG === 'en' ? 'Wait! 👋 Any questions? I\'m happy to help!' :
                    VISITOR_LANG === 'ru' ? 'Подождите! 👋 Есть вопросы? С радостью помогу!' :
                    'Ärge lahkuge! 👋 Kas teil on küsimusi? Aitan hea meelega!';
        } else {
          exitMsg = t('exitIntent');
        }

        bubble.innerHTML = `
          <div class="bubble-close" onclick="event.stopPropagation(); this.parentElement.classList.remove('show');">✕</div>
          ${exitMsg}
        `;
        bubble.classList.add('show');
        setTimeout(function() { bubble.classList.remove('show'); }, 8000);
      }
    });
  }

  // === FUNKTSIOONID ===
  function toggleChat() {
    isOpen = !isOpen;
    const win = document.getElementById('taig-chat-window');
    const btn = document.getElementById('taig-chat-btn');
    const bubble = document.getElementById('taig-chat-bubble');

    if (isOpen) {
      win.classList.add('open');
      btn.innerHTML = '✕';
      btn.classList.remove('has-dot');
      btn.classList.add('no-pulse');
      if (bubble) bubble.classList.remove('show');
      document.getElementById('taig-input').focus();

      // Lisa tervitussõnum ja quick-actions kui vestlus on tühi
      const messages = document.getElementById('taig-messages');
      if (messages.children.length === 0) {
        const ctx = detectPageContext();
        addBotMessage(ctx.greeting);

        // Sirvimisajaloo meeldetuletus tagasitulijale (kui on vaadanud tooteid varem)
        if (returningVisitor && ctx.type === 'home') {
          var viewed = getViewedProducts();
          if (viewed.length > 0) {
            var viewedNames = viewed.slice(0, 3).map(function(v) { return v.name; });
            addBotMessage('Eelmine kord vaatasite: **' + viewedNames.join('**, **') + '**. Kas soovite neid uuesti vaadata?');
          }
        }

        // Püsikliendi sõnum (3+ külastust)
        if (visitCount >= 3 && ctx.type !== 'checkout') {
          var loyaltyEl = document.createElement('div');
          loyaltyEl.className = 'taig-loyalty-msg';
          loyaltyEl.innerHTML = '⭐ Teie kui püsiklient! Kood <strong>TAGASI5</strong> annab lisaks <strong>5% soodustust!</strong>';
          messages.appendChild(loyaltyEl);
        }

        // Progressiriba kui korvis on tooteid
        var shippingBar = renderShippingBar();
        if (shippingBar) {
          messages.appendChild(shippingBar);
        }

        addQuickActions(ctx.type);

        // Proaktiivne müük: saada lehe kontekst API-sse ja lase chatbotil ise pakkumine teha
        var proactiveMsg = '';
        var pc = readPageContext();
        if (ctx.type === 'product') {
          proactiveMsg = '[PROAKTIIVNE MÜÜK] Klient avas chati TOOTE lehel. Toode: ' + (pc.product_name || 'tundmatu') + ', hind: ' + (pc.product_price || '?') + '. Räägi AINULT SELLEST KONKREETSEST tootest! Kiida seda, räägi eelistest. ÄRA paku alternatiive ega muid tooteid - klient tahab teada SELLE toote kohta! Alternatiive paku AINULT siis kui klient ise küsib.';
        } else if (ctx.type === 'checkout' || ctx.type === 'cart') {
          var cartInfo = '';
          if (pc.cart_items && pc.cart_items.length > 0) {
            cartInfo = ' Ostukorvis: ' + pc.cart_items.map(function(i) { return i.name; }).join(', ') + '.';
          }
          proactiveMsg = '[PROAKTIIVNE MÜÜK] Klient on ostukorvis/kassas!' + cartInfo + ' Maini TAIG10 koodi (10% allahindlust). Loo kiireloomulisust!';
        } else if (ctx.type === 'school') {
          proactiveMsg = '[PROAKTIIVNE MÜÜK] Klient vaatab KOOLITARVETE kategooriat. Küsi mis klassis laps käib ja paku konkreetseid tooteid vastavalt. Maini kooli stardipakki!';
        } else if (ctx.type === 'thule' || ctx.type === 'caselogic') {
          proactiveMsg = '[PROAKTIIVNE MÜÜK] Klient vaatab ' + ctx.type.toUpperCase() + ' tooteid. Paku selle brändi populaarsemaid tooteid ja räägi brändi kvaliteedist!';
        } else if (pc.category_name) {
          proactiveMsg = '[PROAKTIIVNE MÜÜK] Klient sirvib kategooriat: ' + pc.category_name + '. Paku selle kategooria populaarsemaid tooteid konkreetselt!';
        }
        // Saada proaktiivne müügipäring taustale (ei näita "typing")
        if (proactiveMsg) {
          setTimeout(function() { sendToAPI(proactiveMsg); }, 2000);
        }
      }

      autoOpenDone = true;
      sessionStorage.setItem('taig_auto_opened', 'true');
    } else {
      win.classList.remove('open');
      btn.innerHTML = '💬';
    }
  }

  // Sõnumi ID counter
  let msgCounter = 0;

  function addBotMessage(text) {
    const messages = document.getElementById('taig-messages');
    const msgId = 'taig-msg-' + (++msgCounter);

    // Parsi spetsiaalsed tagid
    const products = parseProducts(text);
    const lowStock = parseLowStock(text);
    let cleanText = stripProductTags(text);
    cleanText = stripLowStockTag(cleanText);

    // Koosta HTML teksti jaoks
    let html = cleanText
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\n/g, '<br>');

    // [IMG:url] tagid
    html = parseImgTags(html);

    // Low stock badge
    if (lowStock !== null) {
      html += ' <span class="taig-low-stock">Ainult ' + lowStock + ' tk!</span>';
    }

    // Loo wrapper (tekst + feedback)
    const wrap = document.createElement('div');
    wrap.className = 'taig-bot-msg-wrap';
    wrap.id = msgId;

    const msgEl = document.createElement('div');
    msgEl.className = 'taig-msg bot';
    msgEl.innerHTML = html;
    wrap.appendChild(msgEl);

    // Feedback nupud
    const feedbackEl = addFeedbackButtons(msgId);
    wrap.appendChild(feedbackEl);

    messages.appendChild(wrap);

    // Toote kaardid (horisontaalne rida)
    if (products.length > 0) {
      const cardRow = renderProductCards(products);
      messages.appendChild(cardRow);
    }

    messages.scrollTop = messages.scrollHeight;
  }

  function addMessage(text, type) {
    if (type === 'bot') {
      addBotMessage(text);
      return;
    }
    const messages = document.getElementById('taig-messages');
    const msg = document.createElement('div');
    msg.className = 'taig-msg user';

    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\n/g, '<br>');

    msg.innerHTML = html;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  function addQuickActions(pageType) {
    const messages = document.getElementById('taig-messages');
    const actions = getQuickActions(pageType);
    const wrap = document.createElement('div');
    wrap.className = 'taig-quick-actions';

    actions.forEach(function(action) {
      const btn = document.createElement('button');
      btn.className = 'taig-quick-btn';
      if (action.query === '__school_wizard__') {
        btn.classList.add('school-wizard-btn');
      }
      btn.textContent = action.label;
      btn.onclick = function() {
        wrap.remove();
        if (action.query === '__school_wizard__') {
          startSchoolWizard();
        } else {
          document.getElementById('taig-input').value = action.query;
          window._taigSend();
        }
      };
      wrap.appendChild(btn);
    });

    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
  }

  // === KOOLI STARDIPAKK VIISARD ===
  const schoolWizardSteps = [
    {
      question: 'Mis klassiga on tegu?',
      options: ['1.-3. klass', '4.-6. klass', '7.-9. klass', '10.-12. klass'],
    },
    {
      question: 'Mitu last läheb kooli?',
      options: ['1 laps', '2 last', '3+ last'],
    },
    {
      question: 'Mis on eelarve koolitarvetele?',
      options: ['Kuni 20€', '20-50€', '50-100€', '100€+'],
    },
  ];

  let wizardAnswers = [];
  let wizardStep = 0;

  function startSchoolWizard() {
    wizardAnswers = [];
    wizardStep = 0;
    showWizardStep();
  }

  function showWizardStep() {
    const messages = document.getElementById('taig-messages');
    const step = schoolWizardSteps[wizardStep];

    const wizardEl = document.createElement('div');
    wizardEl.className = 'taig-wizard';

    const title = document.createElement('div');
    title.className = 'taig-wizard-title';
    title.textContent = '🎒 Kooli stardipakk ' + (wizardStep + 1) + '/' + schoolWizardSteps.length;
    wizardEl.appendChild(title);

    const question = document.createElement('div');
    question.className = 'taig-wizard-question';
    question.textContent = step.question;
    wizardEl.appendChild(question);

    const optWrap = document.createElement('div');
    optWrap.className = 'taig-wizard-options';

    step.options.forEach(function(opt) {
      const optBtn = document.createElement('button');
      optBtn.className = 'taig-wizard-opt';
      optBtn.textContent = opt;
      optBtn.onclick = function() {
        wizardAnswers.push(opt);
        wizardEl.remove();

        if (wizardStep < schoolWizardSteps.length - 1) {
          wizardStep++;
          showWizardStep();
        } else {
          finishWizard();
        }
      };
      optWrap.appendChild(optBtn);
    });

    wizardEl.appendChild(optWrap);
    messages.appendChild(wizardEl);
    messages.scrollTop = messages.scrollHeight;
  }

  function finishWizard() {
    const query = 'Soovi leida kooli stardipakk: ' + wizardAnswers[0] + ' õpilasele, ' + wizardAnswers[1] + ', eelarve ' + wizardAnswers[2] + '. Paku sobivaid koolitarbeid.';
    addMessage(query, 'user');
    sendToAPI(query);
  }

  function showTyping(show) {
    const typing = document.getElementById('taig-typing');
    if (show) {
      typing.classList.add('show');
      typing.parentElement.querySelector('.taig-chat-messages').scrollTop =
        typing.parentElement.querySelector('.taig-chat-messages').scrollHeight;
    } else {
      typing.classList.remove('show');
    }
  }

  // === API SAATMINE ===
  async function sendToAPI(message) {
    if (isLoading) return;
    isLoading = true;
    document.getElementById('taig-send').disabled = true;
    showTyping(true);

    const pageContext = readPageContext();

    try {
      const resp = await fetch(API_URL + '/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
          page_context: pageContext,
        }),
      });

      if (resp.status === 429) {
        addBotMessage('Liiga palju päringuid. Palun oodake natuke. 🙏');
        return;
      }

      if (!resp.ok) {
        throw new Error('HTTP ' + resp.status);
      }

      const data = await resp.json();

      sessionId = data.session_id;
      localStorage.setItem('taig_chat_session', sessionId);

      addBotMessage(data.message);

    } catch (err) {
      console.error('Taig chatbot error:', err);
      addBotMessage('Vabandust, tekkis ühenduse viga. Palun proovige uuesti! 🔄');
    } finally {
      isLoading = false;
      document.getElementById('taig-send').disabled = false;
      showTyping(false);
      document.getElementById('taig-input').focus();
    }
  }

  window._taigSend = function() {
    if (isLoading) return;

    const input = document.getElementById('taig-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';
    sendToAPI(message);
  };

  // === INIT ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }

})();

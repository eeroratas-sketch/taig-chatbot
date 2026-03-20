(function() {
  'use strict';

  // Seadistus
  const SCRIPT_SRC = document.currentScript && document.currentScript.src;
  const AUTO_URL = SCRIPT_SRC ? SCRIPT_SRC.replace(/\/static\/chatbot-widget\.js.*$/, '').replace(/\/widget\.js.*$/, '') : '';
  const API_URL = window.TAIG_CHATBOT_URL || AUTO_URL || 'http://localhost:8100';
  const WIDGET_TITLE = 'Taig Abi';
  const PLACEHOLDER = 'Kirjuta siia...';

  // Auto-open seadistus
  const AUTO_OPEN_DELAY = 15000; // 15 sek pärast lehe laadimist
  const BUBBLE_DELAY = 5000;     // 5 sek pärast ilmub teate-mull
  const BUBBLE_DISMISS_TIME = 12000; // Mull kaob 12 sek pärast

  // Sessioon
  let sessionId = localStorage.getItem('taig_chat_session') || '';
  let isOpen = false;
  let isLoading = false;
  let autoOpenDone = sessionStorage.getItem('taig_auto_opened') === 'true';
  let bubbleDismissed = sessionStorage.getItem('taig_bubble_dismissed') === 'true';

  // === KONTEKSTITUVASTUS ===
  function detectPageContext() {
    const path = window.location.pathname.toLowerCase();
    const title = document.title.toLowerCase();

    if (path.includes('/checkout') || path.includes('/cart')) {
      return { type: 'checkout', greeting: 'Näen, et olete ostmas! 🛒 Kas teadsite, et koodiga TAIG10 saate 10% soodsamalt? Kas saan millegagi aidata?' };
    }
    if (path.includes('thule') || title.includes('thule')) {
      return { type: 'thule', greeting: 'Uurite Thule tooteid? 🧳 Need on absoluutne premium kvaliteet! Küsige julgelt – aitan leida teile sobiva kohvri või koti!' };
    }
    if (path.includes('case-logic') || title.includes('case logic')) {
      return { type: 'caselogic', greeting: 'Case Logic teeb suurepäraseid sülearvutikotte! 💼 Mis suuruses arvutile otsite kotti?' };
    }
    if (path.includes('kooli') || path.includes('school') || title.includes('kooli')) {
      return { type: 'school', greeting: 'Koolitarvete valik on meil lai! 📚 Kas otsite midagi konkreetset – pliiatseid, vihikuid, värve? Aitan leida!' };
    }
    if (path.includes('kontori') || path.includes('office') || title.includes('kontori')) {
      return { type: 'office', greeting: 'Kontoritarbed mugavalt kohale! 🏢 Kas otsite midagi konkreetset? Meil on Pentel, Staedtler ja teised top brändid!' };
    }
    if (path.includes('kirjutus') || title.includes('kirjutus') || title.includes('pliiats') || title.includes('pastakas')) {
      return { type: 'writing', greeting: 'Kirjutusvahendite valik! ✏️ Meie bestseller on Pentel BK417 pastakas – ainult 0,21€! Kas aitan valida?' };
    }
    // Toote leht
    if (path.match(/\.html$/) || document.querySelector('.product-info-main')) {
      return { type: 'product', greeting: 'Kas teil on selle toote kohta küsimusi? 🤔 Aitan hea meelega! Küsige mõõtude, materjalide või alternatiivide kohta.' };
    }
    // Avalehe / üldine
    return { type: 'home', greeting: 'Tere tulemast taig.ee poodi! 👋 Olen siin, et aidata teil leida sobivaid tooteid. Mis teid huvitab – koolitarbed, kontoritarbed või ehk Thule reisikohvrid?' };
  }

  // === QUICK-ACTION NUPUD ===
  function getQuickActions(pageType) {
    const actions = {
      home: [
        { label: '📚 Koolitarbed', query: 'Näita populaarseid koolitarbeid' },
        { label: '✏️ Kirjutusvahendid', query: 'Mis pastakad ja pliiatsid teil on?' },
        { label: '🧳 Thule kohvrid', query: 'Näita Thule kohvreid ja kotte' },
        { label: '🏷️ Soodustused', query: 'Mis soodustused teil praegu on?' },
      ],
      school: [
        { label: '✏️ Pliiatsid', query: 'Näita pliiatseid ja pastakaid kooli' },
        { label: '🎨 Värvid', query: 'Näita guašše ja akvarellvärve' },
        { label: '📓 Vihikud', query: 'Näita vihikuid' },
        { label: '🏷️ TAIG10 -10%', query: 'Kuidas saan allahindlust?' },
      ],
      office: [
        { label: '🖊️ Pastakad', query: 'Mis pastakad teil on?' },
        { label: '📎 Kontorikaubad', query: 'Näita kontoritarbeid' },
        { label: '💰 Hulgitellimus', query: 'Kas saan hulgihinda?' },
        { label: '🏷️ TAIG10 -10%', query: 'Kuidas saan allahindlust?' },
      ],
      checkout: [
        { label: '🏷️ Kasuta TAIG10', query: 'Kuidas kasutada kupongikoodi?' },
        { label: '🚚 Tarne info', query: 'Mis on tarnevõimalused ja hinnad?' },
        { label: '💳 Makse info', query: 'Mis makseviisid on?' },
      ],
      product: [
        { label: '📏 Mõõdud?', query: 'Mis on selle toote mõõdud?' },
        { label: '🔄 Alternatiivid', query: 'Mis alternatiive on sellele tootele?' },
        { label: '🏷️ TAIG10 -10%', query: 'Kas saan allahindlust?' },
      ],
      thule: [
        { label: '🧳 Kohvrid', query: 'Näita Thule kohvreid' },
        { label: '🎒 Seljakotid', query: 'Näita Thule seljakotte' },
        { label: '💼 Kotid', query: 'Näita Thule kotte' },
      ],
      caselogic: [
        { label: '💻 Sülearvutikotid', query: 'Näita Case Logic sülearvutikotte' },
        { label: '📱 Tahvelarvutile', query: 'Näita Case Logic tahvelarvutikotte' },
      ],
      writing: [
        { label: '🖊️ Pastakad', query: 'Näita pastakaid' },
        { label: '✏️ Pliiatsid', query: 'Näita pliiatseid' },
        { label: '🖍️ Markerid', query: 'Näita markereid' },
      ],
    };
    return actions[pageType] || actions.home;
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
      height: 540px;
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
    }
  `;

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
          <div class="subtitle">taig.ee müügiassistent • vastab kohe</div>
        </div>
        <button class="taig-chat-close" onclick="document.getElementById('taig-chat-btn').click()">✕</button>
      </div>
      <div class="taig-chat-messages" id="taig-messages"></div>
      <div class="taig-typing" id="taig-typing"><span></span><span></span><span></span></div>
      <div class="taig-chat-input-wrap">
        <input class="taig-chat-input" id="taig-input" type="text" placeholder="${PLACEHOLDER}" autocomplete="off">
        <button class="taig-chat-send" id="taig-send" onclick="window._taigSend()">➤</button>
      </div>
      <div class="taig-powered">Powered by AI ✨</div>
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
        bubble.innerHTML = `
          <div class="bubble-close" onclick="event.stopPropagation(); this.parentElement.classList.remove('show');">✕</div>
          Ärge lahkuge! 👋 Kasutage koodi <strong>TAIG10</strong> ja saate <strong>10% soodsamalt!</strong>
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
        addMessage(ctx.greeting, 'bot');
        addQuickActions(ctx.type);
      }

      autoOpenDone = true;
      sessionStorage.setItem('taig_auto_opened', 'true');
    } else {
      win.classList.remove('open');
      btn.innerHTML = '💬';
    }
  }

  function addMessage(text, type) {
    const messages = document.getElementById('taig-messages');
    const msg = document.createElement('div');
    msg.className = `taig-msg ${type}`;

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
      btn.textContent = action.label;
      btn.onclick = function() {
        // Eemalda quick-actions pärast klõpsu
        wrap.remove();
        // Simuleeri sõnumi saatmist
        document.getElementById('taig-input').value = action.query;
        window._taigSend();
      };
      wrap.appendChild(btn);
    });

    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
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

  window._taigSend = async function() {
    if (isLoading) return;

    const input = document.getElementById('taig-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';
    isLoading = true;
    document.getElementById('taig-send').disabled = true;
    showTyping(true);

    try {
      const resp = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
        }),
      });

      if (resp.status === 429) {
        addMessage('Liiga palju päringuid. Palun oodake natuke. 🙏', 'bot');
        return;
      }

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();

      sessionId = data.session_id;
      localStorage.setItem('taig_chat_session', sessionId);

      addMessage(data.message, 'bot');

    } catch (err) {
      console.error('Taig chatbot error:', err);
      addMessage('Vabandust, tekkis ühenduse viga. Palun proovige uuesti! 🔄', 'bot');
    } finally {
      isLoading = false;
      document.getElementById('taig-send').disabled = false;
      showTyping(false);
      document.getElementById('taig-input').focus();
    }
  };

  // === INIT ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createWidget);
  } else {
    createWidget();
  }

})();

(function() {
  'use strict';

  // Seadistus
  // Automaatne URL tuvastus: kui widget on laetud serverist, kasuta sama URL-i
  const SCRIPT_SRC = document.currentScript && document.currentScript.src;
  const AUTO_URL = SCRIPT_SRC ? SCRIPT_SRC.replace(/\/static\/chatbot-widget\.js.*$/, '').replace(/\/widget\.js.*$/, '') : '';
  const API_URL = window.TAIG_CHATBOT_URL || AUTO_URL || 'http://localhost:8100';
  const WIDGET_TITLE = 'Taig Abi';
  const WELCOME_MESSAGE = 'Tere! 👋 Olen Taig.ee müügiassistent. Kuidas saan aidata? Küsi julgelt toodete, hindade või soovituste kohta!';
  const PLACEHOLDER = 'Kirjuta siia...';

  // Sessioon
  let sessionId = localStorage.getItem('taig_chat_session') || '';
  let isOpen = false;
  let isLoading = false;

  // === STIILID ===
  const styles = `
    #taig-chat-btn {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: #2563eb;
      color: white;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(37,99,235,0.4);
      z-index: 99999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s, box-shadow 0.2s;
      font-size: 28px;
    }
    #taig-chat-btn:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 20px rgba(37,99,235,0.5);
    }
    #taig-chat-btn.has-dot::after {
      content: '';
      position: absolute;
      top: 4px;
      right: 4px;
      width: 14px;
      height: 14px;
      background: #ef4444;
      border-radius: 50%;
      border: 2px solid white;
    }

    #taig-chat-window {
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 370px;
      height: 520px;
      background: white;
      border-radius: 16px;
      box-shadow: 0 8px 30px rgba(0,0,0,0.15);
      z-index: 99998;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    #taig-chat-window.open { display: flex; }

    .taig-chat-header {
      background: #2563eb;
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
      background: #2563eb;
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
    .taig-chat-input:focus { border-color: #2563eb; }
    .taig-chat-send {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #2563eb;
      color: white;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
    }
    .taig-chat-send:hover { background: #1d4ed8; }
    .taig-chat-send:disabled { background: #94a3b8; cursor: not-allowed; }

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
    }
  `;

  // === HTML ===
  function createWidget() {
    // Style
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

    // Chat window
    const win = document.createElement('div');
    win.id = 'taig-chat-window';
    win.innerHTML = `
      <div class="taig-chat-header">
        <div>
          <h3>${WIDGET_TITLE}</h3>
          <div class="subtitle">taig.ee müügiassistent</div>
        </div>
        <button class="taig-chat-close" onclick="document.getElementById('taig-chat-btn').click()">✕</button>
      </div>
      <div class="taig-chat-messages" id="taig-messages"></div>
      <div class="taig-typing" id="taig-typing"><span></span><span></span><span></span></div>
      <div class="taig-chat-input-wrap">
        <input class="taig-chat-input" id="taig-input" type="text" placeholder="${PLACEHOLDER}" autocomplete="off">
        <button class="taig-chat-send" id="taig-send" onclick="window._taigSend()">➤</button>
      </div>
      <div class="taig-powered">Powered by AI</div>
    `;
    document.body.appendChild(win);

    // Enter key
    document.getElementById('taig-input').addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        window._taigSend();
      }
    });
  }

  // === FUNKTSIOONID ===
  function toggleChat() {
    isOpen = !isOpen;
    const win = document.getElementById('taig-chat-window');
    const btn = document.getElementById('taig-chat-btn');

    if (isOpen) {
      win.classList.add('open');
      btn.innerHTML = '✕';
      btn.classList.remove('has-dot');
      document.getElementById('taig-input').focus();

      // Lisa tervitussõnum kui vestlus on tühi
      const messages = document.getElementById('taig-messages');
      if (messages.children.length === 0) {
        addMessage(WELCOME_MESSAGE, 'bot');
      }
    } else {
      win.classList.remove('open');
      btn.innerHTML = '💬';
    }
  }

  function addMessage(text, type) {
    const messages = document.getElementById('taig-messages');
    const msg = document.createElement('div');
    msg.className = `taig-msg ${type}`;

    // Parsi markdown linkid: [tekst](url)
    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/\n/g, '<br>');

    msg.innerHTML = html;
    messages.appendChild(msg);

    // Scroll alla
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

    // Lisa kasutaja sõnum
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

      // Salvesta sessioon
      sessionId = data.session_id;
      localStorage.setItem('taig_chat_session', sessionId);

      // Lisa bot vastus
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

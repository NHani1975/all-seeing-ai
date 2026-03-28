/* ════════════════════════════════════════════════
   ALL-SEEING AI — app.js
   Handles: neural canvas, loading sim, tab switching,
            chat UI, insights tabs, hint tags, scroll.
   All API calls commented with // TODO: backend
   ════════════════════════════════════════════════ */
'use strict';

/* ── API config ─────────────────────────────────── */
const API_BASE = 'http://127.0.0.1:8000';

// Global store: website content from last analyze call (used in chat)
let _siteContent = '';

/* ── Utils ──────────────────────────────────── */
const $ = id => document.getElementById(id);
const qs = sel => document.querySelector(sel);
const qsa = sel => document.querySelectorAll(sel);
const sleep = ms => new Promise(r => setTimeout(r, ms));

/* ═══════════════════════════════════════════════
   1. NEURAL CANVAS — animated grid + particle nodes
═══════════════════════════════════════════════ */
(function initNeuralCanvas() {
  const canvas = $('neural-bg');
  const ctx = canvas.getContext('2d');

  let W, H, nodes = [], animFrame;

  const NODE_COUNT = 60;
  const MAX_DIST   = 160;
  const NODE_COLOR = '0, 212, 255';
  const LINE_COLOR = '0, 212, 255';

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function initNodes() {
    nodes = [];
    for (let i = 0; i < NODE_COUNT; i++) {
      nodes.push({
        x:  Math.random() * W,
        y:  Math.random() * H,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r:  Math.random() * 1.5 + 0.5,
      });
    }
  }

  function drawGrid() {
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.04)';
    ctx.lineWidth = 1;
    const STEP = 80;
    for (let x = 0; x < W; x += STEP) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += STEP) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }

  function animate() {
    ctx.clearRect(0, 0, W, H);
    drawGrid();

    for (const n of nodes) {
      n.x += n.vx;  n.y += n.vy;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
    }

    // Draw edges
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < MAX_DIST) {
          const alpha = (1 - d / MAX_DIST) * 0.25;
          ctx.strokeStyle = `rgba(${LINE_COLOR}, ${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${NODE_COLOR}, 0.5)`;
      ctx.fill();
    }

    animFrame = requestAnimationFrame(animate);
  }

  window.addEventListener('resize', () => { resize(); initNodes(); });
  resize(); initNodes(); animate();
})();

/* ═══════════════════════════════════════════════
   2. HINT TAGS — pre-fill the URL input
═══════════════════════════════════════════════ */
qsa('.hint-tag').forEach(btn => {
  btn.addEventListener('click', () => {
    $('url-input').value = btn.dataset.url;
    $('url-input').focus();
  });
});

/* ═══════════════════════════════════════════════
   3. ANALYZE BUTTON — loading sequence + results
═══════════════════════════════════════════════ */
$('analyze-btn').addEventListener('click', handleAnalyze);
$('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') handleAnalyze();
});

async function handleAnalyze() {
  const raw = $('url-input').value.trim();
  if (!raw) {
    shakeInput(); return;
  }
  const url = normalizeUrl(raw);
  const data = await runLoadingSequence(url);
  if (data) showResults(url, data);
}

function normalizeUrl(url) {
  if (!/^https?:\/\//i.test(url)) return 'https://' + url;
  return url;
}

function shakeInput() {
  const el = $('target-input-container');
  el.style.animation = 'none';
  requestAnimationFrame(() => {
    el.style.animation = 'shake 0.4s ease';
  });
}

// Inject shake keyframe dynamically
(function injectShake() {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes shake {
      0%,100% { transform: translateX(0); }
      20%      { transform: translateX(-8px); }
      40%      { transform: translateX(8px); }
      60%      { transform: translateX(-5px); }
      80%      { transform: translateX(5px); }
    }`;
  document.head.appendChild(style);
})();

async function runLoadingSequence(url) {
  const overlay  = $('loading-overlay');
  const bar      = $('loading-bar');
  const urlLabel = $('loading-url');
  const steps    = ['ls1','ls2','ls3','ls4'];

  urlLabel.textContent = url;
  overlay.hidden = false;
  document.body.style.overflow = 'hidden';

  // Reset steps
  steps.forEach(id => {
    const el = $(id);
    el.classList.remove('active','done');
    el.textContent = el.textContent.replace(/\[.?\]/,'[ ]');
  });
  bar.style.width = '0%';

  // Animate steps 1–2 visually while fetch runs
  const markActive = id => {
    const el = $(id);
    el.classList.add('active');
    el.textContent = el.textContent.replace('[ ]','[/]');
  };
  const markDone = id => {
    const el = $(id);
    el.classList.remove('active');
    el.classList.add('done');
    el.textContent = el.textContent.replace('[/]','[✓]');
  };

  markActive('ls1');
  await animateBar(bar, 0, 20, 500);
  markDone('ls1');

  markActive('ls2');
  await animateBar(bar, 20, 45, 500);
  markDone('ls2');

  markActive('ls3');
  await animateBar(bar, 45, 60, 400);

  // ── Real API call ─────────────────────────────────────────
  let data = null;
  try {
    const res = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Server error ${res.status}`);
    }

    data = await res.json();
  } catch (exc) {
    overlay.hidden = true;
    document.body.style.overflow = '';
    showError(`Analysis failed: ${exc.message}`);
    return null;
  }
  // ─────────────────────────────────────────────────────────

  markDone('ls3');
  markActive('ls4');
  await animateBar(bar, 60, 100, 400);
  markDone('ls4');
  await sleep(300);

  overlay.hidden = true;
  document.body.style.overflow = '';
  return data;
}

function showError(msg) {
  // Inject a dismissible error banner below the URL input
  let banner = $('error-banner');
  if (!banner) {
    banner = document.createElement('p');
    banner.id = 'error-banner';
    banner.style.cssText = [
      'margin-top:14px', 'font-size:0.75rem', 'color:#ff3a6e',
      'border:1px solid rgba(255,58,110,0.3)', 'padding:8px 14px',
      'border-radius:2px', 'cursor:pointer', 'max-width:680px',
      'text-align:left'
    ].join(';');
    banner.title = 'Click to dismiss';
    banner.addEventListener('click', () => banner.remove());
    $('target-input-container').insertAdjacentElement('afterend', banner);
  }
  banner.textContent = `⚠ ${msg}`;
}

function animateBar(bar, from, to, duration) {
  return new Promise(resolve => {
    const start = performance.now();
    function step(now) {
      const p = Math.min((now - start) / duration, 1);
      bar.style.width = (from + (to - from) * easeOut(p)) + '%';
      if (p < 1) requestAnimationFrame(step);
      else resolve();
    }
    requestAnimationFrame(step);
  });
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

/* ═══════════════════════════════════════════════
   4. RESULTS — render real API data
═══════════════════════════════════════════════ */
function showResults(url, data) {
  const hostname = (() => {
    try { return new URL(url).hostname.replace('www.', ''); }
    catch { return url; }
  })();

  $('results-url-badge').textContent = hostname;
  const section = $('results-section');
  section.hidden = false;

  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Stagger panel entrances
  qsa('.glass-panel').forEach((p, i) => {
    p.style.opacity = '0';
    p.style.transform = 'translateY(24px)';
    p.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    setTimeout(() => {
      p.style.opacity = '1';
      p.style.transform = 'translateY(0)';
    }, 120 * i);
  });

  injectRealContent(hostname, data);
}

/* ── Real content from API ──────────────────────── */
function injectRealContent(hostname, data) {
  // Store content globally for chat calls
  _siteContent = data.content || '';

  // ── SUMMARY TABS ────────────────────────────────
  const bulletsHtml = (data.bullet_points || []).map(b =>
    `<li>${b}</li>`
  ).join('');

  const prosHtml  = (data.pros || []).map(p => `<li>${p}</li>`).join('');
  const consHtml  = (data.cons || []).map(c => `<li>${c}</li>`).join('');

  const summaryData = {
    short: `<p>${data.summary || 'No summary available.'}</p>`,

    bullets: `<ul class="bullet-list">${bulletsHtml}</ul>`,

    proscons: `<div class="pros-cons">
      <div class="pros-block">
        <h4>✦ STRENGTHS</h4>
        <ul class="pros-list">${prosHtml}</ul>
      </div>
      <div class="cons-block">
        <h4>✦ WEAKNESSES</h4>
        <ul class="cons-list">${consHtml}</ul>
      </div>
    </div>`,
  };

  window._summaryData = summaryData;
  renderTab('short');

  // ── CHAT INIT ────────────────────────────────────
  const msgs = $('chat-messages');
  msgs.innerHTML = '';
  addMsg('ai', `I've analyzed <strong>${hostname}</strong>. Ask me anything — I'll only answer from what's on this page.`);

  // ── INSIGHTS — map backend insights array to 3 tabs ───────
  const insights = data.insights || [];
  // Split insights evenly across tabs (backend returns flat list)
  const chunk = (arr, size) => Array.from({ length: Math.ceil(arr.length / size) }, (_, i) => arr.slice(i * size, i * size + size));
  const chunks = chunk(insights, Math.max(1, Math.ceil(insights.length / 3)));

  const icons = ['💡','🚀','🎯','⚡','🔍','📊','🤝','💰','👥'];
  const toCards = (arr) => arr.map((text, i) => ({
    icon: icons[i % icons.length],
    title: text.split('.')[0].substring(0, 50),
    body: text,
  }));

  const insightsData = {
    ideas:     toCards(chunks[0] || insights.slice(0, 2)),
    improve:   toCards(chunks[1] || insights.slice(0, 2)),
    takeaways: toCards(chunks[2] || insights.slice(0, 2)),
  };

  window._insightsData = insightsData;
  renderInsights('ideas');
}

/* ── Render summary tab ─────────────────────── */
function renderTab(key) {
  const content = $('tab-content');
  content.style.opacity = '0';
  setTimeout(() => {
    content.innerHTML = window._summaryData[key];
    content.style.transition = 'opacity 0.2s ease';
    content.style.opacity = '1';
  }, 150);
}

/* ── Render insights tab ────────────────────── */
function renderInsights(key) {
  const container = $('insights-content');
  container.style.opacity = '0';
  setTimeout(() => {
    const cards = window._insightsData[key];
    container.innerHTML = cards.map((c, i) => `
      <div class="insight-card" style="animation-delay:${i * 80}ms">
        <div class="insight-card-title">
          <span>${c.icon}</span>${c.title}
        </div>
        <div>${c.body}</div>
      </div>
    `).join('');
    container.style.transition = 'opacity 0.2s ease';
    container.style.opacity = '1';
  }, 150);
}

/* ═══════════════════════════════════════════════
   5. TAB SWITCHING — Summary panel
═══════════════════════════════════════════════ */
qsa('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    qsa('.tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
    tab.classList.add('active');
    tab.setAttribute('aria-selected','true');
    $('tab-content').setAttribute('aria-labelledby', tab.id);
    renderTab(tab.dataset.tab);
  });
});

/* ═══════════════════════════════════════════════
   6. INSIGHTS TAB SWITCHING
═══════════════════════════════════════════════ */
qsa('.insights-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    qsa('.insights-tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
    tab.classList.add('active');
    tab.setAttribute('aria-selected','true');
    renderInsights(tab.dataset.itab);
  });
});

/* ═══════════════════════════════════════════════
   7. CHAT — message handling
═══════════════════════════════════════════════ */
$('chat-send-btn').addEventListener('click', sendChat);
$('chat-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') sendChat();
});

async function sendChat() {
  const input = $('chat-input');
  const text  = input.value.trim();
  if (!text) return;

  input.value = '';
  addMsg('user', text);

  if (!_siteContent) {
    addMsg('ai', 'Please analyze a website first before asking questions.');
    return;
  }

  // Show typing indicator
  const typingId = 'typing-' + Date.now();
  const typingDiv = document.createElement('div');
  typingDiv.id = typingId;
  typingDiv.className = 'msg ai';
  typingDiv.innerHTML = `<div class="msg-role">◉ ALL-SEEING</div><div class="msg-bubble" style="opacity:0.5;font-style:italic">Thinking...</div>`;
  $('chat-messages').appendChild(typingDiv);
  $('chat-messages').scrollTop = $('chat-messages').scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text, content: _siteContent }),
    });

    typingDiv.remove();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      addMsg('ai', `⚠ Error: ${err.detail || 'Could not reach the server.'}`);
      return;
    }

    const data = await res.json();
    addMsg('ai', data.answer || 'No answer returned.');
  } catch (exc) {
    typingDiv.remove();
    addMsg('ai', `⚠ Network error: ${exc.message}. Is the server running at ${API_BASE}?`);
  }
}

function addMsg(role, html) {
  const msgs = $('chat-messages');
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = `
    <div class="msg-role">${role === 'ai' ? '◉ ALL-SEEING' : '▸ YOU'}</div>
    <div class="msg-bubble">${html}</div>
  `;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

/* ═══════════════════════════════════════════════
   8. NEW ANALYSIS BUTTON
═══════════════════════════════════════════════ */
$('new-analysis-btn').addEventListener('click', () => {
  $('results-section').hidden = true;
  $('url-input').value = '';
  document.querySelector('.hero').scrollIntoView({ behavior: 'smooth' });
  setTimeout(() => $('url-input').focus(), 600);
});

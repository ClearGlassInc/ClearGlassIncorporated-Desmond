(() => {
  'use strict';

  const VERSION = '1.0.0';
  const STORAGE_KEY = 'clearglass:aegis:trace:v1';
  const SIGNAL_LIMIT = 64;
  const WINDOW_MS = 60_000;
  const ROTATE_MS = 15_000;
  const CLASSIFICATIONS = ['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'CROWN-JEWEL'];
  const STATES = ['LOW', 'GUARDED', 'HIGH', 'CRITICAL'];

  const now = () => Date.now();
  const clampClassification = (value) => {
    const normalized = String(value || 'PUBLIC').trim().toUpperCase();
    return CLASSIFICATIONS.includes(normalized) ? normalized : 'PUBLIC';
  };

  const randomToken = () => {
    const bytes = new Uint8Array(18);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
  };

  const getTraceToken = () => {
    try {
      const existing = sessionStorage.getItem(STORAGE_KEY);
      if (existing && /^[a-f0-9]{36}$/i.test(existing)) return existing;
      const token = randomToken();
      sessionStorage.setItem(STORAGE_KEY, token);
      return token;
    } catch {
      return randomToken();
    }
  };

  const configuredClassification = () => {
    const meta = document.querySelector('meta[name="aegis-classification"]');
    return clampClassification(
      document.documentElement.dataset.aegisClassification ||
      document.body?.dataset.aegisClassification ||
      meta?.content ||
      'PUBLIC'
    );
  };

  const classification = configuredClassification();
  const classificationRank = CLASSIFICATIONS.indexOf(classification);
  const explicitlyProtected =
    document.documentElement.dataset.aegisProtected === 'true' ||
    document.body?.dataset.aegisProtected === 'true';
  const protectedMode = explicitlyProtected || classificationRank >= CLASSIFICATIONS.indexOf('CONFIDENTIAL');
  const traceToken = getTraceToken();
  const traceFragment = traceToken.slice(0, 10).toUpperCase();
  const signals = [];
  let state = 'LOW';

  const isEditable = (target) => {
    if (!(target instanceof Element)) return false;
    return Boolean(target.closest('input, textarea, select, [contenteditable="true"], [data-aegis-copy-allowed="true"]'));
  };

  const scoreState = () => {
    const cutoff = now() - WINDOW_MS;
    const recent = signals.filter((signal) => signal.at >= cutoff);
    const weighted = recent.reduce((sum, signal) => sum + signal.weight, 0);
    if (weighted >= 24) return 'CRITICAL';
    if (weighted >= 12) return 'HIGH';
    if (weighted >= 5) return 'GUARDED';
    return 'LOW';
  };

  const setState = (nextState) => {
    if (!STATES.includes(nextState) || nextState === state) return;
    const previous = state;
    state = nextState;
    const root = document.getElementById('aegis-glass-root');
    if (root) {
      for (const candidate of STATES) root.classList.remove(`aegis-state-${candidate.toLowerCase()}`);
      root.classList.add(`aegis-state-${state.toLowerCase()}`);
    }
    updateStatus();
    window.dispatchEvent(new CustomEvent('aegis:risk-change', {
      detail: Object.freeze({ previous, state, classification, trace: traceFragment })
    }));
  };

  const recordSignal = (type, weight = 1, detail = {}) => {
    const signal = Object.freeze({
      type,
      weight,
      at: now(),
      detail: { ...detail }
    });
    signals.push(signal);
    if (signals.length > SIGNAL_LIMIT) signals.splice(0, signals.length - SIGNAL_LIMIT);
    window.dispatchEvent(new CustomEvent('aegis:signal', { detail: signal }));
    setState(scoreState());
  };

  const watermarkText = () => {
    const timestamp = new Date().toISOString().replace('T', ' ').slice(0, 19) + 'Z';
    return `CLEARGLASS • ${classification} • ${traceFragment} • ${timestamp}`;
  };

  const rotateWatermarks = () => {
    const root = document.getElementById('aegis-glass-root');
    if (!root || !protectedMode) return;
    const x = Math.floor(Math.random() * 41) - 20;
    const y = Math.floor(Math.random() * 41) - 20;
    root.style.setProperty('--aegis-shift-x', `${x}px`);
    root.style.setProperty('--aegis-shift-y', `${y}px`);
    root.querySelectorAll('.aegis-watermark').forEach((node) => {
      node.textContent = watermarkText();
    });
  };

  function updateStatus() {
    const node = document.getElementById('aegis-glass-status');
    if (!node) return;
    const mode = protectedMode ? 'PROTECTED' : 'MONITOR';
    node.textContent = `AEGIS GLASS · ${mode} · ${classification} · ${state}`;
    node.setAttribute(
      'aria-label',
      `Aegis Glass security layer. Mode ${mode}. Classification ${classification}. Risk state ${state}.`
    );
  }

  const mount = () => {
    if (!document.body || document.getElementById('aegis-glass-root')) return;

    if (protectedMode) document.body.classList.add('aegis-protected');

    const root = document.createElement('div');
    root.id = 'aegis-glass-root';
    root.className = 'aegis-state-low';
    root.dataset.aegisVersion = VERSION;

    const mesh = document.createElement('div');
    mesh.id = 'aegis-glass-mesh';
    mesh.setAttribute('aria-hidden', 'true');

    const watermarks = document.createElement('div');
    watermarks.id = 'aegis-glass-watermarks';
    watermarks.setAttribute('aria-hidden', 'true');
    for (let index = 0; index < 12; index += 1) {
      const item = document.createElement('span');
      item.className = 'aegis-watermark';
      item.textContent = watermarkText();
      watermarks.appendChild(item);
    }

    const status = document.createElement('div');
    status.id = 'aegis-glass-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');

    const printNotice = document.createElement('div');
    printNotice.id = 'aegis-print-notice';
    printNotice.textContent = `Protected ClearGlass content. Printing is disabled for this classified view. Trace ${traceFragment}.`;

    let securityStack = document.getElementById('cg-security-stack');
    if (!securityStack) {
      securityStack = document.createElement('div');
      securityStack.id = 'cg-security-stack';
      securityStack.setAttribute('role', 'group');
      securityStack.setAttribute('aria-label', 'ClearGlass security controls');
    }

    root.append(mesh, watermarks, printNotice);
    document.body.appendChild(root);
    document.body.appendChild(securityStack);
    const stealthButton = document.getElementById('cg-stealth-btn');
    if (stealthButton) securityStack.appendChild(stealthButton);
    securityStack.appendChild(status);
    updateStatus();
    rotateWatermarks();

    if (protectedMode) {
      setInterval(rotateWatermarks, ROTATE_MS);
    }
  };

  const denyProtectedAction = (event, type, weight) => {
    if (!protectedMode || isEditable(event.target)) return false;
    event.preventDefault();
    recordSignal(type, weight, { tag: event.target?.tagName || null });
    return true;
  };

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) recordSignal('visibility-hidden', protectedMode ? 2 : 1);
  }, { passive: true });

  window.addEventListener('blur', () => recordSignal('window-blur', protectedMode ? 2 : 1), { passive: true });
  window.addEventListener('focus', () => recordSignal('window-focus', 0), { passive: true });

  document.addEventListener('copy', (event) => {
    if (denyProtectedAction(event, 'copy-blocked', 3)) return;
    if (event.target instanceof Element && event.target.closest('[data-aegis-protected="true"]')) {
      event.preventDefault();
      recordSignal('protected-copy-blocked', 3);
    }
  });

  document.addEventListener('contextmenu', (event) => {
    if (protectedMode && !isEditable(event.target)) {
      event.preventDefault();
      recordSignal('context-menu-blocked', 2);
    }
  });

  document.addEventListener('dragstart', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    if (protectedMode && target.closest('img, video, canvas, [data-aegis-protected="true"]')) {
      event.preventDefault();
      recordSignal('drag-blocked', 2);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (!protectedMode) return;
    const key = event.key.toLowerCase();
    const modifier = event.ctrlKey || event.metaKey;
    if (modifier && (key === 'p' || key === 's')) {
      event.preventDefault();
      recordSignal(key === 'p' ? 'print-shortcut-blocked' : 'save-shortcut-blocked', 4);
    }
  });

  window.addEventListener('beforeprint', () => {
    if (protectedMode) recordSignal('print-attempt', 4);
  });

  Object.defineProperty(window, 'AegisGlass', {
    configurable: false,
    enumerable: false,
    writable: false,
    value: Object.freeze({
      version: VERSION,
      classification,
      protectedMode,
      trace: traceFragment,
      getState: () => state,
      getSignals: () => signals.map((signal) => ({ ...signal, detail: { ...signal.detail } })),
      recordSignal: (type, weight = 1, detail = {}) => recordSignal(type, weight, detail)
    })
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount, { once: true });
  } else {
    mount();
  }
})();

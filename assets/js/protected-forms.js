(function () {
  'use strict';

  var meta = document.querySelector('meta[name="clearglass-api-base"]');
  var rawBase = meta && meta.getAttribute('content') ? meta.getAttribute('content').trim() : '';
  if (!rawBase) return;

  var apiBase;
  try {
    apiBase = new URL(rawBase);
  } catch (_) {
    return;
  }
  var host = apiBase.hostname.toLowerCase();
  if (
    apiBase.protocol !== 'https:' ||
    apiBase.username ||
    apiBase.password ||
    apiBase.search ||
    apiBase.hash ||
    apiBase.pathname !== '/' ||
    (host !== 'clearglassinc.com' && !host.endsWith('.clearglassinc.com'))
  ) {
    return;
  }

  function statusNode(form) {
    var node = form.querySelector('[data-cg-form-status]');
    if (!node) {
      node = document.createElement('p');
      node.setAttribute('data-cg-form-status', '');
      node.setAttribute('aria-live', 'polite');
      form.appendChild(node);
    }
    return node;
  }

  document.addEventListener('submit', function (event) {
    var form = event.target.closest('form[data-cg-form-kind]');
    if (!form) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (!form.reportValidity()) return;

    var data = new FormData(form);
    var consentInput = form.querySelector('[name="consent"]');
    var payload = {
      kind: form.getAttribute('data-cg-form-kind'),
      email: String(data.get('email') || ''),
      name: String(data.get('name') || ''),
      organization: String(data.get('organization') || ''),
      size: String(data.get('size') || ''),
      message: String(data.get('message') || ''),
      consent: consentInput ? (consentInput.type === 'checkbox' ? consentInput.checked : String(data.get('consent')) === 'true') : false,
      website: String(data.get('_honey') || '')
    };
    var status = statusNode(form);
    var button = form.querySelector('button[type="submit"]');
    if (button) button.disabled = true;
    status.textContent = 'Sending…';

    var controller = new AbortController();
    var timeout = window.setTimeout(function () { controller.abort(); }, 10000);
    fetch(new URL('/api/forms/submit', apiBase).href, {
      method: 'POST',
      headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'omit',
      signal: controller.signal
    }).then(function (response) {
      if (!response.ok) throw new Error('form API returned ' + response.status);
      status.textContent = 'Thank you — your request was accepted.';
      form.reset();
      var next = data.get('_next');
      if (next) {
        var target = new URL(String(next), window.location.href);
        if (target.protocol === 'https:' && (target.hostname === 'clearglassinc.com' || target.hostname.endsWith('.clearglassinc.com'))) {
          window.location.assign(target.href);
        }
      }
    }).catch(function () {
      status.textContent = 'Could not submit just now. Please use the published contact email.';
    }).finally(function () {
      window.clearTimeout(timeout);
      if (button) button.disabled = false;
    });
  }, true);
})();

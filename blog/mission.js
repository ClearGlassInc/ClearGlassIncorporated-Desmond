(function () {
  'use strict';
  var root = document.querySelector('.cg-blog-mission');
  if (!root) return;
  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-article-card]'));
  var pageSize = 9;
  var page = 1;
  var filtered = cards.slice();
  var search = root.querySelector('[data-search]');
  var category = root.querySelector('[data-category]');
  var tag = root.querySelector('[data-tag]');
  var sort = root.querySelector('[data-sort]');
  var state = root.querySelector('[data-state]');
  var empty = root.querySelector('[data-empty]');
  var historyOnly = false;
  var storage = { bookmarks: 'cg.blog.bookmarks.v1', history: 'cg.blog.history.v1' };

  function emit(name, detail) {
    root.dispatchEvent(new CustomEvent('cg:analytics', { bubbles: true, detail: Object.assign({ event: name }, detail || {}) }));
    if (Array.isArray(window.dataLayer)) window.dataLayer.push(Object.assign({ event: 'cg_blog_' + name }, detail || {}));
  }
  function read(key) { try { return JSON.parse(localStorage.getItem(key) || '[]'); } catch (_) { return []; } }
  function write(key, value) { try { localStorage.setItem(key, JSON.stringify(value.slice(0, 100))); return true; } catch (_) { toast('Local storage is unavailable.'); return false; } }
  function toast(message) { var node = root.querySelector('[data-toast]'); if (!node) return; node.textContent = message; node.setAttribute('data-visible', ''); clearTimeout(node._timer); node._timer = setTimeout(function () { node.removeAttribute('data-visible'); }, 2400); }
  function norm(value) { return (value || '').toLowerCase().trim(); }
  function syncUrl() { if (!history.replaceState) return; var params = new URLSearchParams(); if (search && search.value) params.set('q', search.value); if (category && category.value) params.set('category', category.value); if (tag && tag.value) params.set('tag', tag.value); if (sort && sort.value !== 'newest') params.set('sort', sort.value); if (page > 1) params.set('page', page); history.replaceState(null, '', location.pathname + (params.toString() ? '?' + params : '')); }
  function render() {
    cards.forEach(function (card) { card.hidden = true; });
    var start = (page - 1) * pageSize;
    filtered.slice(start, start + pageSize).forEach(function (card) { card.hidden = false; });
    var pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    var status = root.querySelector('[data-page-status]');
    if (status) status.textContent = filtered.length ? 'Page ' + page + ' of ' + pages : 'No results';
    var previous = root.querySelector('[data-previous]'); var next = root.querySelector('[data-next]');
    if (previous) previous.disabled = page <= 1; if (next) next.disabled = page >= pages;
    if (empty) empty.hidden = filtered.length !== 0;
    if (state) state.textContent = filtered.length + ' published briefing' + (filtered.length === 1 ? '' : 's') + ' matched.';
    syncUrl();
  }
  function apply(reason) {
    var query = norm(search && search.value); var cat = norm(category && category.value); var selectedTag = norm(tag && tag.value); var visited = read(storage.history);
    filtered = cards.filter(function (card) {
      var haystack = [card.dataset.title, card.dataset.summary, card.dataset.category, card.dataset.tags, card.dataset.author].join(' ').toLowerCase();
      return (!query || haystack.indexOf(query) !== -1) && (!cat || norm(card.dataset.category) === cat) && (!selectedTag || norm(card.dataset.tags).split(/\s+/).indexOf(selectedTag) !== -1) && (!historyOnly || visited.indexOf(card.dataset.slug) !== -1);
    });
    filtered.sort(function (a, b) { if (sort && sort.value === 'oldest') return a.dataset.date.localeCompare(b.dataset.date); if (sort && sort.value === 'reading-time') return Number(a.dataset.minutes) - Number(b.dataset.minutes); return b.dataset.date.localeCompare(a.dataset.date); });
    page = 1; render(); if (reason) emit(reason, { query_length: query.length, category: cat, tag: selectedTag, sort: sort && sort.value, result_count: filtered.length });
  }
  [search, category, tag, sort].forEach(function (control) { if (control) control.addEventListener(control === search ? 'input' : 'change', function () { apply(control === search ? 'search' : 'filter'); }); });
  root.addEventListener('click', function (event) {
    var categoryButton = event.target.closest('[data-category-filter]'); var tagButton = event.target.closest('[data-tag-filter]');
    if (categoryButton && category) { category.value = categoryButton.dataset.categoryFilter; apply('filter'); category.focus(); }
    if (tagButton && tag) { tag.value = tagButton.dataset.tagFilter; apply('filter'); tag.focus(); }
    if (event.target.closest('[data-reset]')) { if (search) search.value = ''; if (category) category.value = ''; if (tag) tag.value = ''; if (sort) sort.value = 'newest'; historyOnly = false; apply('filter'); }
    if (event.target.closest('[data-previous]') && page > 1) { page--; render(); }
    if (event.target.closest('[data-next]') && page < Math.ceil(filtered.length / pageSize)) { page++; render(); }
    if (event.target.closest('[data-history-toggle]')) { historyOnly = !historyOnly; event.target.closest('[data-history-toggle]').setAttribute('aria-pressed', String(historyOnly)); apply('filter'); }
    var tool = event.target.closest('[data-bookmark],[data-copy-link],[data-share]');
    if (tool) {
      var toolCard = tool.closest('[data-article-card]'); var url = new URL(toolCard.querySelector('h3 a').getAttribute('href'), location.href).href;
      if (tool.hasAttribute('data-bookmark')) { var saved = read(storage.bookmarks); var exists = saved.indexOf(toolCard.dataset.slug) !== -1; saved = saved.filter(function (item) { return item !== toolCard.dataset.slug; }); if (!exists) saved.unshift(toolCard.dataset.slug); if (write(storage.bookmarks, saved)) { tool.setAttribute('aria-pressed', String(!exists)); tool.textContent = exists ? '☆ Bookmark' : '★ Bookmarked'; toast(exists ? 'Bookmark removed.' : 'Briefing bookmarked locally.'); emit('bookmark', { slug: toolCard.dataset.slug, saved: !exists }); } }
      if (tool.hasAttribute('data-copy-link')) { navigator.clipboard && navigator.clipboard.writeText(url).then(function () { toast('Link copied.'); emit('share', { method: 'copy', slug: toolCard.dataset.slug }); }, function () { toast('Copy unavailable in this browser.'); }); }
      if (tool.hasAttribute('data-share')) { if (navigator.share) navigator.share({ title: toolCard.dataset.title, url: url }).then(function () { emit('share', { method: 'native', slug: toolCard.dataset.slug }); }, function () {}); else { navigator.clipboard && navigator.clipboard.writeText(url); toast('Native share unavailable; link copied.'); emit('share', { method: 'copy_fallback', slug: toolCard.dataset.slug }); } }
    }
    var link = event.target.closest('a[href]'); if (link) { var articleCard = link.closest('[data-article-card]'); if (articleCard) { var visited = read(storage.history).filter(function (slug) { return slug !== articleCard.dataset.slug; }); visited.unshift(articleCard.dataset.slug); write(storage.history, visited); emit('article_view', { slug: articleCard.dataset.slug }); } else if (link.origin !== location.origin) emit('outbound_link', { host: link.hostname }); }
  });
  var params = new URLSearchParams(location.search); if (search) search.value = params.get('q') || ''; if (category) category.value = params.get('category') || ''; if (tag) tag.value = params.get('tag') || ''; if (sort) sort.value = params.get('sort') || 'newest'; apply(); page = Math.min(Math.max(1, Number(params.get('page')) || 1), Math.max(1, Math.ceil(filtered.length / pageSize))); render();

  var savedOnLoad = read(storage.bookmarks); cards.forEach(function (card) { var button = card.querySelector('[data-bookmark]'); if (button && savedOnLoad.indexOf(card.dataset.slug) !== -1) { button.setAttribute('aria-pressed', 'true'); button.textContent = '★ Bookmarked'; } });

  var palette = root.querySelector('[data-palette]'); var paletteInput = root.querySelector('[data-palette-search]'); var results = root.querySelector('[data-palette-results]'); var selected = 0;
  function paletteItems(query) { var fixed = [{ title: 'Intelligence archive', url: '#mission-archive', meta: 'Navigate' }, { title: 'Featured briefing', url: '#featured', meta: 'Navigate' }, { title: 'RSS feed', url: 'feed.xml', meta: 'Feed' }]; return fixed.concat(cards.map(function (card) { return { title: card.dataset.title, url: card.querySelector('a').getAttribute('href'), meta: card.dataset.category }; })).filter(function (item) { return !query || norm(item.title + ' ' + item.meta).indexOf(norm(query)) !== -1; }).slice(0, 12); }
  function paintPalette() { if (!results) return; var items = paletteItems(paletteInput && paletteInput.value); selected = Math.min(selected, Math.max(0, items.length - 1)); results.innerHTML = items.map(function (item, index) { return '<li' + (index === selected ? ' data-active' : '') + '><a href="' + item.url + '"><span>' + item.title.replace(/[&<>"']/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]; }) + '</span><small>' + item.meta + '</small></a></li>'; }).join(''); }
  function openPalette() { if (!palette) return; palette.showModal(); selected = 0; if (paletteInput) paletteInput.value = ''; paintPalette(); requestAnimationFrame(function () { paletteInput && paletteInput.focus(); }); emit('command_palette_open'); }
  root.querySelectorAll('[data-open-palette]').forEach(function (button) { button.addEventListener('click', openPalette); });
  document.addEventListener('keydown', function (event) { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); if (palette && palette.open) palette.close(); else openPalette(); } else if (palette && palette.open && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) { event.preventDefault(); var count = paletteItems(paletteInput.value).length; selected = (selected + (event.key === 'ArrowDown' ? 1 : -1) + count) % count; paintPalette(); } else if (palette && palette.open && event.key === 'Enter' && document.activeElement === paletteInput) { event.preventDefault(); var active = results.querySelector('[data-active] a'); if (active) location.href = active.href; } });
  if (paletteInput) paletteInput.addEventListener('input', function () { selected = 0; paintPalette(); });
  function progress() { var max = document.documentElement.scrollHeight - innerHeight; root.style.setProperty('--progress', (max > 0 ? Math.min(100, scrollY / max * 100) : 0) + '%'); }
  addEventListener('scroll', progress, { passive: true }); progress();
}());

(function () {
  'use strict';
  var root = document.querySelector('.cg-blog-mission');
  if (!root) return;
  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-article-card]'));
  var controls = { search: root.querySelector('[data-search]'), category: root.querySelector('[data-category]'), tag: root.querySelector('[data-tag]'), sort: root.querySelector('[data-sort]'), motion: root.querySelector('[data-motion]') };
  var state = root.querySelector('[data-state]');
  var empty = root.querySelector('[data-empty]');
  var grid = root.querySelector('[data-grid]');
  var graph = root.querySelector('[data-graph]');
  var pageSize = 9, page = 1, filtered = cards.slice(), historyOnly = false, savedOnly = false, view = 'briefing';
  var keys = { bookmarks: 'cg.blog.bookmarks.v2', history: 'cg.blog.history.v2', views: 'cg.blog.views.v1' };
  var allowedViews = ['briefing', 'signals', 'archive', 'focus', 'graph'];
  var allowedSorts = ['newest', 'oldest', 'reading-time', 'relevance'];
  var allowedMotion = ['full', 'balanced', 'minimal'];

  function emit(name, detail) {
    root.dispatchEvent(new CustomEvent('cg:analytics', { bubbles: true, detail: Object.assign({ event: name }, detail || {}) }));
    if (Array.isArray(window.dataLayer)) window.dataLayer.push(Object.assign({ event: 'cg_blog_' + name }, detail || {}));
  }
  function announce(message) { if (state) state.textContent = message; }
  function toast(message) { var node = root.querySelector('[data-toast]'); if (!node) return; node.textContent = message; node.setAttribute('data-visible', ''); clearTimeout(node._timer); node._timer = setTimeout(function () { node.removeAttribute('data-visible'); }, 2400); }
  function read(key) { try { var value = JSON.parse(localStorage.getItem(key) || '{"version":2,"items":[]}'); return value && value.version <= 2 && Array.isArray(value.items) ? value.items.filter(function (item) { return typeof item === 'string'; }).slice(0, 100) : []; } catch (_) { return []; } }
  function write(key, items) { try { localStorage.setItem(key, JSON.stringify({ version: 2, items: items.slice(0, 100) })); return true; } catch (_) { toast('Local storage is unavailable.'); return false; } }
  function norm(value) { return (value || '').toLowerCase().normalize ? (value || '').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').trim() : (value || '').toLowerCase().trim(); }
  function safeParam(params, name, maximum) { var value = params.get(name) || ''; return value.length <= maximum ? value : ''; }
  function tokens(value) { return norm(value).split(/[^a-z0-9]+/).filter(Boolean).slice(0, 12); }
  function distance(a, b) { if (Math.abs(a.length - b.length) > 2) return 3; var previous = Array.from({ length: b.length + 1 }, function (_, i) { return i; }); for (var i = 0; i < a.length; i++) { var next = [i + 1]; for (var j = 0; j < b.length; j++) next[j + 1] = Math.min(next[j] + 1, previous[j + 1] + 1, previous[j] + (a[i] === b[j] ? 0 : 1)); previous = next; } return previous[b.length]; }
  function score(card, query) {
    if (!query) return 0;
    var fields = [[card.dataset.title, 8], [card.dataset.summary, 4], [card.dataset.tags, 5], [card.dataset.category, 5], [card.dataset.author, 2], [card.dataset.date, 2]];
    return tokens(query).reduce(function (total, needle) { return total + fields.reduce(function (fieldTotal, field) { var words = tokens(field[0]); var exact = norm(field[0]).indexOf(needle) !== -1; var fuzzy = !exact && needle.length > 3 && words.some(function (word) { return distance(needle, word) <= 1; }); return fieldTotal + (exact ? field[1] : fuzzy ? field[1] / 2 : 0); }, 0); }, 0);
  }
  function validOption(control, value) { return Array.prototype.some.call(control.options, function (option) { return option.value === value || option.text === value; }) ? value : ''; }
  function syncUrl() { if (!history.replaceState) return; var params = new URLSearchParams(); if (controls.search.value) params.set('q', controls.search.value.slice(0, 120)); if (controls.category.value) params.set('category', controls.category.value); if (controls.tag.value) params.set('tag', controls.tag.value); if (controls.sort.value !== 'newest') params.set('sort', controls.sort.value); if (view !== 'briefing') params.set('view', view); if (page > 1) params.set('page', String(page)); history.replaceState(null, '', location.pathname + (params.toString() ? '?' + params.toString() : '') + location.hash); }
  function paintChips() { var host = root.querySelector('[data-active-chips]'); if (!host) return; host.replaceChildren(); [['Query', controls.search.value], ['Category', controls.category.value], ['Tag', controls.tag.value]].forEach(function (pair) { if (!pair[1]) return; var chip = document.createElement('span'); chip.textContent = pair[0] + ': ' + pair[1]; host.appendChild(chip); }); }
  function paintGraph() { var body = root.querySelector('[data-graph-rows]'); if (!body) return; body.replaceChildren(); var groups = new Map(); filtered.forEach(function (card) { norm(card.dataset.tags).split(/\s+/).filter(Boolean).forEach(function (tag) { var key = card.dataset.category + '\u0000' + tag; groups.set(key, (groups.get(key) || 0) + 1); }); }); Array.from(groups.entries()).sort().forEach(function (entry) { var parts = entry[0].split('\u0000'), row = document.createElement('tr'); [parts[0], '#' + parts[1], String(entry[1])].forEach(function (value) { var cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); }); body.appendChild(row); }); }
  function render() {
    var pages = Math.max(1, Math.ceil(filtered.length / pageSize)); page = Math.min(page, pages);
    cards.forEach(function (card) { card.hidden = true; });
    if (view !== 'graph') filtered.slice((page - 1) * pageSize, page * pageSize).forEach(function (card) { card.hidden = false; });
    grid.hidden = view === 'graph'; graph.hidden = view !== 'graph'; if (view === 'graph') paintGraph();
    root.dataset.view = view; root.querySelectorAll('[data-view]').forEach(function (button) { if (button.tagName === 'BUTTON') button.setAttribute('aria-pressed', String(button.dataset.view === view)); });
    var status = root.querySelector('[data-page-status]'); if (status) status.textContent = filtered.length ? 'Page ' + page + ' of ' + pages : 'No results';
    root.querySelector('[data-previous]').disabled = page <= 1 || view === 'graph'; root.querySelector('[data-next]').disabled = page >= pages || view === 'graph';
    empty.hidden = filtered.length !== 0; announce(filtered.length + ' published briefing' + (filtered.length === 1 ? '' : 's') + ' matched.'); paintChips(); syncUrl();
  }
  function apply(reason) {
    var query = controls.search.value.slice(0, 120), cat = norm(controls.category.value), selectedTag = norm(controls.tag.value), visited = read(keys.history), saved = read(keys.bookmarks);
    filtered = cards.filter(function (card) { var rank = score(card, query); card._rank = rank; return (!query || rank > 0) && (!cat || norm(card.dataset.category) === cat) && (!selectedTag || norm(card.dataset.tags).split(/\s+/).indexOf(selectedTag) !== -1) && (!historyOnly || visited.indexOf(card.dataset.slug) !== -1) && (!savedOnly || saved.indexOf(card.dataset.slug) !== -1); });
    filtered.sort(function (a, b) { if (controls.sort.value === 'oldest') return a.dataset.date.localeCompare(b.dataset.date); if (controls.sort.value === 'reading-time') return Number(a.dataset.minutes) - Number(b.dataset.minutes); if (controls.sort.value === 'relevance' || query) return b._rank - a._rank || b.dataset.date.localeCompare(a.dataset.date); return b.dataset.date.localeCompare(a.dataset.date); });
    page = 1; render(); if (reason) emit(reason, { query_length: query.length, category: cat, tag: selectedTag, sort: controls.sort.value, result_count: filtered.length });
  }
  function copy(value, success) { if (!navigator.clipboard) { toast('Clipboard access is unavailable.'); return; } navigator.clipboard.writeText(value).then(function () { toast(success); }, function () { toast('Clipboard access is unavailable.'); }); }
  function setView(next) { if (allowedViews.indexOf(next) === -1) return; view = next; page = 1; render(); emit('view_change', { view: view }); }
  function reset() { controls.search.value = ''; controls.category.value = ''; controls.tag.value = ''; controls.sort.value = 'newest'; historyOnly = savedOnly = false; setView('briefing'); apply('clear'); }
  [controls.search, controls.category, controls.tag, controls.sort].forEach(function (control) { control.addEventListener(control === controls.search ? 'input' : 'change', function () { apply(control === controls.search ? 'search' : 'filter'); }); });
  controls.motion.addEventListener('change', function () { root.dataset.motion = allowedMotion.indexOf(controls.motion.value) >= 0 ? controls.motion.value : 'minimal'; });
  root.addEventListener('click', function (event) {
    var target = event.target.closest('button,a'); if (!target) return;
    if (target.matches('[data-view]')) setView(target.dataset.view);
    if (target.matches('[data-category-filter]')) { controls.category.value = target.dataset.categoryFilter; apply('filter'); controls.category.focus(); }
    if (target.matches('[data-tag-filter]')) { controls.tag.value = target.dataset.tagFilter; apply('filter'); controls.tag.focus(); }
    if (target.matches('[data-reset]')) reset();
    if (target.matches('[data-previous]') && page > 1) { page--; render(); }
    if (target.matches('[data-next]') && page < Math.ceil(filtered.length / pageSize)) { page++; render(); }
    if (target.matches('[data-history-toggle]')) { historyOnly = !historyOnly; target.setAttribute('aria-pressed', String(historyOnly)); apply('filter'); }
    if (target.matches('[data-saved-toggle]')) { savedOnly = !savedOnly; target.setAttribute('aria-pressed', String(savedOnly)); apply('filter'); }
    if (target.matches('[data-share-view]')) copy(location.href, 'Shareable view link copied.');
    if (target.matches('[data-save-view]')) { var views = read(keys.views), snapshot = location.search || '?'; views = views.filter(function (item) { return item !== snapshot; }); views.unshift(snapshot); if (write(keys.views, views)) toast('View saved on this device.'); }
    var tool = target.closest('[data-bookmark],[data-copy-link],[data-share]');
    if (tool) { var card = tool.closest('[data-article-card]'), url = new URL(card.querySelector('h3 a').getAttribute('href'), location.href).href;
      if (tool.hasAttribute('data-bookmark')) { var saved = read(keys.bookmarks), exists = saved.indexOf(card.dataset.slug) >= 0; saved = saved.filter(function (slug) { return slug !== card.dataset.slug; }); if (!exists) saved.unshift(card.dataset.slug); if (write(keys.bookmarks, saved)) { tool.setAttribute('aria-pressed', String(!exists)); tool.textContent = exists ? '☆ Bookmark' : '★ Bookmarked'; toast(exists ? 'Bookmark removed.' : 'Briefing bookmarked locally.'); } }
      if (tool.hasAttribute('data-copy-link')) copy(url, 'Link copied.');
      if (tool.hasAttribute('data-share')) { if (navigator.share) navigator.share({ title: card.dataset.title, url: url }).catch(function () {}); else copy(url, 'Link copied.'); }
    }
    if (target.matches('a[href]')) { var articleCard = target.closest('[data-article-card]'); if (articleCard) { var viewed = read(keys.history).filter(function (slug) { return slug !== articleCard.dataset.slug; }); viewed.unshift(articleCard.dataset.slug); write(keys.history, viewed); } }
  });

  var params = new URLSearchParams(location.search);
  controls.search.value = safeParam(params, 'q', 120); controls.category.value = validOption(controls.category, safeParam(params, 'category', 80)); controls.tag.value = validOption(controls.tag, safeParam(params, 'tag', 80)); controls.sort.value = allowedSorts.indexOf(params.get('sort')) >= 0 ? params.get('sort') : 'newest'; view = allowedViews.indexOf(params.get('view')) >= 0 ? params.get('view') : 'briefing';
  apply(); page = Math.min(Math.max(1, Number(params.get('page')) || 1), Math.max(1, Math.ceil(filtered.length / pageSize))); render();
  var savedOnLoad = read(keys.bookmarks); cards.forEach(function (card) { var button = card.querySelector('[data-bookmark]'); if (savedOnLoad.indexOf(card.dataset.slug) >= 0) { button.setAttribute('aria-pressed', 'true'); button.textContent = '★ Bookmarked'; } });

  var palette = root.querySelector('[data-palette]'), paletteInput = root.querySelector('[data-palette-search]'), results = root.querySelector('[data-palette-results]'), selected = 0;
  function paletteItems(query) { var fixed = [{ title: 'Intelligence archive', url: '#mission-archive', meta: 'Navigate' }, { title: 'Featured briefing', url: '#featured', meta: 'Navigate' }, { title: 'RSS feed', url: 'feed.xml', meta: 'Feed' }]; return fixed.concat(cards.map(function (card) { return { title: card.dataset.title, url: card.querySelector('a').getAttribute('href'), meta: card.dataset.category }; })).filter(function (item) { return !query || score({ dataset: { title: item.title, summary: '', tags: '', category: item.meta, author: '', date: '' } }, query) > 0; }).slice(0, 12); }
  function paintPalette() { results.replaceChildren(); var items = paletteItems(paletteInput.value); selected = Math.min(selected, Math.max(0, items.length - 1)); items.forEach(function (item, index) { var li = document.createElement('li'), link = document.createElement('a'), title = document.createElement('span'), meta = document.createElement('small'); link.href = item.url; title.textContent = item.title; meta.textContent = item.meta; link.append(title, meta); li.appendChild(link); if (index === selected) li.setAttribute('data-active', ''); results.appendChild(li); }); }
  function openPalette() { palette.showModal(); selected = 0; paletteInput.value = ''; paintPalette(); requestAnimationFrame(function () { paletteInput.focus(); }); }
  root.querySelectorAll('[data-open-palette]').forEach(function (button) { button.addEventListener('click', openPalette); }); paletteInput.addEventListener('input', paintPalette);
  document.addEventListener('keydown', function (event) { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); palette.open ? palette.close() : openPalette(); } else if (event.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) { event.preventDefault(); controls.search.focus(); } else if (palette.open && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) { event.preventDefault(); var count = paletteItems(paletteInput.value).length; if (count) { selected = (selected + (event.key === 'ArrowDown' ? 1 : -1) + count) % count; paintPalette(); } } else if (palette.open && event.key === 'Enter' && document.activeElement === paletteInput) { event.preventDefault(); var active = results.querySelector('[data-active] a'); if (active) location.href = active.href; } });

  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches, lowPower = (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4) || (navigator.deviceMemory && navigator.deviceMemory <= 4);
  if (reduced || lowPower) { root.dataset.motion = 'minimal'; controls.motion.value = 'minimal'; }
  var pointerFrame = 0; root.addEventListener('pointermove', function (event) { if (root.dataset.motion === 'minimal' || event.pointerType !== 'mouse') return; cancelAnimationFrame(pointerFrame); pointerFrame = requestAnimationFrame(function () { root.style.setProperty('--pointer-x', event.clientX + 'px'); root.style.setProperty('--pointer-y', event.clientY + 'px'); var card = event.target.closest('[data-article-card]'); if (card && root.dataset.motion === 'full') { var rect = card.getBoundingClientRect(), x = (event.clientX - rect.left) / rect.width - .5, y = (event.clientY - rect.top) / rect.height - .5; card.style.transform = 'perspective(900px) rotateX(' + (-y * 2).toFixed(2) + 'deg) rotateY(' + (x * 2).toFixed(2) + 'deg) translateY(-3px)'; } }); }, { passive: true });
  root.addEventListener('pointerout', function (event) { var card = event.target.closest('[data-article-card]'); if (card && !card.contains(event.relatedTarget)) card.style.transform = ''; });
  function progress() { var max = document.documentElement.scrollHeight - innerHeight; root.style.setProperty('--progress', (max > 0 ? Math.min(100, scrollY / max * 100) : 0) + '%'); root.style.setProperty('--scroll-depth', Math.min(24, scrollY / 80) + 'px'); }
  addEventListener('scroll', progress, { passive: true }); progress();
  var boot = root.querySelector('[data-mission-boot]'); if (boot) setTimeout(function () { boot.setAttribute('data-complete', ''); }, reduced ? 0 : 1200);
}());

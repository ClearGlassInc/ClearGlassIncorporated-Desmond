/* ClearGlass Data Fabric v1
 * Same-origin, read-only runtime for governed /data assets.
 * The catalog is the discovery boundary; arbitrary cross-origin fetches and
 * parent traversal are intentionally rejected.
 */
(function (global) {
  'use strict';

  var CATALOG_URL = '/data/catalog.json';
  var catalogPromise = null;

  function normalizeRelativePath(value) {
    if (typeof value !== 'string' || !value.trim()) {
      throw new TypeError('Data path must be a non-empty string.');
    }
    var path = value.trim().replace(/^\/+/, '');
    var segments = path.split('/');
    if (segments.some(function (segment) { return segment === '..'; })) {
      throw new Error('Parent traversal is not permitted.');
    }
    return segments.filter(Boolean).join('/');
  }

  function dataUrl(relativePath) {
    return '/data/' + normalizeRelativePath(relativePath);
  }

  function parseCsv(text) {
    var rows = [];
    var row = [];
    var field = '';
    var quoted = false;

    for (var i = 0; i < text.length; i += 1) {
      var char = text[i];
      var next = text[i + 1];
      if (char === '"' && quoted && next === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = !quoted;
      } else if (char === ',' && !quoted) {
        row.push(field);
        field = '';
      } else if ((char === '\n' || char === '\r') && !quoted) {
        if (char === '\r' && next === '\n') i += 1;
        row.push(field);
        field = '';
        if (row.some(function (cell) { return cell.length > 0; })) rows.push(row);
        row = [];
      } else {
        field += char;
      }
    }
    if (field.length || row.length) {
      row.push(field);
      rows.push(row);
    }
    return rows;
  }

  function decode(response, path) {
    var lower = path.toLowerCase();
    if (lower.endsWith('.json')) return response.json();
    if (lower.endsWith('.csv')) return response.text().then(parseCsv);
    return response.text();
  }

  function request(relativePath, options) {
    var path = normalizeRelativePath(relativePath);
    var init = Object.assign({ credentials: 'same-origin' }, options || {});
    return fetch(dataUrl(path), init).then(function (response) {
      if (!response.ok) {
        throw new Error('Data request failed: ' + response.status + ' ' + path);
      }
      return decode(response, path);
    });
  }

  function catalog() {
    if (!catalogPromise) {
      catalogPromise = fetch(CATALOG_URL, { credentials: 'same-origin' })
        .then(function (response) {
          if (!response.ok) throw new Error('Data catalog unavailable: ' + response.status);
          return response.json();
        })
        .then(function (value) {
          if (!value || value.schema !== 'clearglass.data-fabric/v1') {
            throw new Error('Unsupported ClearGlass data catalog schema.');
          }
          return value;
        });
    }
    return catalogPromise;
  }

  function rootDataset(id) {
    return catalog().then(function (value) {
      var dataset = value.rootDatasets.find(function (item) { return item.id === id; });
      if (!dataset) throw new Error('Unknown root dataset: ' + id);
      if (dataset.browserLoad === false) throw new Error('Browser loading is disabled for: ' + id);
      return request(dataset.path);
    });
  }

  function moduleAsset(moduleId, relativePath) {
    return catalog().then(function (value) {
      var module = value.modules.find(function (item) { return item.id === moduleId; });
      if (!module) throw new Error('Unknown data module: ' + moduleId);
      if (module.browserLoad === false) throw new Error('Browser loading is disabled for module: ' + moduleId);
      var path = normalizeRelativePath(relativePath);
      return request(module.root + '/' + path);
    });
  }

  function probe(relativePath) {
    var path = normalizeRelativePath(relativePath);
    return fetch(dataUrl(path), {
      method: 'GET',
      cache: 'no-store',
      credentials: 'same-origin'
    }).then(function (response) {
      return { path: path, ok: response.ok, status: response.status };
    }).catch(function (error) {
      return { path: path, ok: false, status: 0, error: String(error && error.message || error) };
    });
  }

  function health() {
    return catalog().then(function (value) {
      var required = value.rootDatasets
        .filter(function (item) { return item.browserLoad !== false; })
        .map(function (item) { return item.path; });
      required.unshift('catalog.json');
      return Promise.all(required.map(probe)).then(function (checks) {
        return {
          ok: checks.every(function (check) { return check.ok; }),
          checkedAt: new Date().toISOString(),
          checks: checks,
          moduleCount: value.modules.length,
          rootDatasetCount: value.rootDatasets.length
        };
      });
    });
  }

  var api = Object.freeze({
    version: '1.0.0',
    catalog: catalog,
    load: request,
    loadRoot: rootDataset,
    loadModuleAsset: moduleAsset,
    health: health
  });

  Object.defineProperty(global, 'ClearGlassDataFabric', {
    value: api,
    configurable: false,
    enumerable: true,
    writable: false
  });

  global.dispatchEvent(new CustomEvent('clearglass:data-fabric-ready', { detail: { version: api.version } }));
})(window);

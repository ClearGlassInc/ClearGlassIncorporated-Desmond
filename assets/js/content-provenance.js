/* ClearGlass public text-provenance helper.
   This browser layer intentionally contains no signing secret. It creates
   removable source markers only; signed provenance is produced by Node tooling. */
(function (global) {
  'use strict';
  var ZERO = '\u200B';
  var ONE = '\u200C';
  var START = '\u2063\u2063\u200B\u200C';
  var END = '\u2063\u2063\u200C\u200B';

  function encodeUtf8(text) {
    return new TextEncoder().encode(text);
  }

  function decodeUtf8(bytes) {
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  }

  function bytesToHidden(bytes) {
    var out = '';
    for (var i = 0; i < bytes.length; i += 1) {
      for (var bit = 7; bit >= 0; bit -= 1) out += (bytes[i] & (1 << bit)) ? ONE : ZERO;
    }
    return out;
  }

  function hiddenToBytes(hidden) {
    if (!hidden || hidden.length % 8 !== 0) return null;
    var bytes = new Uint8Array(hidden.length / 8);
    for (var i = 0; i < hidden.length; i += 8) {
      var value = 0;
      for (var bit = 0; bit < 8; bit += 1) {
        var ch = hidden[i + bit];
        if (ch !== ZERO && ch !== ONE) return null;
        value = (value << 1) | (ch === ONE ? 1 : 0);
      }
      bytes[i / 8] = value;
    }
    return bytes;
  }

  function createPublicMarker(contentId) {
    var envelope = JSON.stringify({ v: 1, m: 'public-source', id: String(contentId || '') });
    return START + bytesToHidden(encodeUtf8(envelope)) + END;
  }

  function extract(text) {
    var found = [];
    var cursor = 0;
    while (cursor < text.length) {
      var start = text.indexOf(START, cursor);
      if (start === -1) break;
      var dataStart = start + START.length;
      var end = text.indexOf(END, dataStart);
      if (end === -1) break;
      try {
        var bytes = hiddenToBytes(text.slice(dataStart, end));
        if (bytes) found.push(JSON.parse(decodeUtf8(bytes)));
      } catch (e) { /* malformed marker */ }
      cursor = end + END.length;
    }
    return found;
  }

  function strip(text) {
    var out = String(text || '');
    var cursor = 0;
    while (cursor < out.length) {
      var start = out.indexOf(START, cursor);
      if (start === -1) break;
      var end = out.indexOf(END, start + START.length);
      if (end === -1) break;
      out = out.slice(0, start) + out.slice(end + END.length);
      cursor = start;
    }
    return out;
  }

  function applyPublicAttribution(selector, contentId) {
    var root = document.querySelector(selector);
    if (!root) return 0;
    var marker = createPublicMarker(contentId || location.pathname);
    var nodes = root.querySelectorAll('p, li, blockquote');
    var applied = 0;
    for (var i = 0; i < nodes.length; i += 1) {
      var node = nodes[i];
      if ((node.textContent || '').trim().length < 80 || node.dataset.cgProvenance === '1') continue;
      node.appendChild(document.createTextNode(marker));
      node.dataset.cgProvenance = '1';
      applied += 1;
    }
    return applied;
  }

  global.ClearGlassProvenance = Object.freeze({
    createPublicMarker: createPublicMarker,
    extract: extract,
    strip: strip,
    applyPublicAttribution: applyPublicAttribution
  });
})(window);

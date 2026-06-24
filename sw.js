/* ClearGlass · service worker — offline resilience + fast repeat visits.
   Strategy:
     • HTML  → network-first (always fresh), cached copy as fallback,
               offline.html as the last resort
     • CSS/JS/fonts/images (same-origin) → stale-while-revalidate
     • cross-origin (live data APIs, CDNs) → untouched: network only, never
       cached, so live feeds stay live and never serve stale intel
   Bump VERSION to invalidate all caches on deploy. */
"use strict";

var VERSION = "cg-v11";
var PRECACHE = [
  "/",
  "/index.html",
  "/offline.html",
  "/tokens.css",
  "/theme.css",
  "/buttons.css",
  "/ui.css",
  "/ui.js",
  "/control-surface.js",
  "/platform.js",
  "/nav.js",
  "/Ontario-osint.html",
  "/data/Ontario-osint/intel.json",
  "/icon.svg",
  "/manifest.webmanifest"
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(VERSION).then(function (c) {
      // best-effort precache: one missing asset must not break install
      return Promise.all(PRECACHE.map(function (u) {
        return c.add(u).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== VERSION; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   // live APIs/CDNs: hands off

  var isHTML = req.mode === "navigate" ||
    (req.headers.get("accept") || "").indexOf("text/html") > -1;

  if (isHTML) {
    // network-first: fresh page when online, cache then offline page when not
    e.respondWith(
      fetch(req).then(function (res) {
        var copy = res.clone();
        caches.open(VERSION).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match("/offline.html");
        });
      })
    );
    return;
  }

  // static assets: stale-while-revalidate
  e.respondWith(
    caches.match(req).then(function (hit) {
      var refresh = fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(VERSION).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return hit; });
      return hit || refresh;
    })
  );
});

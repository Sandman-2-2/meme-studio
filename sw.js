// Meme Studio service worker: offline app shell, cached templates, update notifications.
const VERSION = "2026-11-19.3";
const SHELL = `shell-${VERSION}`, IMGS = "imgs-v1", FONTS = "fonts-v1", API = "api-v1";
const SHELL_FILES = ["./", "./index.html", "./manifest.webmanifest", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png", "./favicon-32.png"];
const IMG_LIMIT = 250;

self.addEventListener("install", e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).catch(() => {}));
});
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith("shell-") && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});
self.addEventListener("message", e => { if (e.data === "skipWaiting") self.skipWaiting(); });

async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const res = await fetch(req);
    if (res && res.ok && res.type !== "opaque") cache.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(req, { ignoreSearch: req.mode === "navigate" }) || (req.mode === "navigate" && await cache.match("./index.html"));
    if (hit) return hit;
    throw err;
  }
}
async function cacheFirst(req, cacheName, limit) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res && res.ok && res.type !== "opaque") {
    await cache.put(req, res.clone());
    if (limit) { const keys = await cache.keys(); for (const k of keys.slice(0, Math.max(0, keys.length - limit))) await cache.delete(k); }
  }
  return res;
}
async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  const net = fetch(req).then(res => { if (res && res.ok && res.type !== "opaque") cache.put(req, res.clone()); return res; }).catch(() => hit);
  return hit || net;
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.hostname === "generativelanguage.googleapis.com") return; // never cache AI calls
  if (url.origin === self.location.origin) return e.respondWith(networkFirst(req, SHELL));
  if (url.hostname === "i.imgflip.com") {
    // Only CORS (non-opaque) responses are stored, so canvas export always works from cache.
    if (req.mode === "cors") return e.respondWith(cacheFirst(req, IMGS, IMG_LIMIT));
    return;
  }
  if (url.hostname === "api.imgflip.com") return e.respondWith(networkFirst(req, API));
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") return e.respondWith(staleWhileRevalidate(req, FONTS));
});

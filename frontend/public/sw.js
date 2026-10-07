/* global self, caches, URL, location, fetch */
// Installable shell only. Never cache API responses, uploads, PDF or user images.
const cacheName = "wusheng-shell-v2";
self.addEventListener("install", event => event.waitUntil(self.skipWaiting()));
self.addEventListener("activate", event => event.waitUntil((async () => {
  for (const key of await caches.keys()) if (key.startsWith("wusheng-shell-") && key !== cacheName) await caches.delete(key);
  await self.clients.claim();
})()));
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== location.origin || !/^\/assets\/[^/]+\.(js|css)$/.test(url.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(cacheName);
    const existing = await cache.match(event.request);
    if (existing) return existing;
    const response = await fetch(event.request);
    if (response.ok) await cache.put(event.request, response.clone());
    return response;
  })());
});

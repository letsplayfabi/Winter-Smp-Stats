// Minimaler Service Worker: macht die Seite als App installierbar, cached aber nichts (Statistiken sollen immer frisch sein).
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});

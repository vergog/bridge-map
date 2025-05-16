const CACHE_NAME = "bridge-inspection-cache-v1";
const urlsToCache = [
  "./Bridge Inspection Map.html",
  "./static/js/map.js",
  "./static/css/style.css",
  "./data/bridges.json",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
  "https://cdn.jsdelivr.net/npm/leaflet.awesome-markers@2.0.5/dist/leaflet.awesome-markers.min.js"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});

/* History's Ledger — cache the ledger for offline reading.
   Atticus and the Family waitlist stay on the network. */
var CACHE = "hl-ledger-v1";

var PRECACHE = [
  "/",
  "/index.html",
  "/family",
  "/family/",
  "/family.html",
  "/app.css",
  "/app.js",
  "/manifest.webmanifest",
  "/favicon.png",
  "/apple-touch-icon.png",
  "/brand/hl-seal-red-256.png",
  "/brand/hl-seal-red-cut.png",
  "/brand/bg-books-shelf.jpg",
  "/brand/bg-ledger-page.jpg",
  "/read/",
  "/read/01-the-founding.html",
  "/read/02-slavery-and-emancipation.html",
  "/read/03-reconstruction.html",
  "/read/04-standard-oil.html",
  "/read/05-civil-rights.html",
  "/read/06-cold-war.html",
  "/read/07-the-bullet-and-the-podium.html",
  "/read/modern-wars/",
  "/read/modern-wars/01-how-europe-walked-in.html",
  "/read/modern-wars/01-world-war-ii.html"
];

function isNetworkOnly(url) {
  if (url.hostname === "atticus.historysledger.com") return true;
  if (url.pathname === "/chat" || url.pathname === "/waitlist") return true;
  if (url.pathname.indexOf("/waitlist") === 0) return true;
  return false;
}

function isFont(url) {
  return (
    url.hostname === "fonts.googleapis.com" ||
    url.hostname === "fonts.gstatic.com"
  );
}

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return Promise.all(
        PRECACHE.map(function (url) {
          return cache.add(url).catch(function () {
            /* pretty-url variants may 404 on some hosts; ignore */
          });
        })
      );
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (k) {
            return k !== CACHE;
          })
          .map(function (k) {
            return caches.delete(k);
          })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

self.addEventListener("fetch", function (event) {
  var req = event.request;
  var url = new URL(req.url);

  if (isNetworkOnly(url)) return;
  if (req.method !== "GET") return;
  if (url.pathname.indexOf("/cdn-cgi/") === 0) return;

  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(req));
    return;
  }

  if (isFont(url)) {
    event.respondWith(staleWhileRevalidate(req));
  }
});

function cacheFirst(req) {
  return caches.open(CACHE).then(function (cache) {
    return cache.match(req, { ignoreSearch: true }).then(function (hit) {
      if (hit) return hit;
      return fetch(req)
        .then(function (res) {
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        })
        .catch(function () {
          var path = new URL(req.url).pathname;
          if (path === "/family" || path === "/family/") {
            return cache.match("/family.html").then(function (alt) {
              return alt || cache.match("/family/");
            });
          }
          if (path === "/" || path === "/index.html") {
            return cache.match("/index.html").then(function (alt) {
              return alt || cache.match("/");
            });
          }
          if (path === "/read/" || path === "/read") {
            return cache.match("/read/");
          }
          if (path === "/read/modern-wars/" || path === "/read/modern-wars") {
            return cache.match("/read/modern-wars/");
          }
        });
    });
  });
}

function staleWhileRevalidate(req) {
  return caches.open(CACHE).then(function (cache) {
    return cache.match(req).then(function (hit) {
      var fetched = fetch(req)
        .then(function (res) {
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        })
        .catch(function () {
          return hit;
        });
      return hit || fetched;
    });
  });
}

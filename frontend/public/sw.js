// Self-destructing service worker: clears all caches and unregisters itself.
// This ensures stale cached content from previous deployments is purged.
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => Promise.all(names.map((n) => caches.delete(n))))
      .then(() => self.registration.unregister())
      .then(() => self.clients.matchAll()).then((clients) => {
        clients.forEach((client) => client.navigate(client.url))
      })
  )
})

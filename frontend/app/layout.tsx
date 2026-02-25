import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from './providers'

export const viewport: Viewport = {
  themeColor: '#0f172a',
}

export const metadata: Metadata = {
  title: 'NBNE Platform',
  description: 'Three-tier business management platform',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'NBNE',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body>
        <script dangerouslySetInnerHTML={{ __html: `
          // Nuke all service workers and caches on every load
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(function(regs) {
              regs.forEach(function(r) { r.unregister(); });
            });
          }
          if ('caches' in window) {
            caches.keys().then(function(names) {
              names.forEach(function(n) { caches.delete(n); });
            });
          }
          // Monkey-patch fetch to cache-bust ALL /api/ requests.
          // This runs BEFORE React hydrates, so even old cached JS bundles
          // will have their API calls cache-busted, defeating Chrome HTTP cache.
          (function() {
            var _origFetch = window.fetch;
            window.fetch = function(input, init) {
              var url = (typeof input === 'string') ? input : (input && input.url ? input.url : '');
              if (url.indexOf('/api/') !== -1) {
                var sep = url.indexOf('?') !== -1 ? '&' : '?';
                var busted = url + sep + '_cb=' + Date.now();
                init = Object.assign({}, init || {}, { cache: 'no-store' });
                console.log('[FETCH-PATCH]', busted.substring(0, 150));
                return _origFetch.call(this, busted, init).then(function(resp) {
                  if (url.indexOf('staff') !== -1) {
                    resp.clone().text().then(function(t) {
                      console.log('[STAFF-RESP]', t.substring(0, 200));
                    });
                  }
                  return resp;
                });
              }
              return _origFetch.call(this, input, init);
            };
          })();
        `}} />
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}

const CACHE_NAME = 'rocket-dashboard-v1';
const urlsToCache = [
  '/',              // Caches your index.html (served from root)
  '/dashboard',     // Caches your dashboard.html (served from /dashboard)
  '/manifest.json', // Caches your manifest file (served from /manifest.json route)

  // All static assets need paths relative to the domain root
  '/static/css/lib/leaflet.css',
  '/static/js/lib/chart.min.js',
  // ... (add all other specific static files from your dashboard.html and index.html)
  '/static/imgs/logo.png',
  '/static/images/marker-icon.png', // Example, check Leaflet actual paths if different
  '/static/models/rocket.glb',
  '/static/stars.js'
  // IMPORTANT: Add any CSS, JS, or images *specifically used by index.html* if they aren't already covered by your dashboard assets.
];

// ... (rest of your service worker code - install, fetch, activate listeners) ...
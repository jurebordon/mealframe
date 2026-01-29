const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  // Cache strategies
  runtimeCaching: [
    {
      // Cache API responses for /today endpoint (primary daily use)
      urlPattern: /^https?:\/\/.*\/api\/v1\/today$/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'today-api-cache',
        expiration: {
          maxEntries: 1,
          maxAgeSeconds: 60 * 60, // 1 hour
        },
        networkTimeoutSeconds: 10,
      },
    },
    {
      // Cache other API responses with stale-while-revalidate
      urlPattern: /^https?:\/\/.*\/api\/v1\/.*/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 60 * 60 * 24, // 24 hours
        },
      },
    },
    {
      // Cache static assets
      urlPattern: /\.(?:js|css|woff2?)$/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'static-assets',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
        },
      },
    },
    {
      // Cache images
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/i,
      handler: 'CacheFirst',
      options: {
        cacheName: 'images',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
        },
      },
    },
  ],
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Standalone output for Docker production builds
  output: 'standalone',

  // Transpile packages that might have issues
  transpilePackages: ['lucide-react'],
}

module.exports = withPWA(nextConfig)

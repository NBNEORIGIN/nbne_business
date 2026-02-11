/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  skipTrailingSlashRedirect: true,
  async rewrites() {
    return [
      {
        source: '/api/django/:path*',
        destination: 'https://nbnebusiness-production-6853.up.railway.app/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig

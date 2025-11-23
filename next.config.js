/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost'],
  },
  experimental: {
    serverActions: {
      bodySizeLimit: '500mb',
    },
  },
  async rewrites() {
    return [
      {
        source: '/api/python/:path*',
        destination: process.env.PYTHON_API_URL || 'http://127.0.0.1:8000/:path*',
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/api/python/:path*',
        headers: [
          { key: 'Connection', value: 'keep-alive' },
          { key: 'Keep-Alive', value: 'timeout=600' },
        ],
      },
    ];
  },
}

module.exports = nextConfig

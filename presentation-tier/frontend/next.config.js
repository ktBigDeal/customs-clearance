/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    typedRoutes: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8080',
        pathname: '/api/**',
      },
      {
        protocol: 'https',
        hostname: '*.amazonaws.com',
        pathname: '/**',
      },
    ],
  },
  async rewrites() {
    // 프로덕션에서는 직접 백엔드 API 호출 (Vercel에서는 rewrites 사용 안 함)
    if (process.env.NODE_ENV === 'production') {
      return [];
    }
    
    // 개발 환경에서만 rewrites 사용
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_URL || 'http://localhost:8080'}/api/:path*`,
      },
    ];
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8080',
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:3000/api',
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  eslint: {
    ignoreDuringBuilds: true,  // 빌드 시 ESLint 에러 무시
  },
  typescript: {
    ignoreBuildErrors: true,   // TypeScript 에러도 무시 (안전장치)
  },
  poweredByHeader: false,
  reactStrictMode: true,
  swcMinify: true,
};

module.exports = nextConfig;
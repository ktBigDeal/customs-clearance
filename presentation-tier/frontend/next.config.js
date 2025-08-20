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
      {
        protocol: 'https',
        hostname: '*.run.app',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '*.railway.app',
        pathname: '/**',
      },
    ],
  },
  async rewrites() {
    const rewrites = [
      // Java Backend API (Railway)
      {
        source: '/api/auth/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://customs-backend-java.up.railway.app'}/api/auth/:path*`,
      },
      {
        source: '/api/admin/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://customs-backend-java.up.railway.app'}/api/admin/:path*`,
      },
      {
        source: '/api/user/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://customs-backend-java.up.railway.app'}/api/user/:path*`,
      },
      
      // AI Gateway (Cloud Run)
      {
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_AI_GATEWAY_URL || 'https://ai-gateway-service-805290929724.asia-northeast3.run.app'}/api/v1/:path*`,
      },
    ];

    // 선택적으로 Cloud Run 서비스 추가 (환경변수가 설정된 경우에만)
    if (process.env.CLOUD_RUN_OCR_URL) {
      rewrites.push({
        source: '/api/ocr/:path*',
        destination: `${process.env.CLOUD_RUN_OCR_URL}/:path*`,
      });
    }

    if (process.env.CLOUD_RUN_REPORT_URL) {
      rewrites.push({
        source: '/api/report/:path*',
        destination: `${process.env.CLOUD_RUN_REPORT_URL}/:path*`,
      });
    }

    if (process.env.CLOUD_RUN_CHATBOT_URL) {
      rewrites.push({
        source: '/api/chatbot/:path*',
        destination: `${process.env.CLOUD_RUN_CHATBOT_URL}/:path*`,
      });
    }

    return rewrites;
  },
  env: {
    // 서버사이드에서 사용할 환경변수들 (안전한 기본값 포함)
    CLOUD_RUN_GATEWAY_URL: process.env.CLOUD_RUN_GATEWAY_URL || process.env.NEXT_PUBLIC_AI_GATEWAY_URL,
    CLOUD_RUN_OCR_URL: process.env.CLOUD_RUN_OCR_URL,
    CLOUD_RUN_REPORT_URL: process.env.CLOUD_RUN_REPORT_URL,
    CLOUD_RUN_CHATBOT_URL: process.env.CLOUD_RUN_CHATBOT_URL,
    HSCODE_URL: process.env.HSCODE_URL,
    HSCODE_CONVERT_URL: process.env.HSCODE_CONVERT_URL,
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  poweredByHeader: false,
  reactStrictMode: true,
  swcMinify: true,
};

module.exports = nextConfig;

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
    // 🔧 디버깅 코드 추가 (여기에 넣으세요)
    console.log('🔍 Environment Variables Check:');
    console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://customs-backend-java.up.railway.app';
    console.log('🎯 Final API URL:', apiUrl);
    
    const rewrites = [
      // Java Backend API (Railway) - 모든 /api/v1 요청을 Railway로
      {
        source: '/api/v1/:path*',
        destination: `${apiUrl}/api/v1/:path*`,
      },
      // AI Gateway (Cloud Run) - 특정 AI 서비스들만
      {
        source: '/api/ai/:path*',
        destination: `${process.env.NEXT_PUBLIC_AI_GATEWAY_URL || 'https://ai-gateway-service-805290929724.asia-northeast3.run.app'}/api/v1/:path*`,
      },
    ];

    console.log('📋 Generated Rewrites:', JSON.stringify(rewrites, null, 2));
    
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

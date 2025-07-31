import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';
import { Inter, Noto_Sans_KR } from 'next/font/google';
import { Toaster } from 'react-hot-toast';

import '@/styles/globals.css';
import { cn } from '@/lib/utils';
import { QueryProvider } from '@/components/providers/query-provider';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const notoSansKR = Noto_Sans_KR({
  subsets: ['latin'],
  variable: '--font-noto-sans-kr',
  display: 'swap',
});

export const metadata = {
  title: {
    default: '관세청 통관 시스템',
    template: '%s | 관세청 통관 시스템',
  },
  description: '한국관세청 전자통관 시스템 - 수출입 신고서 처리 및 관리',
  keywords: ['관세청', '통관', '수출입', '신고서', '전자통관'],
  authors: [{ name: '관세청 IT팀' }],
  creator: '한국관세청',
  publisher: '한국관세청',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  openGraph: {
    title: '관세청 통관 시스템',
    description: '한국관세청 전자통관 시스템 - 수출입 신고서 처리 및 관리',
    type: 'website',
    locale: 'ko_KR',
    siteName: '관세청 통관 시스템',
  },
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} className={cn(inter.variable, notoSansKR.variable)}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <NextIntlClientProvider messages={messages}>
          <QueryProvider>
            <div className="relative flex min-h-screen flex-col">
              <div className="flex-1">{children}</div>
            </div>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10b981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          </QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
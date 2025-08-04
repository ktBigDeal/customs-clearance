// Use the default Pages Router 404 page for non-matching locales
export default function GlobalNotFound() {
  return (
    <html>
      <body>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl font-bold text-blue-600 mb-4">404</div>
            <div className="text-xl text-gray-600 mb-4">페이지를 찾을 수 없습니다</div>
            <a
              href="/ko"
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              홈으로 돌아가기
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
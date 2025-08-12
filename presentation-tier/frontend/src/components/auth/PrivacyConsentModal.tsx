'use client';

interface PrivacyConsentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgree: () => void;
}

export function PrivacyConsentModal({ isOpen, onClose, onAgree }: PrivacyConsentModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              개인정보 수집·이용 동의서
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="space-y-6 text-sm text-gray-700">
            {/* 수집 목적 */}
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">1. 개인정보 수집·이용 목적</h3>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <ul className="space-y-2">
                  <li>• <strong>회원가입 및 본인확인:</strong> 서비스 이용을 위한 회원 식별 및 인증</li>
                  <li>• <strong>통관업무 서비스 제공:</strong> 수출입신고서 작성, HS코드 분류, 관세계산 등</li>
                  <li>• <strong>고객지원:</strong> 문의사항 답변, 불만처리, 공지사항 전달</li>
                  <li>• <strong>서비스 개선:</strong> 이용 패턴 분석을 통한 서비스 품질 향상</li>
                  <li>• <strong>법정의무 이행:</strong> 관세법령에 따른 통관업무 처리</li>
                </ul>
              </div>
            </section>

            {/* 수집 항목 */}
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">2. 수집하는 개인정보 항목</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2 text-gray-800">필수 정보</h4>
                  <ul className="space-y-1">
                    <li>• 아이디</li>
                    <li>• 비밀번호</li>
                    <li>• 이름</li>
                    <li>• 이메일 주소</li>
                  </ul>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2 text-gray-800">선택 정보</h4>
                  <ul className="space-y-1">
                    <li>• 회사명</li>
                    <li>• 연락처 (추후 입력 가능)</li>
                  </ul>
                </div>
              </div>
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-yellow-800 text-sm">
                  <strong>자동 수집 정보:</strong> 접속 IP주소, 쿠키, 접속 로그, 서비스 이용 기록
                </p>
              </div>
            </section>

            {/* 보유 기간 */}
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">3. 개인정보 보유·이용 기간</h3>
              <div className="overflow-x-auto">
                <table className="w-full border border-gray-300 text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border border-gray-300 p-3 text-left">정보 구분</th>
                      <th className="border border-gray-300 p-3 text-left">보유 기간</th>
                      <th className="border border-gray-300 p-3 text-left">근거</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-300 p-3">회원 기본정보</td>
                      <td className="border border-gray-300 p-3">회원 탈퇴시까지</td>
                      <td className="border border-gray-300 p-3">서비스 제공</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 p-3">통관업무 관련 기록</td>
                      <td className="border border-gray-300 p-3">5년</td>
                      <td className="border border-gray-300 p-3">관세법 시행령 제292조</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 p-3">접속 로그</td>
                      <td className="border border-gray-300 p-3">6개월</td>
                      <td className="border border-gray-300 p-3">통신비밀보호법</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* 동의 거부권 */}
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">4. 개인정보 수집·이용 동의 거부권</h3>
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <p className="text-red-800">
                  귀하는 개인정보 수집·이용에 동의하지 않을 권리가 있습니다. 
                  다만, 필수 정보 수집에 동의하지 않으실 경우 회원가입 및 서비스 이용이 제한될 수 있습니다.
                </p>
              </div>
            </section>

            {/* 개인정보 처리 위탁 */}
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">5. 개인정보 처리 위탁</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="mb-3">관세청 통관시스템은 서비스 제공을 위해 다음과 같이 개인정보 처리를 위탁합니다.</p>
                <div className="overflow-x-auto">
                  <table className="w-full border border-gray-300 text-xs">
                    <thead className="bg-gray-200">
                      <tr>
                        <th className="border border-gray-300 p-2 text-left">수탁업체</th>
                        <th className="border border-gray-300 p-2 text-left">위탁업무</th>
                        <th className="border border-gray-300 p-2 text-left">보유기간</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="border border-gray-300 p-2">시스템 운영업체</td>
                        <td className="border border-gray-300 p-2">IT시스템 운영·유지보수</td>
                        <td className="border border-gray-300 p-2">위탁계약 종료시까지</td>
                      </tr>
                      <tr>
                        <td className="border border-gray-300 p-2">클라우드 서비스 업체</td>
                        <td className="border border-gray-300 p-2">데이터 저장·백업</td>
                        <td className="border border-gray-300 p-2">서비스 이용계약 종료시까지</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            {/* 연락처 정보 */}
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">6. 개인정보 보호책임자 연락처</h3>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p><strong>개인정보보호책임자:</strong></p>
                    <ul className="mt-1 space-y-1 text-blue-700">
                      <li>• 관세청 정보통신담당관</li>
                      <li>• 전화: 042-481-7777</li>
                      <li>• 이메일: privacy@customs.go.kr</li>
                    </ul>
                  </div>
                  <div>
                    <p><strong>개인정보보호담당자:</strong></p>
                    <ul className="mt-1 space-y-1 text-blue-700">
                      <li>• 시스템 관리팀</li>
                      <li>• 전화: 042-481-7890</li>
                      <li>• 이메일: system@customs.go.kr</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* 고지일자 */}
            <section className="border-t pt-4">
              <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                <p className="text-yellow-800 text-center text-sm">
                  <strong>본 동의서는 2025년 1월 1일부터 시행됩니다.</strong>
                </p>
              </div>
            </section>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-6 py-4 rounded-b-lg">
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors"
            >
              동의하지 않음
            </button>
            <button
              onClick={onAgree}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 transition-colors"
            >
              동의함
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
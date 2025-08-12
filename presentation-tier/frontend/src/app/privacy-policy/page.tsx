'use client';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">개인정보처리방침</h1>
          
          <div className="space-y-8 text-gray-700">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제1조 (개인정보의 처리목적)</h2>
              <p className="mb-4">
                관세청 통관시스템(이하 "시스템")은 다음의 목적을 위하여 개인정보를 처리합니다. 
                처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 
                이용 목적이 변경되는 경우에는 개인정보보호법 제18조에 따라 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.
              </p>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>통관업무 처리 및 수출입신고서 관리</li>
                <li>관세 및 세금 계산, 징수업무</li>
                <li>사용자 인증 및 서비스 제공</li>
                <li>고객상담 및 민원처리</li>
                <li>법정의무 이행 및 관세행정 업무</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제2조 (개인정보의 처리 및 보유기간)</h2>
              <p className="mb-4">
                시스템은 법령에 따른 개인정보 보유·이용기간 또는 정보주체로부터 개인정보를 수집 시에 
                동의받은 개인정보 보유·이용기간 내에서 개인정보를 처리·보유합니다.
              </p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">주요 개인정보 보유기간</h3>
                <ul className="space-y-1">
                  <li>• 통관신고서류: 5년 (관세법 시행령 제292조)</li>
                  <li>• 사용자 계정정보: 회원탈퇴 시까지</li>
                  <li>• 상담기록: 3년</li>
                  <li>• 접속로그: 6개월</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제3조 (개인정보의 제3자 제공)</h2>
              <p className="mb-4">
                시스템은 정보주체의 개인정보를 제1조(개인정보의 처리목적)에서 명시한 범위 내에서만 처리하며, 
                정보주체의 동의, 법률의 특별한 규정 등 개인정보보호법 제17조에 해당하는 경우에만 개인정보를 제3자에게 제공합니다.
              </p>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h3 className="font-semibold mb-2 text-blue-800">법정 제3자 제공 기관</h3>
                <ul className="space-y-1 text-blue-700">
                  <li>• 관세청 본청 및 세관</li>
                  <li>• 국세청 (세무조사 목적)</li>
                  <li>• 검찰, 경찰 (수사목적)</li>
                  <li>• 기타 법령에 의한 요청기관</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제4조 (개인정보처리의 위탁)</h2>
              <p className="mb-4">
                시스템은 원활한 개인정보 업무처리를 위하여 다음과 같이 개인정보 처리업무를 위탁하고 있습니다.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full border border-gray-300">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="border border-gray-300 p-3 text-left">위탁업체</th>
                      <th className="border border-gray-300 p-3 text-left">위탁업무</th>
                      <th className="border border-gray-300 p-3 text-left">보유기간</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-300 p-3">시스템 운영업체</td>
                      <td className="border border-gray-300 p-3">IT시스템 운영 및 유지보수</td>
                      <td className="border border-gray-300 p-3">위탁계약 종료시까지</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 p-3">클라우드 서비스 제공업체</td>
                      <td className="border border-gray-300 p-3">데이터 저장 및 백업</td>
                      <td className="border border-gray-300 p-3">서비스 이용계약 종료시까지</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제5조 (정보주체의 권리·의무 및 행사방법)</h2>
              <p className="mb-4">
                정보주체는 개인정보보호법에 따라 다음과 같은 권리를 행사할 수 있습니다.
              </p>
              <ul className="list-disc list-inside ml-4 space-y-2 mb-4">
                <li>개인정보 처리현황 통지요구</li>
                <li>개인정보 열람요구</li>
                <li>개인정보 정정·삭제요구</li>
                <li>개인정보 처리정지 요구</li>
              </ul>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-green-800">
                  <strong>권리행사 방법:</strong> 개인정보보호법 시행규칙 별지 제8호 서식에 따라 작성 후 
                  관세청 개인정보보호 담당자에게 서면, 전화, 전자우편, 모사전송(FAX) 등을 통하여 요청하실 수 있습니다.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제6조 (개인정보의 안전성 확보조치)</h2>
              <p className="mb-4">
                시스템은 개인정보의 안전성 확보를 위해 다음과 같은 조치를 취하고 있습니다.
              </p>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">기술적 조치</h3>
                  <ul className="space-y-1 text-sm">
                    <li>• 개인정보처리시스템 등의 접근권한 관리</li>
                    <li>• 개인정보의 암호화</li>
                    <li>• 해킹 등에 대비한 기술적 대책</li>
                    <li>• 개인정보처리시스템 접속기록 보관</li>
                  </ul>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">관리적 조치</h3>
                  <ul className="space-y-1 text-sm">
                    <li>• 개인정보 취급직원의 최소화 및 교육</li>
                    <li>• 개인정보 보호책임자 등의 지정</li>
                    <li>• 정기적인 점검 및 내부관리계획 수립</li>
                    <li>• 개인정보 취급 현황 점검</li>
                  </ul>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제7조 (개인정보보호 책임자)</h2>
              <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-2 text-blue-800">개인정보보호 책임자</h3>
                    <ul className="space-y-1 text-blue-700">
                      <li>성명: 관세청 정보통신담당관</li>
                      <li>직책: 과장</li>
                      <li>연락처: 042-481-7777</li>
                      <li>이메일: privacy@customs.go.kr</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2 text-blue-800">개인정보보호 담당자</h3>
                    <ul className="space-y-1 text-blue-700">
                      <li>성명: 시스템 관리팀</li>
                      <li>부서: 통관정보과</li>
                      <li>연락처: 042-481-7890</li>
                      <li>이메일: system@customs.go.kr</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제8조 (권익침해 구제방법)</h2>
              <p className="mb-4">
                정보주체는 아래의 기관에 대해 개인정보 침해신고를 접수하거나 상담을 받을 수 있습니다.
              </p>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <h3 className="font-semibold mb-2">개인정보보호위원회</h3>
                  <p className="text-sm">개인정보보호 종합지원 포털</p>
                  <p className="text-blue-600 font-medium">privacy.go.kr</p>
                  <p className="text-sm">전화: 국번없이 125</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <h3 className="font-semibold mb-2">개인정보보호 전문기관</h3>
                  <p className="text-sm">한국인터넷진흥원</p>
                  <p className="text-blue-600 font-medium">privacy.kisa.or.kr</p>
                  <p className="text-sm">전화: 국번없이 118</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <h3 className="font-semibold mb-2">대검찰청</h3>
                  <p className="text-sm">사이버범죄수사단</p>
                  <p className="text-blue-600 font-medium">spo.go.kr</p>
                  <p className="text-sm">전화: 02-3480-3571</p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">제9조 (개인정보처리방침 변경)</h2>
              <p className="mb-4">
                이 개인정보처리방침은 시행일로부터 적용되며, 법령 및 방침에 따른 변경내용의 추가, 삭제 및 정정이 있는 경우에는 
                변경사항의 시행 7일 전부터 시스템을 통하여 고지할 것입니다.
              </p>
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <p className="text-yellow-800">
                  <strong>시행일자:</strong> 2025년 1월 1일<br/>
                  <strong>개정일자:</strong> 2025년 1월 1일
                </p>
              </div>
            </section>
          </div>

          <div className="mt-12 text-center">
            <button
              onClick={() => window.close()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
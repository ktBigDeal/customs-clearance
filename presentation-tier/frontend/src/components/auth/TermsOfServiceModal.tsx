'use client';

interface TermsOfServiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgree: () => void;
}

export function TermsOfServiceModal({ isOpen, onClose, onAgree }: TermsOfServiceModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">
              이용약관
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
            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제1조 (목적)</h3>
              <p>
                이 약관은 관세청에서 운영하는 관세청 통관시스템(이하 "시스템")의 이용과 관련하여 
                관세청과 이용자 간의 권리, 의무 및 책임사항, 기타 필요한 사항을 규정함을 목적으로 합니다.
              </p>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제2조 (정의)</h3>
              <div className="space-y-3">
                <div className="flex">
                  <span className="font-semibold min-w-0 flex-shrink-0 w-24">1. "시스템"</span>
                  <span>관세청에서 운영하는 통관업무 전자시스템을 말합니다.</span>
                </div>
                <div className="flex">
                  <span className="font-semibold min-w-0 flex-shrink-0 w-24">2. "이용자"</span>
                  <span>시스템에 접속하여 서비스를 이용하는 모든 개인 및 법인을 말합니다.</span>
                </div>
                <div className="flex">
                  <span className="font-semibold min-w-0 flex-shrink-0 w-24">3. "회원"</span>
                  <span>시스템에 회원가입을 하고 이용 승인을 받은 개인 또는 법인을 말합니다.</span>
                </div>
                <div className="flex">
                  <span className="font-semibold min-w-0 flex-shrink-0 w-24">4. "서비스"</span>
                  <span>통관신고, HS코드 분류, 관세계산, 상담 등 시스템에서 제공하는 모든 서비스를 말합니다.</span>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제3조 (약관의 효력 및 변경)</h3>
              <p className="mb-4">
                1. 이 약관은 시스템을 통해 공시하고, 이용자가 서비스를 이용함으로써 효력이 발생합니다.
              </p>
              <p className="mb-4">
                2. 관세청은 필요하다고 인정하는 경우 이 약관을 변경할 수 있으며, 변경된 약관은 
                제1항과 같은 방법으로 공시 또는 통지함으로써 효력을 발생합니다.
              </p>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-blue-800">
                  <strong>중요:</strong> 변경된 약관에 동의하지 않는 경우, 이용자는 서비스 이용을 중단하고 탈퇴를 요청할 수 있습니다.
                </p>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제4조 (회원가입)</h3>
              <p className="mb-4">
                1. 회원가입을 희망하는 자는 관세청이 정한 양식에 따라 회원정보를 기입한 후 본 약관에 동의한다는 의사표시를 함으로써 회원가입을 신청합니다.
              </p>
              <p className="mb-4">
                2. 관세청은 제1항과 같이 회원으로 가입할 것을 신청한 자가 다음 각호에 해당하지 않는 한 회원으로 등록합니다.
              </p>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>가입신청자가 본 약관에 의하여 이전에 회원자격을 상실한 적이 있는 경우</li>
                <li>실명이 아니거나 타인의 명의를 이용한 경우</li>
                <li>허위의 정보를 기재하거나, 관세청이 제시하는 내용을 기재하지 않은 경우</li>
                <li>기타 회원으로 등록하는 것이 시스템의 기술상 현저히 지장이 있다고 판단되는 경우</li>
              </ul>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제5조 (서비스의 제공)</h3>
              <p className="mb-4">
                관세청은 회원에게 다음과 같은 서비스를 제공합니다.
              </p>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">통관 관련 서비스</h4>
                  <ul className="space-y-1 text-sm">
                    <li>• 수출입신고서 작성 및 접수</li>
                    <li>• 통관진행상황 조회</li>
                    <li>• 관세 및 부가세 계산</li>
                    <li>• HS코드 분류 서비스</li>
                  </ul>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">부가 서비스</h4>
                  <ul className="space-y-1 text-sm">
                    <li>• AI 챗봇 상담서비스</li>
                    <li>• 통관 가이드 및 FAQ</li>
                    <li>• 관세율 정보 제공</li>
                    <li>• 무역통계 정보 제공</li>
                  </ul>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제6조 (서비스 이용시간)</h3>
              <p className="mb-4">
                1. 서비스 이용은 관세청의 업무상 또는 기술상 특별한 지장이 없는 한 연중무휴, 1일 24시간 운영을 원칙으로 합니다.
              </p>
              <p className="mb-4">
                2. 관세청은 시스템 정기점검 등의 필요로 인하여 서비스를 일시 중단할 수 있으며, 
                예정된 작업으로 인한 서비스 중단은 사전에 공지합니다.
              </p>
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <h4 className="font-semibold mb-2 text-yellow-800">서비스 중단 시간</h4>
                <ul className="space-y-1 text-yellow-700">
                  <li>• 정기점검: 매월 첫째 일요일 02:00~06:00</li>
                  <li>• 긴급점검: 사전공지 후 필요시</li>
                  <li>• 시스템 업그레이드: 사전공지 후 필요시</li>
                </ul>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제7조 (이용자의 의무)</h3>
              <p className="mb-4">이용자는 다음 사항을 준수해야 합니다.</p>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>회원가입 신청 또는 회원정보 변경 시 실명으로 모든 사항을 사실에 근거하여 작성해야 하며, 허위 또는 타인의 정보를 등록할 경우 일체의 권리를 주장할 수 없습니다.</li>
                <li>다른 회원의 ID를 부정하게 사용해서는 안 됩니다.</li>
                <li>시스템을 이용하여 얻은 정보를 관세청의 사전 승낙 없이 복제하거나 이를 출판 및 방송 등에 사용하거나 제3자에게 제공해서는 안 됩니다.</li>
                <li>시스템의 운영을 고의로 방해해서는 안 됩니다.</li>
                <li>공공질서 및 미풍양속에 위반되는 내용의 정보, 문장, 도형, 음향, 동영상을 전송해서는 안 됩니다.</li>
                <li>관세법령 및 관련 법령을 준수해야 합니다.</li>
              </ul>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제8조 (관세청의 의무)</h3>
              <p className="mb-4">
                1. 관세청은 특별한 사정이 없는 한 회원이 서비스 이용신청을 한 날에 서비스를 이용할 수 있도록 하여야 합니다.
              </p>
              <p className="mb-4">
                2. 관세청은 이 약관에서 정한 바에 따라 지속적이고 안정적인 서비스를 제공하도록 노력합니다.
              </p>
              <p className="mb-4">
                3. 관세청은 회원으로부터 제기되는 의견이나 불만이 정당하다고 객관적으로 인정될 경우에는 
                적절한 절차를 거쳐 즉시 처리하여야 합니다. 다만, 즉시 처리가 곤란한 경우는 회원에게 그 사유와 처리일정을 통보하여야 합니다.
              </p>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제9조 (개인정보보호)</h3>
              <p className="mb-4">
                1. 관세청은 이용자의 개인정보 수집시 서비스 제공을 위하여 필요한 범위에서 최소한의 개인정보를 수집합니다.
              </p>
              <p className="mb-4">
                2. 관세청은 회원의 개인정보를 본인의 동의없이 제3자에게 제공하지 않습니다. 
                단, 다음의 경우에는 예외로 합니다.
              </p>
              <ul className="list-disc list-inside ml-4 space-y-2 mb-4">
                <li>관세법령 및 기타 법령에 의하여 요구되는 경우</li>
                <li>수사기관이 수사목적으로 법령에 정해진 절차와 방법에 따라 요청하는 경우</li>
                <li>통계작성, 학술연구 또는 시장조사를 위하여 필요한 경우로서 특정 개인을 식별할 수 없는 형태로 가공하여 제공하는 경우</li>
              </ul>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-green-800">
                  개인정보 보호에 관한 자세한 사항은 별도의 <strong>개인정보처리방침</strong>을 참고하시기 바랍니다.
                </p>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제10조 (회원탈퇴 및 자격상실)</h3>
              <p className="mb-4">
                1. 회원은 관세청에 언제든지 탈퇴를 요청할 수 있으며 관세청은 즉시 회원탈퇴를 처리합니다.
              </p>
              <p className="mb-4">
                2. 회원이 다음 각호의 사유에 해당하는 경우, 관세청은 회원자격을 제한하거나 정지시킬 수 있습니다.
              </p>
              <ul className="list-disc list-inside ml-4 space-y-2">
                <li>가입 신청 시에 허위 내용을 등록한 경우</li>
                <li>시스템을 이용하여 구입한 재화 등의 대금, 기타 시스템 이용에 관련하여 회원이 부담하는 채무를 기일에 이행하지 않는 경우</li>
                <li>다른 사람의 시스템 이용을 방해하거나 그 정보를 도용하는 등 질서를 위협하는 경우</li>
                <li>시스템을 이용하여 법령 또는 본 약관이 금지하거나 공서양속에 반하는 행위를 하는 경우</li>
              </ul>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제11조 (손해배상 및 면책조항)</h3>
              <p className="mb-4">
                1. 관세청은 서비스에서 제공하는 정보, 자료, 사실의 신뢰도, 정확성 등의 내용에 관하여는 보증하지 않으며 이로 인해 발생한 손해에 대하여 책임을 지지 않습니다.
              </p>
              <p className="mb-4">
                2. 관세청은 시스템의 운영과 관련하여 관세청의 고의 또는 중대한 과실이 없는 한 손해배상의 책임을 지지 않습니다.
              </p>
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <h4 className="font-semibold mb-2 text-red-800">면책사항</h4>
                <ul className="space-y-1 text-red-700">
                  <li>• 천재지변 또는 이에 준하는 불가항력으로 인한 서비스 중단</li>
                  <li>• 회원의 귀책사유로 인한 서비스 이용의 장애</li>
                  <li>• 제3자에 의한 서비스 방해 또는 자료 변조</li>
                  <li>• 시스템에 접속 또는 이용과정에서 발생하는 개인적인 손해</li>
                </ul>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">제12조 (분쟁해결)</h3>
              <p className="mb-4">
                1. 관세청과 이용자는 시스템과 관련하여 발생한 분쟁을 원만하게 해결하기 위하여 노력하여야 합니다.
              </p>
              <p className="mb-4">
                2. 제1항의 노력에도 불구하고 분쟁이 조정되지 아니하거나 조정의 결과가 이행되지 아니하는 경우 민사소송법상의 관할법원에 소를 제기할 수 있습니다.
              </p>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 text-center">
                <p className="text-blue-800">
                  <strong>고객센터:</strong> 042-481-7890 | <strong>이메일:</strong> support@customs.go.kr<br/>
                  <strong>운영시간:</strong> 평일 09:00 ~ 18:00 (토·일·공휴일 제외)
                </p>
              </div>
            </section>

            <section>
              <h3 className="text-base font-semibold text-gray-900 mb-3">부칙</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p><strong>시행일:</strong> 2025년 1월 1일</p>
                <p><strong>개정일:</strong> 2025년 1월 1일</p>
                <p className="mt-2 text-sm text-gray-600">
                  이 약관은 시행일자부터 적용되며, 종전 약관은 본 약관으로 대체됩니다.
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
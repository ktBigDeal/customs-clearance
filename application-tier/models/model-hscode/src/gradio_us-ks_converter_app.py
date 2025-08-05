import gradio as gr
import os
import sys
import re

# 핵심 모듈 임포트
from us_to_korea_hs_converter import HSCodeConverter

# 전역 변환기 인스턴스
converter = None

def initialize_converter(progress=gr.Progress()):
    """변환기 초기화"""
    global converter
    
    us_tariff_file = r".\관세청_미국 관세율표_20250714.xlsx"
    
    # 파일 존재 확인
    if not os.path.exists(us_tariff_file):
        return "❌ 미국 관세율표 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요."
    
    # 한국 추천 시스템 로드
    korea_recommender = None
    try:
        from hs_recommender import HSCodeRecommender
        cache_dir = r'C:\Users\User\통관\cache\hs_code_cache'
        korea_recommender = HSCodeRecommender(cache_dir=cache_dir)
        if korea_recommender.load_data():
            print("✅ 한국 추천 시스템 로드 완료")
        else:
            print("⚠️ 한국 추천 시스템 로드 실패")
            korea_recommender = None
    except ImportError:
        print("⚠️ 한국 추천 시스템 모듈을 찾을 수 없음")
        korea_recommender = None
    
    # 변환기 초기화
    converter = HSCodeConverter(us_tariff_file, korea_recommender)
    
    def progress_callback(value, message):
        if progress:
            progress(value, message)
    
    success, message = converter.initialize_system(progress_callback)
    return message

def is_other_item(text):
    """텍스트에서 기타 항목 여부 확인"""
    if not text:
        return False
    
    text_lower = str(text).lower().strip()
    
    # 기타 키워드 리스트
    other_keywords = [
        '기타', '그 밖의', '따로 분류되지', '기타의',
        'other', 'others', 'nesoi', 'not elsewhere', 'not specified',
        'not elsewhere specified or included',
        'other, not elsewhere specified'
    ]
    
    return any(keyword in text_lower for keyword in other_keywords)

def enhance_product_name_with_context(korea_name, hs6_description):
    """기타 상품명을 맥락 정보와 함께 표시"""
    if not korea_name or not hs6_description:
        return korea_name
    
    if is_other_item(korea_name):
        # "기타" 항목인 경우 맥락 추가
        return f"{hs6_description} 분야의 기타 항목"
    else:
        # 일반 항목은 그대로
        return korea_name

def convert_hs_code(us_hs_code, us_product_name=""):
    """HS 코드 변환 함수"""
    global converter
    
    if converter is None:
        return "❌ 시스템이 초기화되지 않았습니다. 먼저 '시스템 초기화' 버튼을 클릭해주세요.", "", "", "", "", ""
    
    # 입력 검증
    if not us_hs_code or not us_hs_code.strip():
        return "❌ HS 코드를 입력해주세요.", "", "", "", "", ""
    
    us_hs_code = us_hs_code.strip()
    
    # HS 코드 유효성 검사
    if not re.match(r'^\d{4,10}$', us_hs_code):
        return "❌ 올바른 HS 코드를 입력하세요 (4-10자리 숫자)", "", "", "", "", ""
    
    # 변환 실행
    result = converter.convert_hs_code(us_hs_code, us_product_name)
    
    if result['status'] == 'success':
        # 성공적인 변환
        us_info = result['us_info']
        korea_rec = result['korea_recommendation']
        hs_analysis = result['hs_analysis']
        
        # HS6 분류 설명 가져오기
        hs6 = us_info['hs_components']['hs6']
        hs6_description = converter.get_hs6_description(hs6)
        
        # 한국 상품명에 맥락 정보 추가 (기타 항목인 경우)
        enhanced_korea_name = enhance_product_name_with_context(
            korea_rec['name_kr'], 
            hs6_description
        )
        
        # 메인 결과 포맷팅
        main_result = f"""
## ✅ 변환 성공!

### 📋 미국 HS 코드 정보
- **코드**: `{result['us_hs_code']}`
- **영문명**: {us_info['english_name']}
- **한글명**: {us_info.get('korean_name', '없음')}

### 🎯 추천 한국 HSK 코드
- **코드**: `{korea_rec['hs_code']}`
- **상품명**: {enhanced_korea_name}
- **신뢰도**: {korea_rec['confidence']:.1%}
- **데이터 출처**: {korea_rec.get('data_source', '통합')}

### 📊 분석 정보
- **HS 6자리 매칭**: ✅ 완료 (`{hs_analysis['us_hs6']}`)
- **구조 유사도**: {hs_analysis['hs_similarity']:.1%}
- **의미 유사도**: {hs_analysis['semantic_similarity']:.1%}
- **후보군 수**: {hs_analysis['total_candidates']}개
"""
        
        # 후보 목록 테이블 (후보들도 맥락 정보 추가)
        candidates_md = "### 🎯 상위 후보 목록\n\n"
        candidates_md += "| 순위 | HSK 코드 | 상품명 | 유사도 |\n"
        candidates_md += "|------|----------|--------|--------|\n"
        
        for i, candidate in enumerate(result['all_candidates'][:3], 1):
            similarity = candidate.get('similarity_score', 0.0)
            
            # 후보 상품명도 맥락 정보와 함께 표시
            candidate_name = enhance_product_name_with_context(
                candidate['name_kr'], 
                hs6_description
            )
            
            name_display = candidate_name[:50] + "..." if len(candidate_name) > 50 else candidate_name
            candidates_md += f"| {i} | `{candidate['hs_code']}` | {name_display} | {similarity:.1%} |\n"
        
        return (
            main_result,
            korea_rec['hs_code'],
            enhanced_korea_name,  # 맥락 정보가 포함된 상품명
            korea_rec.get('name_en', ''),
            f"{korea_rec['confidence']:.1%}",
            candidates_md
        )
    
    elif result['status'] == 'error':
        error_msg = f"❌ **오류 발생**\n\n{result['message']}"
        if 'suggestions' in result and result['suggestions']:
            error_msg += f"\n\n💡 **유사한 코드 제안:**\n"
            for suggestion in result['suggestions'][:3]:
                error_msg += f"- `{suggestion}`\n"
        
        return error_msg, "", "", "", "", ""
    
    elif result['status'] == 'no_hs6_match':
        no_match_msg = f"""
❌ **HS 6자리 매칭 실패**

미국 HS 코드 `{result['us_hs_code']}`의 HS 6자리 `{result['hs6']}`에 해당하는 한국 코드가 없습니다.

### 📋 미국 코드 정보
- **영문명**: {result['us_info']['english_name']}
- **한글명**: {result['us_info'].get('korean_name', '없음')}

이는 해당 상품이 한국에서 취급되지 않거나 다른 분류 체계를 사용할 가능성을 의미합니다.
"""
        
        return no_match_msg, "", "", "", "", ""
    
    else:
        return f"❌ 알 수 없는 오류: {result.get('message', '오류 정보 없음')}", "", "", "", "", ""

def get_system_status():
    """시스템 상태 확인"""
    global converter
    
    if converter is None:
        return "❌ 시스템이 초기화되지 않음"
    
    if not converter.initialized:
        return "⚠️ 시스템 초기화 진행 중..."
    
    status = "✅ **시스템 상태**\n\n"
    
    # 기본 상태
    status += f"- 초기화 상태: {'✅ 완료' if converter.initialized else '❌ 미완료'}\n"
    status += f"- 미국 데이터: {'✅ 로드됨' if converter.us_data is not None else '❌ 없음'}\n"
    status += f"- 한국 데이터: {'✅ 로드됨' if converter.korea_data is not None else '❌ 없음'}\n"
    status += f"- 시맨틱 모델: {'✅ 로드됨' if converter.semantic_model is not None else '❌ 없음'}\n"
    
    # 데이터 통계
    if converter.us_data is not None:
        status += f"\n📊 **미국 데이터 통계:**\n"
        status += f"- 총 코드 수: {len(converter.us_data):,}개\n"
        status += f"- HS 6자리 종류: {len(converter.us_hs6_index):,}개\n"
        status += f"- 장(Chapter) 종류: {len(converter.us_data['chapter'].unique())}개\n"
    
    if converter.korea_data is not None:
        status += f"\n📊 **한국 데이터 통계:**\n"
        status += f"- 총 코드 수: {len(converter.korea_data):,}개\n"
        status += f"- HS 6자리 종류: {len(converter.korea_hs6_index):,}개\n"
    
    # 캐시 정보
    status += f"\n💾 **캐시 정보:**\n"
    status += f"- 변환 캐시: {len(converter.conversion_cache)}개\n"
    
    return status

def clear_cache():
    """캐시 초기화"""
    global converter
    
    if converter is None:
        return "❌ 시스템이 초기화되지 않음"
    
    cache_size = converter.clear_cache()
    return f"✅ 캐시 초기화 완료 ({cache_size}개 항목 삭제)"

# Gradio 인터페이스 생성
def create_gradio_interface():
    """Gradio 웹 인터페이스 생성"""
    
    with gr.Blocks(
        title="HS Code Converter",
        theme=gr.themes.Soft(),
        css="""
        .main-container { max-width: 1200px; margin: 0 auto; }
        .result-box { border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
        .error-box { border: 1px solid #ff6b6b; background-color: #fff5f5; }
        .success-box { border: 1px solid #51cf66; background-color: #f3faf3; }
        """
    ) as demo:
        
        gr.Markdown("""
# 🔄 HS Code Converter

## 미국 HS코드 → 한국 HSK코드 변환 시스템

HS 6자리 국제 공통 분류체계와 각국 고유 세분류를 고려한 정밀 변환 시스템

""")
        
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📋 변환 입력")
                
                with gr.Group():
                    us_hs_input = gr.Textbox(
                        label="미국 HS 코드",
                        placeholder="예: 8471300000",
                        info="4-10자리 숫자를 입력하세요"
                    )
                    
                    product_name_input = gr.Textbox(
                        label="상품명 (선택사항)",
                        placeholder="예: 노트북 컴퓨터",
                        info="더 정확한 매칭을 위해 상품명을 입력하세요"
                    )
                
                with gr.Row():
                    convert_btn = gr.Button("🔄 변환 실행", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ 입력 초기화", variant="secondary")
            
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ 시스템 관리")
                
                with gr.Group():
                    init_btn = gr.Button("🚀 시스템 초기화", variant="primary")
                    status_btn = gr.Button("📊 상태 확인", variant="secondary")
                    cache_clear_btn = gr.Button("💾 캐시 초기화", variant="secondary")
                
                system_status = gr.Textbox(
                    label="시스템 상태",
                    value="시스템 초기화가 필요합니다.",
                    max_lines=10,
                    interactive=False
                )
        
        gr.Markdown("---")
        
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### 📋 변환 결과")
                main_result = gr.Markdown(
                    value="변환 결과가 여기에 표시됩니다.",
                    elem_classes=["result-box"]
                )
            
            with gr.Column(scale=2):
                gr.Markdown("### 📊 상세 정보")
                
                with gr.Group():
                    korea_hs_code = gr.Textbox(
                        label="한국 HSK 코드",
                        interactive=False
                    )
                    
                    korea_name_kr = gr.Textbox(
                        label="한국 상품명",
                        interactive=False,
                        info="기타 항목의 경우 자동으로 분야 맥락 포함"
                    )
                    
                    korea_name_en = gr.Textbox(
                        label="영문 상품명",
                        interactive=False
                    )
                    
                    confidence_score = gr.Textbox(
                        label="신뢰도",
                        interactive=False
                    )

        
        with gr.Row():
            with gr.Column():
     
                candidates_table = gr.Markdown(
                    value="후보 목록이 여기에 표시됩니다."
                )
        
        # 예제 추가
        gr.Markdown("### 💡 사용 예제")
        examples = gr.Examples(
            examples=[
                ["9507100040", "낚시대"],  # 기타 낚시용구 - 맥락 강조용
                ["9507109000", ""],       # 기타 항목 테스트용
                ["8471300100", "노트북 컴퓨터"],
            ],
            inputs=[us_hs_input, product_name_input],
            label="클릭하여 예제 사용 (기타 항목 예제 포함)"
        )
        
        # 이벤트 핸들러 설정
        init_btn.click(
            fn=initialize_converter,
            outputs=system_status,
            show_progress=True
        )
        
        status_btn.click(
            fn=get_system_status,
            outputs=system_status
        )
        
        cache_clear_btn.click(
            fn=clear_cache,
            outputs=system_status
        )
        
        convert_btn.click(
            fn=convert_hs_code,
            inputs=[us_hs_input, product_name_input],
            outputs=[
                main_result,
                korea_hs_code,
                korea_name_kr,
                korea_name_en,
                confidence_score,
                candidates_table,
             
            ]
        )
        
        clear_btn.click(
            fn=lambda: ("", ""),
            outputs=[us_hs_input, product_name_input]
        )
        
        # 사용 가이드에 맥락 정보 설명 추가
        gr.Markdown("""
---

### 📝 사용 가이드

1. **시스템 초기화**: 먼저 '시스템 초기화' 버튼을 클릭하여 데이터를 로드하세요.
2. **HS 코드 입력**: 미국 HS 코드를 입력하세요 (4-10자리).
3. **상품명 입력**: 더 정확한 매칭을 위해 상품명을 추가로 입력할 수 있습니다.
4. **변환 실행**: '변환 실행' 버튼을 클릭하여 한국 HSK 코드를 확인하세요.

### 🔍 특징

- **HS 체계 기반**: HS 6자리 국제 공통 분류를 기준으로 정확한 매칭
- **🎯 자동 맥락 제공**: 시스템이 자동으로 추출한 HS 6자리 분류 설명 활용
  - **"기타" 항목**: 자동으로 "~~~ 분야의 기타 항목"으로 맥락 제공
  - **일반 항목**: 해당 분야 정보를 명확히 표시
- **의미 분석**: AI 기반 상품명 분석으로 세분류 매칭
- **신뢰도 측정**: HS 구조 유사도와 의미 유사도를 종합한 신뢰도 제공
- **다중 후보**: 여러 후보 중에서 최적의 코드 추천

### 💡 "기타(Others)" 항목 자동 처리

**작동 방식**: 
- 시스템이 상품명에서 "기타", "other", "nesoi" 등을 자동 감지
- **기존 HS 6자리 설명**을 활용하여 맥락 정보 자동 생성

**결과 예시**:
- `9507109000 기타` → **"낚시용 라인, 훅 등 분야의 기타 항목"**
- `8412109000 기타` → **"유압모터 분야의 기타 항목"**
- `8471300000 기타` → **"휴대용 자동자료처리기계 분야의 기타 항목"**


### ⚠️ 주의사항

- 초기 실행 시 모델 다운로드로 인해 시간이 걸릴 수 있습니다.
- 정확한 변환을 위해 미국 관세율표 파일이 필요합니다.
- 결과는 참고용이며, 최종 결정 시 관련 기관에 확인하시기 바랍니다.

""")
    
    return demo

if __name__ == "__main__":
    # Gradio 앱 실행
    print("📱 브라우저에서 http://localhost:7890 으로 접속하세요")
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7890,
        share=False,
        debug=True,
        show_error=True
    )

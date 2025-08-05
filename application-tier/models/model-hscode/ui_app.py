# ui_app.py - Gradio UI 인터페이스

import gradio as gr
import pandas as pd
import os
import sys
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(__file__))

from src.hs_recommender import HSCodeRecommender
from config import SYSTEM_CONFIG

class HSCodeUI:
    """HS 코드 추천 시스템 Gradio UI 클래스"""
    
    def __init__(self):
        self.recommender = None
        self.is_initialized = False
        self.openai_available = False
        self.api_key = None
        
    def load_api_key_from_file(self) -> Optional[str]:
        """docs/Aivle-api.txt 파일에서 API 키 로드"""
        try:
            # 여러 경로에서 API 키 파일을 찾기
            possible_paths = [
                os.path.join(os.path.dirname(__file__), 'docs', 'Aivle-api.txt'),
                os.path.join('.', 'docs', 'Aivle-api.txt'),
                './docs/Aivle-api.txt'
            ]
            
            for api_file_path in possible_paths:
                if os.path.exists(api_file_path):
                    try:
                        with open(api_file_path, 'r', encoding='utf-8') as f:
                            api_key = f.read().strip()
                            if api_key and api_key.startswith('sk-'):
                                return api_key
                    except Exception as read_error:
                        print(f"API 키 파일 읽기 오류 ({api_file_path}): {read_error}")
                        continue
            
            return None
        except Exception as e:
            print(f"API 키 파일 로드 중 오류: {e}")
            return None
        
    def initialize_system(self, progress=gr.Progress()):
        """시스템 초기화 (API 키 자동 로드 포함)"""
        if self.is_initialized:
            return "✅ 시스템이 이미 초기화되었습니다."
        
        try:
            progress(0.1, desc="HS 코드 추천 시스템 초기화 중...")
            
            # API 키 자동 로드
            progress(0.15, desc="API 키 로딩 중...")
            self.api_key = self.load_api_key_from_file()
            
            # 캐시 디렉토리 설정
            cache_dir = './cache/hs_code_cache'
            
            progress(0.2, desc="추천 엔진 로딩 중...")
            self.recommender = HSCodeRecommender(
                semantic_model_name=SYSTEM_CONFIG['semantic_model'],
                top_k=SYSTEM_CONFIG['top_k'],
                cache_dir=cache_dir
            )
            
            progress(0.4, desc="데이터 로딩 중...")
            if not self.recommender.load_data():
                return "❌ 데이터 로드에 실패했습니다. 데이터 파일을 확인해주세요."
            
            progress(0.6, desc="OpenAI API 설정 중...")
            if self.api_key:
                os.environ['OPENAI_API_KEY'] = self.api_key
                self.openai_available = self.recommender.initialize_openai()
            
            progress(0.8, desc="시스템 상태 확인 중...")
            stats = self.recommender.get_statistics()
            if not stats.get('system_initialized'):
                return "❌ 시스템 초기화에 실패했습니다."
            
            self.is_initialized = True
            progress(1.0, desc="초기화 완료!")
            
            api_status = "✅ 자동 설정됨" if self.openai_available else "❌ 설정 실패"
            
            return f"""✅ **HS 코드 추천 시스템이 준비되었습니다!**

📊 **시스템 정보:**
- 총 항목 수: {stats.get('total_items', 0):,}개
- HS 챕터 수: {stats.get('chapters', 0)}개
- 의미 모델: {stats.get('semantic_model', 'N/A')}
- 캐시 상태: {'유효' if stats.get('cache_info', {}).get('cache_valid') else '무효'}

🤖 **OpenAI API 상태:** {api_status}
{f"📁 API 키 파일에서 자동 로드됨" if self.api_key else "⚠️ docs/Aivle-api.txt 파일을 확인하세요"}

이제 상품명을 입력하여 AI 기반 HS 코드 추천을 받을 수 있습니다! 🚀"""
            
        except Exception as e:
            return f"❌ 초기화 중 오류가 발생했습니다: {str(e)}"
    
    def setup_openai(self, api_key: str) -> str:
        """OpenAI API 수동 설정 (자동 로드 실패 시에만 사용)"""
        if not self.is_initialized:
            return "⚠️ 먼저 시스템을 초기화해주세요."
        
        if self.openai_available:
            return "✅ OpenAI API가 이미 자동으로 설정되어 있습니다."
        
        if not api_key.strip():
            return "⚠️ API 키를 입력해주세요."
        
        try:
            # API 키 수동 설정
            os.environ['OPENAI_API_KEY'] = api_key.strip()
            self.api_key = api_key.strip()
            
            # OpenAI 초기화 시도
            self.openai_available = self.recommender.initialize_openai()
            
            if self.openai_available:
                return "✅ OpenAI API가 수동으로 설정되었습니다! AI 고급 추천 기능을 사용할 수 있습니다."
            else:
                return "❌ OpenAI API 설정에 실패했습니다. API 키를 확인해주세요."
                
        except Exception as e:
            return f"❌ OpenAI 설정 중 오류: {str(e)}"
    
    def recommend_hs_code(self, 
                         product_name: str, 
                         material: str = "", 
                         usage: str = "", 
                         result_count: int = 5,
                         progress=gr.Progress()) -> tuple:
        """HS 코드 추천 실행 (AI 고급 추천 기본 사용)"""
        
        if not self.is_initialized:
            return "⚠️ 먼저 시스템 설정 탭에서 '시스템 초기화' 버튼을 클릭해주세요.", None
            
        if not self.openai_available:
            return """⚠️ OpenAI API 설정이 필요합니다.
            
**해결 방법:**
1. docs/Aivle-api.txt 파일에 올바른 API 키가 있는지 확인
2. 시스템을 다시 초기화해보세요
3. 그래도 안되면 시스템 설정 탭에서 수동으로 API 키를 입력하세요""", None
        
        if not product_name.strip():
            return "⚠️ 상품명을 입력해주세요.", None
        
        try:
            progress(0.1, desc="AI 추천 준비 중...")
            progress(0.3, desc=f"'{product_name}' AI 분석 중...")
            
            # 항상 AI 고급 추천 사용
            progress(0.5, desc="🤖 AI 기반 고급 추천 실행 중...")
            results = self.recommender.recommend_ultimate(
                query=product_name.strip(),
                material=material.strip(),
                usage=usage.strip(),
                final_count=result_count
            )
            
            progress(0.8, desc="결과 정리 중...")
            
            # 결과 포맷팅
            if not results.get('recommendations'):
                return "😔 검색 결과가 없습니다. 다른 검색어를 시도해보세요.", None
            
            # 결과 테이블 생성
            recommendations = results['recommendations']
            table_data = []
            
            for i, rec in enumerate(recommendations, 1):
                try:
                    confidence = f"{rec.get('confidence', 0):.3f}"
                    hs_code = rec.get('hs_code', 'N/A')
                    
                    # 실제 품목명 추출 (우선순위: llm_analysis > name_kr > description의 첫 부분)
                    name_kr = 'N/A'
                    try:
                        if rec.get('llm_analysis') and isinstance(rec['llm_analysis'], dict) and rec['llm_analysis'].get('korean_name'):
                            name_kr = str(rec['llm_analysis']['korean_name'])
                        elif rec.get('name_kr'):
                            name_kr = str(rec['name_kr'])
                        elif rec.get('description'):
                            # description에서 품목명 추출 (첫 번째 의미있는 부분)
                            desc_str = str(rec['description']).strip()
                            if desc_str:
                                desc_parts = desc_str.split(' ')
                                if len(desc_parts) > 0 and desc_parts[0]:
                                    name_kr = ' '.join(desc_parts[:3])  # 처음 3단어
                    except Exception:
                        name_kr = 'N/A'
                    
                    description = str(rec.get('description', ''))
                    data_source = str(rec.get('data_source', 'N/A'))
                    
                    # 설명 텍스트 제한
                    if len(description) > 150:
                        description = description[:150] + "..."
                    
                    table_data.append([
                        i, hs_code, name_kr, confidence, data_source, description
                    ])
                except Exception as e:
                    # 개별 레코드 처리 실패 시 기본값으로 추가
                    table_data.append([
                        i, rec.get('hs_code', 'N/A'), 'Error', '0.000', 'N/A', f'처리 오류: {str(e)}'
                    ])
            
            # DataFrame 생성
            df = pd.DataFrame(table_data, columns=[
                "순위", "HS 코드", "품목명", "신뢰도", "데이터 소스", "상세 설명"
            ])
            
            progress(1.0, desc="완료!")
            
            # 검색 정보 생성
            search_info = results.get('search_info', {})
            info_text = f"""🤖 **AI 고급 추천 결과**
- 검색어: {product_name}
- 재질: {material if material else '미입력'}
- 용도: {usage if usage else '미입력'}
- AI 분석 방법: 고급 추천 (OpenAI + 의미검색)
- 전체 후보: {search_info.get('total_candidates', len(recommendations))}개
- 최종 결과: {len(recommendations)}개

✨ **AI 추천의 장점**: OpenAI가 상품의 특성을 분석하여 가장 적합한 HS 코드를 제안합니다!"""
            
            return info_text, df
            
        except Exception as e:
            return f"❌ 추천 중 오류가 발생했습니다: {str(e)}", None
    
    def get_system_status(self) -> str:
        """시스템 상태 확인"""
        if not self.is_initialized:
            return "❌ 시스템이 초기화되지 않았습니다."
        
        try:
            stats = self.recommender.get_statistics()
            cache_info = stats.get('cache_info', {})
            
            status = f"""📊 **시스템 상태**

🔧 **기본 정보**
- 초기화 상태: {'✅ 완료' if self.is_initialized else '❌ 미완료'}
- OpenAI 상태: {'✅ 활성' if self.openai_available else '❌ 비활성'}
- 의미 모델: {stats.get('semantic_model', 'N/A')}

📁 **데이터 정보**
- 총 항목 수: {stats.get('total_items', 0):,}개
- HS 챕터 수: {stats.get('chapters', 0)}개
- 표준품명 커버리지: {stats.get('standard_coverage', 0):.1f}%

💾 **캐시 정보**
- 캐시 상태: {'✅ 유효' if cache_info.get('cache_valid') else '❌ 무효'}
- 캐시 크기: {cache_info.get('total_size_mb', 0):.1f} MB
- 캐시 버전: {cache_info.get('metadata', {}).get('cache_version', 'N/A')}
"""
            
            # 데이터 소스별 분포
            if 'data_sources' in stats:
                status += "\n📈 **데이터 소스 분포**\n"
                for source, count in stats['data_sources'].items():
                    status += f"- {source}: {count:,}개\n"
            
            return status
            
        except Exception as e:
            return f"❌ 상태 확인 중 오류: {str(e)}"

def create_interface():
    """Gradio 인터페이스 생성"""
    ui = HSCodeUI()
    
    # CSS 스타일링
    css = """
    .gradio-container {
        font-family: 'Noto Sans KR', sans-serif;
    }
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .status-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .result-table {
        margin-top: 15px;
    }
    """
    
    with gr.Blocks(css=css, title="HS 코드 추천 시스템", theme=gr.themes.Soft()) as demo:
        
        # 헤더
        gr.HTML("""
        <div class="main-header">
            <h1>🏢 HS 코드 추천 시스템</h1>
            <p>한국 관세청 데이터 기반 지능형 HS 코드 추천 서비스</p>
        </div>
        """)
        
        with gr.Tabs():
            # 메인 추천 탭
            with gr.Tab("🔍 HS 코드 추천"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📝 상품 정보 입력")
                        
                        product_input = gr.Textbox(
                            label="상품명",
                            placeholder="예: LED 조명, 볼트, 프린터 토너 등",
                            lines=2
                        )
                        
                        with gr.Row():
                            material_input = gr.Textbox(
                                label="재질 (선택사항)",
                                placeholder="예: 플라스틱, 금속, 유리 등"
                            )
                            usage_input = gr.Textbox(
                                label="용도 (선택사항)",
                                placeholder="예: 의료용, 산업용, 가정용 등"
                            )
                        
                        result_count_slider = gr.Slider(
                            minimum=3,
                            maximum=10,
                            step=1,
                            value=5,
                            label="결과 개수"
                        )
                        
                        gr.Markdown("💡 **AI 고급 추천 모드**: OpenAI가 자동으로 상품을 분석하여 최적의 HS 코드를 제안합니다.")
                        
                        recommend_btn = gr.Button(
                            "🤖 AI로 HS 코드 추천 받기",
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 📊 추천 결과")
                        result_info = gr.Markdown()
                        result_table = gr.Dataframe(
                            headers=["순위", "HS 코드", "품목명", "신뢰도", "데이터 소스", "상세 설명"],
                            datatype=["number", "str", "str", "str", "str", "str"],
                            interactive=False
                        )
                
                # 추천 버튼 이벤트
                recommend_btn.click(
                    fn=ui.recommend_hs_code,
                    inputs=[
                        product_input, material_input, usage_input,
                        result_count_slider
                    ],
                    outputs=[result_info, result_table]
                )
                
                # 예시 버튼들
                gr.Markdown("### 💡 검색 예시")
                with gr.Row():
                    example_btns = [
                        gr.Button("📱 스마트폰", size="sm"),
                        gr.Button("🔧 볼트", size="sm"),
                        gr.Button("💡 LED 전구", size="sm"),
                        gr.Button("🖨️ 프린터 토너", size="sm"),
                        gr.Button("🥤 플라스틱 용기", size="sm")
                    ]
                
                # 예시 버튼 이벤트
                example_btns[0].click(lambda: "스마트폰", outputs=[product_input])
                example_btns[1].click(lambda: "볼트", outputs=[product_input])
                example_btns[2].click(lambda: "LED 전구", outputs=[product_input])
                example_btns[3].click(lambda: "프린터 토너", outputs=[product_input])
                example_btns[4].click(lambda: "플라스틱 용기", outputs=[product_input])
            
            # 시스템 설정 탭
            with gr.Tab("⚙️ 시스템 설정"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🚀 시스템 초기화")
                        init_status = gr.Markdown("시스템 초기화가 필요합니다.")
                        init_btn = gr.Button("🔄 시스템 초기화", variant="primary")
                        
                        gr.Markdown("### 🤖 OpenAI API 설정")
                        gr.Markdown("✅ **API 키는 docs/Aivle-api.txt 파일에서 자동으로 로드됩니다**")
                        gr.Markdown("💡 자동 로드가 실패한 경우에만 아래에 수동으로 입력하세요")
                        openai_key = gr.Textbox(
                            label="OpenAI API Key (선택사항)",
                            type="password",
                            placeholder="자동 로드 실패 시에만 입력하세요"
                        )
                        openai_setup_btn = gr.Button("🔑 수동 API 설정")
                        openai_status = gr.Markdown()
                    
                    with gr.Column():
                        gr.Markdown("### 📊 시스템 상태")
                        status_display = gr.Markdown()
                        status_refresh_btn = gr.Button("🔄 상태 새로고침")
                
                # 이벤트 핸들러
                init_btn.click(
                    fn=ui.initialize_system,
                    outputs=[init_status]
                )
                
                openai_setup_btn.click(
                    fn=ui.setup_openai,
                    inputs=[openai_key],
                    outputs=[openai_status]
                )
                
                status_refresh_btn.click(
                    fn=ui.get_system_status,
                    outputs=[status_display]
                )
            
            # 도움말 탭
            with gr.Tab("❓ 사용법"):
                gr.Markdown("""
                ## 📖 AI 기반 HS 코드 추천 시스템 사용법
                
                ### 🚀 시작하기
                1. **시스템 설정** 탭에서 "시스템 초기화" 버튼을 클릭하세요
                2. **자동**: OpenAI API 키가 docs/Aivle-api.txt에서 자동으로 로드됩니다
                3. **HS 코드 추천** 탭에서 상품명을 입력하고 AI 추천을 받으세요
                
                ### 🤖 AI 고급 추천의 특징
                - **지능형 분석**: OpenAI가 상품의 특성을 깊이 있게 분석
                - **맥락 이해**: 재질, 용도, 특성을 종합적으로 고려
                - **정확한 품목명**: "LLM 제안" 대신 실제 정확한 품목명 제공
                - **높은 신뢰도**: 전통적인 키워드 검색보다 훨씬 정확
                
                ### 🔍 검색 팁
                - **정확한 상품명**: "LED 조명", "스테인리스 볼트" 등 구체적으로 입력
                - **재질 정보**: 플라스틱, 금속, 유리 등 재질 정보 추가
                - **용도 정보**: 의료용, 산업용, 가정용 등 사용 목적 명시
                - **상세할수록 좋음**: AI가 더 많은 정보를 분석할수록 정확도 향상
                
                ### 📊 결과 해석
                - **신뢰도**: 0~1 사이의 값, 높을수록 정확
                - **데이터 소스**: 관세청 공식 데이터 출처 표시
                - **순위**: 신뢰도 기준 정렬된 추천 순위
                
                ### ⚠️ 주의사항
                - HS 코드는 참고용이며, 최종 신고시 관세청 확인 필요
                - 복잡한 상품의 경우 전문가 상담 권장
                - 정기적으로 최신 관세청 데이터로 업데이트됨
                
                ### 🛠️ 문제 해결
                - **초기화 실패시**: 데이터 파일 경로 확인
                - **API 자동 로드 실패**: docs/Aivle-api.txt 파일 확인 또는 수동 입력
                - **검색 결과 없음**: 다른 키워드로 재검색 또는 더 구체적인 설명 추가
                - **API 오류**: OpenAI API 키 및 잔액 확인
                
                ### 📁 API 키 파일 설정
                - **파일 위치**: docs/Aivle-api.txt
                - **형식**: 파일에 API 키만 저장 (sk-proj-...)
                - **자동 로드**: 시스템 초기화 시 자동으로 읽어옴
                - **수동 설정**: 자동 로드 실패 시 UI에서 직접 입력 가능
                """)
        
        # 푸터
        gr.HTML("""
        <div style="text-align: center; padding: 20px; margin-top: 30px; border-top: 1px solid #eee;">
            <p style="color: #666;">
                🏢 HS 코드 추천 시스템 v2.1 | 한국 관세청 데이터 기반 | UV + Gradio 구동
            </p>
        </div>
        """)
    
    return demo

def main():
    """UI 애플리케이션 메인 실행 함수"""
    print("🚀 HS 코드 추천 시스템 UI 시작!")
    print("📱 브라우저에서 http://localhost:7860 으로 접속하세요")
    
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False,
        show_api=False,
        quiet=False
    )

if __name__ == "__main__":
    main()
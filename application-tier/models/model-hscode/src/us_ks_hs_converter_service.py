import numpy as np
from typing import Dict, List, Optional, Tuple
import os
import sys
import re
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch
from dataclasses import dataclass
import pandas as pd
from dotenv import load_dotenv

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def convert_numpy_types(obj):
    """NumPy 타입을 Python 네이티브 타입으로 재귀적으로 변환"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif pd.isna(obj):
        return None
    else:
        return obj


@dataclass
class ProductAnalysis:
    """LLM 분석 결과 구조체"""
    material: str
    function: str
    target_user: str
    size_category: str
    key_features: List[str]
    alternative_hs6: List[str]
    reasoning: str

@dataclass
class LLMRanking:
    """LLM 순위 매김 결과"""
    rank: int
    hs_code: str
    confidence: float
    reason: str

class HSCodeStructureAnalyzer:
    """HS 코드 구조 분석 클래스"""
    
    @staticmethod
    def get_hs_components(hs_code: str) -> Dict[str, str]:
        """HS 코드를 구성 요소별로 분해"""
        hs_code = str(hs_code).strip()
        
        if len(hs_code) <= 10:
            hs_code = hs_code.ljust(10, '0')
        else:
            hs_code = hs_code[:10]
        
        return {
            'full_code': hs_code,
            'chapter': hs_code[:2],
            'heading': hs_code[:4],
            'subheading': hs_code[:6],
            'detailed': hs_code[6:],
            'hs6': hs_code[:6],
            'hs4_national': hs_code[6:]
        }
    
    @staticmethod
    def is_valid_hs6_match(us_code: str, korea_code: str) -> bool:
        """HS 6자리(국제 공통) 매칭 검증"""
        us_hs6 = str(us_code).zfill(10)[:6]
        korea_hs6 = str(korea_code).zfill(10)[:6]
        return us_hs6 == korea_hs6
    
    @staticmethod
    def calculate_hs_similarity(us_code: str, korea_code: str) -> float:
        """HS 구조 기반 유사도 계산"""
        us_comp = HSCodeStructureAnalyzer.get_hs_components(us_code)
        korea_comp = HSCodeStructureAnalyzer.get_hs_components(korea_code)
        
        if us_comp['hs6'] != korea_comp['hs6']:
            return 0.0
        
        similarity = 0.6
        if us_comp['heading'] == korea_comp['heading']:
            similarity += 0.2
        if us_comp['full_code'] == korea_comp['full_code']:
            similarity += 0.2
        
        return min(similarity, 1.0)

class HSCodeConverterService:
    """HS 체계를 반영한 미국→한국 HS코드 변환 서비스 (LLM 강화)"""
    
    def __init__(self, us_tariff_file: str = None, korea_recommender_system=None,
                 openai_api_key: str = None):
        self.us_tariff_file = us_tariff_file
        self.korea_recommender = korea_recommender_system
        
        # 미국 데이터
        self.us_data = None
        self.us_hs6_index = {}
        
        # 한국 데이터
        self.korea_data = None
        self.korea_hs6_index = {}
        
        # HS 6자리 분류 설명
        self.hs6_descriptions = {}
        
        # HS 구조 분석기
        self.hs_analyzer = HSCodeStructureAnalyzer()
        
        # 변환 캐시
        self.conversion_cache = {}
        
        # 텍스트 검색 엔진
        self.semantic_model = None
        
        # LLM 관련 설정
        self.openai_client = None
        self.llm_available = False
        self.use_llm = False
        
        # LLM 초기화 시도
        if openai_api_key and OPENAI_AVAILABLE:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                # API 키 유효성 간단 테스트
                test_response = self.openai_client.models.list()
                self.llm_available = True
                self.use_llm = True
                print("🤖 OpenAI LLM 연결 완료")
            except Exception as e:
                print(f"⚠️ OpenAI LLM 연결 실패: {e}")
                print("📊 기본 모드로 전환합니다.")
                self.llm_available = False
                self.openai_client = None
        
        # LLM 캐시
        self.llm_analysis_cache = {}
        self.llm_ranking_cache = {}
        self.initialized = False
        
        llm_status = "LLM 강화" if self.llm_available else "기본 모드"
        print(f"HS 코드 변환 시스템 ({llm_status}) 초기화")
    
    def initialize_system(self, progress_callback=None):
        """시스템 초기화"""
        try:
            if progress_callback:
                progress_callback(0.1, "시맨틱 모델 로딩 중...")
            
            # 시맨틱 모델 로드
            print("📥 시맨틱 모델 로딩 중...")
            self.semantic_model = SentenceTransformer('jhgan/ko-sbert-nli')
            print("✅ 시맨틱 모델 로드 완료")
            
            if progress_callback:
                progress_callback(0.3, "미국 데이터 로딩 중...")
            
            # 미국 데이터 로드
            if self.us_tariff_file and os.path.exists(self.us_tariff_file):
                print("📥 미국 관세율표 데이터 로딩 중...")
                if self.load_us_tariff_data():
                    print("✅ 미국 데이터 로드 완료")
                else:
                    print("❌ 미국 데이터 로드 실패")
            else:
                print("⚠️ 미국 관세율표 파일을 찾을 수 없음")
            
            if progress_callback:
                progress_callback(0.7, "한국 데이터 로딩 중...")
            
            # 한국 데이터 로드 시도
            if self.korea_recommender:
                print("📥 한국 HSK 데이터 로딩 중...")
                if self.load_korea_data_from_recommender():
                    print("✅ 한국 데이터 로드 완료")
                else:
                    print("❌ 한국 데이터 로드 실패")
            else:
                print("⚠️ 한국 추천 시스템이 제공되지 않음")
            
            if progress_callback:
                progress_callback(1.0, "초기화 완료!")
            
            self.initialized = True
            llm_status = " (LLM 강화 모드)" if self.llm_available else ""
            return True, f"✅ 시스템 초기화 완료!{llm_status}"
            
        except Exception as e:
            error_msg = f"❌ 초기화 실패: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def load_us_tariff_data(self) -> bool:
        """미국 관세율표 데이터 로드 및 HS 6자리 인덱스 구축"""
        try:
            self.us_data = pd.read_excel(self.us_tariff_file, sheet_name=0)
            print(f"📊 원본 데이터: {len(self.us_data)}개 행")
            
            # 컬럼명 표준화
            column_mapping = {
                '세번': 'hs_code',
                '영문품명': 'english_name',
                '한글품명': 'korean_name'
            }
            self.us_data = self.us_data.rename(columns=column_mapping)
            
            # 필수 컬럼 확인
            if 'hs_code' not in self.us_data.columns:
                print("❌ HS 코드 컬럼을 찾을 수 없습니다")
                return False
            
            if 'english_name' not in self.us_data.columns:
                print("❌ 영문명 컬럼을 찾을 수 없습니다")
                return False
            
            # 데이터 정리
            initial_count = len(self.us_data)
            self.us_data = self.us_data.dropna(subset=['hs_code'])
            
            # HS 코드를 문자열로 변환하고 정리
            self.us_data['hs_code'] = self.us_data['hs_code'].astype(str).str.strip()
            self.us_data['hs_code'] = self.us_data['hs_code'].str.replace('.0', '', regex=False)
            self.us_data = self.us_data[self.us_data['hs_code'] != '']
            
            # 숫자로만 구성된 코드만 필터링
            numeric_mask = self.us_data['hs_code'].str.match(r'^\d+$', na=False)
            self.us_data = self.us_data[numeric_mask]
            
            # 영문명이 있는 것만 필터링
            name_mask = self.us_data['english_name'].notna() & (self.us_data['english_name'].str.strip() != '')
            self.us_data = self.us_data[name_mask]
            
            print(f"📊 정리 후 데이터: {len(self.us_data)}개 행")
            
            if len(self.us_data) == 0:
                print("❌ 유효한 데이터가 없습니다")
                return False
            
            # HS 코드를 10자리로 표준화
            self.us_data['hs_code'] = self.us_data['hs_code'].str.ljust(10, '0')
            
            # HS 구조 정보 추가
            self.us_data['hs6'] = self.us_data['hs_code'].str[:6]
            self.us_data['chapter'] = self.us_data['hs_code'].str[:2]
            self.us_data['heading'] = self.us_data['hs_code'].str[:4]
            
            # 한글명이 없는 경우 빈 문자열로 채움
            if 'korean_name' not in self.us_data.columns:
                self.us_data['korean_name'] = ''
            else:
                self.us_data['korean_name'] = self.us_data['korean_name'].fillna('')
            
            # 통합 텍스트 생성
            self.us_data['combined_text'] = (
                self.us_data['english_name'].fillna('') + ' ' +
                self.us_data['korean_name'].fillna('')
            ).str.strip()
            
            # HS 6자리별 인덱스 구축
            self._build_us_hs6_index()
            
            print(f"✅ 미국 데이터 로딩 완료: {len(self.us_data)}개 항목, HS 6자리 {len(self.us_hs6_index)}개")
            return True
            
        except Exception as e:
            print(f"❌ 미국 데이터 로딩 실패: {e}")
            return False
    
    def _build_us_hs6_index(self):
        """미국 데이터의 HS 6자리별 인덱스 구축 + HS6 분류 설명 추출"""
        self.us_hs6_index = {}
        self.hs6_descriptions = {}
        
        for hs6, group in self.us_data.groupby('hs6'):
            # 기본 인덱스 정보
            self.us_hs6_index[hs6] = {
                'count': len(group),
                'codes': group['hs_code'].tolist(),
                'names_en': group['english_name'].tolist(),
                'names_kr': group['korean_name'].tolist(),
                'combined_texts': group['combined_text'].tolist()
            }
            
            # HS6 분류 설명 추출 (대분류 맥락)
            hs6_description = self._extract_hs6_description(group)
            if hs6_description:
                self.hs6_descriptions[hs6] = hs6_description
    
    def _extract_hs6_description(self, hs6_group) -> str:
        """HS 6자리 분류의 대표 설명 추출"""
        # 1순위: 가장 일반적인 설명 (기타가 아닌 것 중에서)
        non_other_names = []
        
        for _, row in hs6_group.iterrows():
            eng_name = str(row['english_name']).lower()
            kor_name = str(row['korean_name']).lower()
            
            # "기타", "other", "nesoi" 등이 아닌 구체적인 설명 찾기
            if not any(word in eng_name for word in ['other', 'nesoi', 'not elsewhere']) and \
               not any(word in kor_name for word in ['기타', '그 밖의', '따로 분류되지']):
                if len(eng_name) > 10:  # 충분히 구체적인 설명
                    non_other_names.append({
                        'eng': row['english_name'],
                        'kor': row['korean_name'],
                        'length': len(eng_name)
                    })
        
        # 가장 적절한 설명 선택
        if non_other_names:
            # 길이가 적당한 것 중에서 선택 (너무 길지도 짧지도 않게)
            suitable_names = [n for n in non_other_names if 15 <= n['length'] <= 100]
            if suitable_names:
                best_name = suitable_names[0]
            else:
                best_name = non_other_names[0]
            
            # 한글명이 있으면 한글명 우선, 없으면 영문명
            if best_name['kor'] and str(best_name['kor']).strip():
                return str(best_name['kor']).strip()
            else:
                return str(best_name['eng']).strip()
        
        # 2순위: 첫 번째 항목의 이름 (기타라도 사용)
        first_row = hs6_group.iloc[0]
        if first_row['korean_name'] and str(first_row['korean_name']).strip():
            return str(first_row['korean_name']).strip()
        else:
            return str(first_row['english_name']).strip()
    
    def load_korea_data_from_recommender(self) -> bool:
        """한국 HSK 데이터를 추천 시스템에서 로드"""
        if not self.korea_recommender or not hasattr(self.korea_recommender, 'integrated_df'):
            return False
        
        try:
            self.korea_data = self.korea_recommender.integrated_df.copy()
            
            # HS 구조 정보 추가
            self.korea_data['hs6'] = self.korea_data['HS_KEY'].str[:6]
            self.korea_data['chapter'] = self.korea_data['HS_KEY'].str[:2]
            self.korea_data['heading'] = self.korea_data['HS_KEY'].str[:4]
            
            # 한국 HS 6자리별 인덱스 구축
            self._build_korea_hs6_index()
            
            print(f"✅ 한국 데이터 로딩 완료: {len(self.korea_data)}개 항목, HS 6자리 {len(self.korea_hs6_index)}개")
            return True
            
        except Exception as e:
            print(f"❌ 한국 데이터 로딩 실패: {e}")
            return False
    
    def _build_korea_hs6_index(self):
        """한국 데이터의 HS 6자리별 인덱스 구축 + HS6 분류 설명 보완"""
        self.korea_hs6_index = {}
        
        for hs6, group in self.korea_data.groupby('hs6'):
            # 대표 이름 추출
            names_kr = []
            names_en = []
            combined_texts = []
            
            for _, row in group.iterrows():
                # 한글명 우선순위
                name_kr = ''
                for col in ['한글품목명', '세번10단위품명', '표준품명']:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip():
                        name_kr = str(row[col]).strip()
                        break
                
                # 영문명
                name_en = ''
                for col in ['영문품목명', '표준품명영문']:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip():
                        name_en = str(row[col]).strip()
                        break
                
                # 통합 텍스트
                combined_text = ''
                if 'final_combined_text' in row and pd.notna(row['final_combined_text']):
                    combined_text = str(row['final_combined_text'])
                
                names_kr.append(name_kr)
                names_en.append(name_en)
                combined_texts.append(combined_text)
            
            self.korea_hs6_index[hs6] = {
                'count': len(group),
                'codes': group['HS_KEY'].tolist(),
                'names_kr': names_kr,
                'names_en': names_en,
                'combined_texts': combined_texts,
                'data_sources': group['data_source'].tolist() if 'data_source' in group.columns else []
            }
            
            # 한국 데이터에서도 HS6 분류 설명 추출 (미국 데이터에 없는 경우)
            if hs6 not in self.hs6_descriptions:
                korea_hs6_desc = self._extract_korea_hs6_description(group)
                if korea_hs6_desc:
                    self.hs6_descriptions[hs6] = korea_hs6_desc
    
    def _extract_korea_hs6_description(self, hs6_group) -> str:
        """한국 데이터에서 HS 6자리 분류 설명 추출"""
        non_other_names = []
        
        for _, row in hs6_group.iterrows():
            # 한글명 우선 확인
            for col in ['한글품목명', '세번10단위품명', '표준품명']:
                if col in row and pd.notna(row[col]):
                    name = str(row[col]).strip()
                    if name and not any(word in name for word in ['기타', '그 밖의', '따로 분류되지']):
                        if len(name) > 5:  # 충분히 구체적인 설명
                            non_other_names.append(name)
                            break
        
        if non_other_names:
            # 가장 적절한 설명 선택 (길이 기준)
            suitable_names = [n for n in non_other_names if 10 <= len(n) <= 50]
            if suitable_names:
                return suitable_names[0]
            else:
                return non_other_names[0]
        
        # 첫 번째 항목 사용
        first_row = hs6_group.iloc[0]
        for col in ['한글품목명', '세번10단위품명', '표준품명']:
            if col in first_row and pd.notna(first_row[col]):
                name = str(first_row[col]).strip()
                if name:
                    return name
        
        return ""
    
    def get_hs6_description(self, hs6: str) -> str:
        """HS 6자리 분류 설명 반환"""
        return self.hs6_descriptions.get(hs6, f"HS {hs6} 분류")
    
    def lookup_us_hs_code(self, us_hs_code: str) -> Optional[Dict]:
        """미국 HS 코드 조회"""
        us_hs_code = str(us_hs_code).strip().ljust(10, '0')
        
        # 정확한 10자리 매칭
        matching_rows = self.us_data[self.us_data['hs_code'] == us_hs_code]
        
        if matching_rows.empty:
            return None
        
        row = matching_rows.iloc[0]
        hs_components = self.hs_analyzer.get_hs_components(us_hs_code)
        
        return {
            'hs_code': us_hs_code,
            'english_name': row['english_name'],
            'korean_name': row['korean_name'],
            'combined_text': row['combined_text'],
            'hs_components': hs_components
        }
    
    def get_korea_candidates_by_hs6(self, hs6: str) -> List[Dict]:
        """HS 6자리 기준으로 한국 후보군 생성"""
        if hs6 not in self.korea_hs6_index:
            return []
        
        korea_group = self.korea_hs6_index[hs6]
        candidates = []
        
        for i in range(korea_group['count']):
            candidates.append({
                'hs_code': korea_group['codes'][i],
                'name_kr': korea_group['names_kr'][i],
                'name_en': korea_group['names_en'][i],
                'combined_text': korea_group['combined_texts'][i],
                'data_source': korea_group['data_sources'][i] if korea_group['data_sources'] else ''
            })
        
        return candidates
    
    def _build_enhanced_search_query(self, us_info: Dict, additional_name: str = "") -> str:
        """HS 체계를 고려한 향상된 검색 쿼리 생성"""
        query_parts = []
        
        # 1순위: 미국 관세율표의 한글명
        if us_info['korean_name'] and us_info['korean_name'].strip():
            query_parts.append(us_info['korean_name'].strip())
        
        # 2순위: 추가 상품명
        if additional_name and additional_name.strip():
            query_parts.append(additional_name.strip())
        
        # 3순위: 영문명에서 핵심 키워드 추출
        if us_info['english_name']:
            english_keywords = self._extract_core_keywords(us_info['english_name'])
            query_parts.extend(english_keywords)
        
        # 4순위: HS 체계 기반 일반적 용어
        hs_chapter = us_info['hs_components']['chapter']
        chapter_keywords = self._get_chapter_keywords(hs_chapter)
        query_parts.extend(chapter_keywords)
        
        return ' '.join(query_parts)
    
    def _extract_core_keywords(self, english_name: str) -> List[str]:
        """영문명에서 핵심 키워드만 추출"""
        # 불용어 제거
        stopwords = {
            'of', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
            'with', 'by', 'from', 'other', 'others', 'nesoi', 'not', 'elsewhere',
            'specified', 'provided', 'including', 'excluding', 'containing',
            'having', 'being', 'used', 'suitable', 'designed', 'intended'
        }
        
        # 의미있는 단어만 추출
        words = re.findall(r'[A-Za-z]+', english_name.lower())
        keywords = []
        
        for word in words:
            if len(word) >= 3 and word not in stopwords:
                # 기술적 용어나 재질명 우선
                if any(tech in word for tech in ['digital', 'electronic', 'automatic', 'portable', 'cellular']):
                    keywords.insert(0, word)
                else:
                    keywords.append(word)
        
        return keywords[:4]
    
    def _get_chapter_keywords(self, chapter: str) -> List[str]:
        """HS 장(Chapter)별 관련 키워드 반환"""
        chapter_map = {
            '84': ['기계', '엔진', '장치', '설비'],
            '85': ['전기', '전자', '통신', '음향'],
            '87': ['자동차', '차량', '운송'],
            '73': ['철강', '금속', '제품'],
            '39': ['플라스틱', '수지', '합성'],
            '90': ['광학', '의료', '정밀', '기기'],
            '94': ['가구', '조명', '램프'],
            '95': ['완구', '게임', '스포츠']
        }
        
        return chapter_map.get(chapter, [])
    
    def _rank_candidates_by_similarity(self, search_query: str, candidates: List[Dict]) -> List[Dict]:
        """후보군을 유사도 기준으로 순위 매김"""
        if not candidates or not self.semantic_model:
            for candidate in candidates:
                candidate['similarity_score'] = 0.5
            return candidates
        
        # 후보들의 텍스트 수집
        candidate_texts = []
        for candidate in candidates:
            text_parts = []
            if candidate['name_kr']:
                text_parts.append(candidate['name_kr'])
            if candidate['name_en']:
                text_parts.append(candidate['name_en'])
            if candidate['combined_text']:
                text_parts.append(candidate['combined_text'])
            
            combined_text = ' '.join(text_parts)
            candidate_texts.append(combined_text)
        
        # 의미 유사도 계산
        try:
            query_embedding = self.semantic_model.encode([search_query])
            candidate_embeddings = self.semantic_model.encode(candidate_texts)
            similarities = cosine_similarity(query_embedding, candidate_embeddings).flatten()
                
                # 후보에 유사도 점수 추가
            for i, candidate in enumerate(candidates):
                candidate['similarity_score'] = float(similarities[i])  # NumPy float를 Python float로 변환
                
                # 유사도 기준 정렬
            ranked_candidates = sorted(candidates, key=lambda x: x['similarity_score'], reverse=True)
            return ranked_candidates
                
        except Exception as e:
            print(f"⚠️ 유사도 계산 실패: {e}")
            # 원본 순서 유지
            for candidate in candidates:
                candidate['similarity_score'] = 0.5
            return candidates   
    
    # ===========================================
    # LLM 관련 새로운 메소드들
    # ===========================================
    
    def analyze_product_with_llm(self, us_info: Dict, additional_name: str = "") -> Optional[ProductAnalysis]:
        """LLM을 활용한 상품 특성 분석"""
        if not self.llm_available:
            return None
        
        # 캐시 확인
        cache_key = f"{us_info['hs_code']}:{additional_name}"
        if cache_key in self.llm_analysis_cache:
            return self.llm_analysis_cache[cache_key]
        
        try:
            prompt = self._build_product_analysis_prompt(us_info, additional_name)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 국제무역과 HS 코드 분류 전문가입니다. 상품을 정확하게 분석하여 구조화된 정보를 제공해주세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            analysis = self._parse_llm_analysis(response.choices[0].message.content)
            
            # 캐시 저장
            if analysis:
                self.llm_analysis_cache[cache_key] = analysis
            return analysis
            
        except Exception as e:
            print(f"⚠️ LLM 상품 분석 실패: {e}")
            return None
    
    def _build_product_analysis_prompt(self, us_info: Dict, additional_name: str) -> str:
        """상품 분석용 프롬프트 생성"""
        hs_chapter = us_info['hs_components']['chapter']
        hs6 = us_info['hs_components']['hs6']
        
        return f"""
다음 상품의 특성을 전문적으로 분석해주세요:

**기본 정보**:
- 미국 HS 코드: {us_info['hs_code']} (장: {hs_chapter}, HS6: {hs6})
- 영문명: {us_info['english_name']}
- 한글명: {us_info.get('korean_name', '없음')}
- 추가 상품명: {additional_name or '없음'}

**분석 요청**:
다음 JSON 형식으로 정확하게 응답해주세요:

```json
{{
    "material": "주요 재질 (예: 플라스틱, 알루미늄, 섬유, 복합재료 등)",
    "function": "주요 기능 (예: 통신, 측정, 가공, 보관, 이동 등)",
    "target_user": "대상 사용자 (예: 일반소비자, 전문가, 산업용, 의료용 등)",
    "size_category": "크기 분류 (예: 휴대용, 탁상용, 대형산업용 등)",
    "key_features": ["주요특징1", "주요특징2", "주요특징3"],
    "alternative_hs6": ["{hs6}", "대안HS6자리1", "대안HS6자리2"],
    "reasoning": "분석 근거와 HS 분류 맥락"
}}
```

**주의사항**:
- HS 코드 체계의 논리를 고려해주세요
- 대안 HS6는 현재 {hs6}와 다르지만 실제로는 같은 상품일 가능성이 있는 분류를 제시해주세요
- JSON 형식을 정확히 지켜주세요
"""
    
    def _parse_llm_analysis(self, llm_response: str) -> Optional[ProductAnalysis]:
        """LLM 응답을 ProductAnalysis 객체로 파싱"""
        try:
            # JSON 부분만 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # JSON 블록이 없으면 전체에서 JSON 찾기
                json_text = llm_response
            
            # JSON 파싱
            data = json.loads(json_text)
            
            return ProductAnalysis(
                material=data.get('material', '알 수 없음'),
                function=data.get('function', '알 수 없음'),
                target_user=data.get('target_user', '알 수 없음'),
                size_category=data.get('size_category', '알 수 없음'),
                key_features=data.get('key_features', []),
                alternative_hs6=data.get('alternative_hs6', []),
                reasoning=data.get('reasoning', '')
            )
            
        except Exception as e:
            print(f"⚠️ LLM 응답 파싱 실패: {e}")
            return None
    
    def get_llm_suggested_candidates(self, product_analysis: ProductAnalysis) -> List[Dict]:
        """LLM이 제안한 대안 HS 분류의 한국 후보들"""
        if not product_analysis:
            return []
        
        candidates = []
        
        for alt_hs6 in product_analysis.alternative_hs6:
            if alt_hs6 in self.korea_hs6_index:
                alt_candidates = self.get_korea_candidates_by_hs6(alt_hs6)
                # 대안 후보임을 표시
                for candidate in alt_candidates:
                    candidate['is_alternative'] = True
                    candidate['source_hs6'] = alt_hs6
                candidates.extend(alt_candidates)
        
        return candidates
    
    def llm_rank_candidates(self, product_analysis: ProductAnalysis, 
                           candidates: List[Dict]) -> List[LLMRanking]:
        """LLM을 활용한 후보 순위 매김"""
        
        if not self.llm_available or not product_analysis or len(candidates) == 0:
            return []
        
        # 너무 많은 후보는 상위 15개만 LLM에게 전달
        top_candidates = candidates[:15]
        
        try:
            prompt = self._build_ranking_prompt(product_analysis, top_candidates)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 HS 코드 매칭 전문가입니다. 상품 특성을 바탕으로 가장 적합한 한국 HSK 코드를 선택해주세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            return self._parse_llm_rankings(response.choices[0].message.content)
            
        except Exception as e:
            print(f"⚠️ LLM 순위 매김 실패: {e}")
            return []
    
    def _build_ranking_prompt(self, product_analysis: ProductAnalysis, 
                             candidates: List[Dict]) -> str:
        """후보 순위 매김용 프롬프트 생성"""
        
        candidates_text = ""
        for i, candidate in enumerate(candidates, 1):
            alt_info = f" (대안분류: {candidate['source_hs6']})" if candidate.get('is_alternative') else ""
            candidates_text += f"{i}. {candidate['hs_code']}: {candidate['name_kr']}{alt_info}\n"
        
        return f"""
다음 상품 분석 결과를 바탕으로 가장 적합한 한국 HSK 코드 3개를 순위별로 선택해주세요:

**상품 특성**:
- 재질: {product_analysis.material}
- 기능: {product_analysis.function}
- 대상 사용자: {product_analysis.target_user}
- 크기 분류: {product_analysis.size_category}
- 주요 특징: {', '.join(product_analysis.key_features)}

**분석 근거**: {product_analysis.reasoning}

**후보 목록**:
{candidates_text}

다음 JSON 형식으로 정확하게 응답해주세요:

```json
{{
    "rankings": [
        {{
            "rank": 1,
            "hs_code": "가장 적합한 HSK 코드",
            "confidence": 0.95,
            "reason": "이 코드를 1순위로 선택한 구체적인 이유"
        }},
        {{
            "rank": 2,
            "hs_code": "두 번째로 적합한 HSK 코드",
            "confidence": 0.80,
            "reason": "이 코드를 2순위로 선택한 구체적인 이유"
        }},
        {{
            "rank": 3,
            "hs_code": "세 번째로 적합한 HSK 코드",
            "confidence": 0.65,
            "reason": "이 코드를 3순위로 선택한 구체적인 이유"
        }}
    ]
}}
```

**선택 기준**:
1. 상품의 재질과 기능이 가장 잘 맞는 코드
2. 대상 사용자와 용도가 일치하는 코드
3. HS 코드 체계의 논리에 부합하는 코드
"""
    
    def _parse_llm_rankings(self, llm_response: str) -> List[LLMRanking]:
        """LLM 순위 응답 파싱"""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = llm_response
            
            data = json.loads(json_text)
            rankings = []
            
            for item in data.get('rankings', []):
                rankings.append(LLMRanking(
                    rank=item.get('rank', 0),
                    hs_code=item.get('hs_code', ''),
                    confidence=item.get('confidence', 0.5),
                    reason=item.get('reason', '')
                ))
            
            return rankings
            
        except Exception as e:
            print(f"⚠️ LLM 순위 파싱 실패: {e}")
            return []
    
    def generate_matching_explanation(self, us_info: Dict, korea_match: Dict, 
                                    product_analysis: Optional[ProductAnalysis] = None) -> str:
        """LLM 기반 매칭 설명 생성"""
        
        if not self.llm_available:
            return self._generate_simple_explanation(us_info, korea_match)
        
        try:
            analysis_text = ""
            if product_analysis:
                analysis_text = f"""
**상품 분석**:
- 재질: {product_analysis.material}
- 기능: {product_analysis.function}
- 대상: {product_analysis.target_user}

**분석 근거**: {product_analysis.reasoning}"""
            
            prompt = f"""
다음 HS 코드 변환 결과에 대해 사용자가 이해하기 쉽게 설명해주세요:

**변환 결과**:
- 미국 HS: {us_info['hs_code']} - {us_info['english_name']}
- 한국 HSK: {korea_match['hs_code']} - {korea_match['name_kr']}
{analysis_text}

다음 내용을 포함해서 친근하고 이해하기 쉽게 3-4문장으로 설명해주세요:
1. 왜 이 한국 코드가 적합한지
2. 두 코드의 공통점
3. 주의사항이나 추가 확인이 필요한 부분
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 친근하고 전문적인 무역 컨설턴트입니다. 복잡한 HS 코드 내용을 쉽게 설명해주세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ 설명 생성 실패: {e}")
            return self._generate_simple_explanation(us_info, korea_match)
    
    def _generate_simple_explanation(self, us_info: Dict, korea_match: Dict) -> str:
        """간단한 설명 생성 (LLM 없을 때)"""
        us_hs6 = us_info['hs_components']['hs6']
        korea_hs6 = korea_match['hs_code'][:6]
        
        if us_hs6 == korea_hs6:
            return f"두 코드 모두 HS {us_hs6} 분류에 속하므로 국제적으로 동일한 상품군으로 인정됩니다. 한국에서는 '{korea_match['name_kr']}'로 분류되며, 세부 규정은 관세청에 확인하시기 바랍니다."
        else:
            return f"미국 코드는 HS {us_hs6} 분류이지만, 한국에서는 HS {korea_hs6} 분류({korea_match['name_kr']})로 매핑됩니다. 두 국가 간 세부 분류 체계가 다를 수 있으니 관세청 확인을 권장합니다."
    
    # ===========================================
    # 메인 변환 로직 (기존 방식 + LLM 강화)
    # ===========================================
    
    def convert_hs_code(self, us_hs_code: str, us_product_name: str = "") -> Dict:
        """HS 코드 변환 실행 (LLM 강화 버전)"""
        if not self.initialized:
            return {
                'status': 'error',
                'message': '시스템이 초기화되지 않았습니다.'
            }
        
        # 캐시 확인
        cache_key = f"{us_hs_code}:{us_product_name}"
        if cache_key in self.conversion_cache:
            cached_result = self.conversion_cache[cache_key].copy()
            cached_result['from_cache'] = True
            return cached_result
        
        # 1단계: 미국 HS 코드 조회
        us_info = self.lookup_us_hs_code(us_hs_code)
        if not us_info:
            result = {
                'status': 'error',
                'message': f"미국 HS코드 '{us_hs_code}'를 찾을 수 없습니다.",
                'us_hs_code': us_hs_code,
                'us_product_name': us_product_name,
                'suggestions': self._get_alternative_suggestions(us_hs_code)
            }
            return result
        
        # 2단계: LLM 기반 상품 특성 분석 (선택적)
        product_analysis = None
        if self.llm_available:
            product_analysis = self.analyze_product_with_llm(us_info, us_product_name)
        
        # 3단계: 후보군 생성
        hs6 = us_info['hs_components']['hs6']
        primary_candidates = self.get_korea_candidates_by_hs6(hs6)
        
        # LLM 제안 대안 후보군
        alternative_candidates = []
        if self.llm_available and product_analysis:
            alternative_candidates = self.get_llm_suggested_candidates(product_analysis)
        
        all_candidates = primary_candidates + alternative_candidates
        
        if not all_candidates:
            result = {
                'status': 'no_hs6_match',
                'message': f"HS 6자리 '{hs6}' 및 대안 분류에서 한국 코드를 찾을 수 없습니다.",
                'us_hs_code': us_hs_code,
                'us_info': us_info,
                'product_analysis': self._analysis_to_dict(product_analysis) if product_analysis else None,
                'hs6': hs6
            }
            return result
        
        # 4단계: 시맨틱 유사도 계산
        search_query = self._build_enhanced_search_query(us_info, us_product_name)
        semantic_ranked = self._rank_candidates_by_similarity(search_query, all_candidates.copy())
        
        # 5단계: LLM 기반 심층 매칭 (선택적)
        llm_rankings = []
        if self.llm_available and product_analysis and len(all_candidates) > 0:
            llm_rankings = self.llm_rank_candidates(product_analysis, semantic_ranked)
        
        # 6단계: 하이브리드 점수 계산
        final_candidates = self._calculate_hybrid_scores(
            semantic_ranked, llm_rankings, us_info['hs_code']
        )
        
        if not final_candidates:
            result = {
                'status': 'no_match',
                'message': '적합한 한국 HSK 코드를 찾을 수 없습니다.',
                'us_hs_code': us_hs_code,
                'us_info': us_info,
                'product_analysis': self._analysis_to_dict(product_analysis) if product_analysis else None
            }
            return result
        
        # 최종 추천 결과
        best_match = final_candidates[0]
        
        # 7단계: LLM 기반 설명 생성 (선택적)
        explanation = ""
        if self.llm_available:
            explanation = self.generate_matching_explanation(us_info, best_match, product_analysis)
        
        # 최종 결과 반환
        result = {
            'status': 'success',
            'method': 'llm_enhanced' if self.llm_available else 'traditional',
            'us_hs_code': us_hs_code,
            'us_product_name': us_product_name,
            'us_info': us_info,
            'korea_recommendation': {
                'hs_code': best_match['hs_code'],
                'name_kr': best_match['name_kr'],
                'name_en': best_match.get('name_en', ''),
                'data_source': best_match.get('data_source', ''),
                'confidence': float(best_match.get('final_score', 0.5)),  # float로 변환
                'is_alternative_classification': best_match.get('is_alternative', False),
                'source_hs6': best_match.get('source_hs6', hs6)
            },
            'hs_analysis': {
                'hs6_match': True,
                'hs_similarity': float(best_match.get('score_breakdown', {}).get('hs_structure', 0.5)),  # float로 변환
                'semantic_similarity': float(best_match.get('score_breakdown', {}).get('semantic', 0.5)),  # float로 변환
                'total_candidates': len(all_candidates),
                'us_hs6': hs6,
                'korea_hs6': best_match['hs_code'][:6],
                'llm_enhanced': self.llm_available
            },
            'search_query': search_query,
            'all_candidates': final_candidates[:3],
            'explanation': explanation,
            'product_analysis': self._analysis_to_dict(product_analysis) if product_analysis else None
        }
        
        # NumPy 타입 변환 적용
        result = convert_numpy_types(result)
        
        # 캐시 저장
        self.conversion_cache[cache_key] = result
        return result
    
    def _calculate_hybrid_scores(self, semantic_candidates: List[Dict], 
                                llm_rankings: List[LLMRanking], us_hs_code: str) -> List[Dict]:
        """하이브리드 점수 계산 (시맨틱 + LLM + 구조적 유사도)"""
        
        # LLM 순위를 딕셔너리로 변환
        llm_scores = {}
        for ranking in llm_rankings:
            llm_scores[ranking.hs_code] = {
                'confidence': ranking.confidence,
                'rank': ranking.rank,
                'reason': ranking.reason
            }
        
        # 각 후보에 대해 하이브리드 점수 계산
        for candidate in semantic_candidates:
            korea_code = candidate['hs_code']
            
            # 1. 시맨틱 유사도 (기존)
            semantic_score = candidate.get('similarity_score', 0.5)
            
            # 2. HS 구조적 유사도 (기존)
            hs_similarity = self.hs_analyzer.calculate_hs_similarity(us_hs_code, korea_code)
            
             # 3. LLM 신뢰도
            llm_score = 0.5  # 기본값
            llm_reason = ""
            if korea_code in llm_scores:
                llm_info = llm_scores[korea_code]
                llm_score = float(llm_info['confidence'])  # float로 변환
                llm_reason = llm_info['reason']
                # 순위가 높을수록 추가 보너스
                rank_bonus = max(0, (4 - llm_info['rank']) * 0.1)
                llm_score = min(1.0, llm_score + rank_bonus)
            
            # 가중 평균 계산
            if self.llm_available and llm_rankings:
                # LLM 사용 가능시: 시맨틱 25% + LLM 55% + 구조적 20%
                final_score = (semantic_score * 0.25) + (llm_score * 0.55) + (hs_similarity * 0.20)
            else:
                # LLM 없을 시: 시맨틱 50% + 구조적 50% (기존과 동일)
                final_score = (semantic_score * 0.5) + (hs_similarity * 0.5)
            
            # 대안 분류 페널티 (기본 HS6가 아닌 경우 약간 감점)
            if candidate.get('is_alternative', False):
                final_score *= 0.9
            
            candidate['final_score'] = float(final_score)  # float로 변환
            candidate['score_breakdown'] = {
                'semantic': float(semantic_score),  # float로 변환
                'hs_structure': float(hs_similarity),  # float로 변환
                'llm_confidence': float(llm_score),  # float로 변환
                'llm_reason': llm_reason
            }
        
        # 최종 점수 기준으로 정렬
        return sorted(semantic_candidates, key=lambda x: x['final_score'], reverse=True)

    
    def _analysis_to_dict(self, analysis: Optional[ProductAnalysis]) -> Optional[Dict]:
        """ProductAnalysis를 딕셔너리로 변환"""
        if not analysis:
            return None
        
        return {
            'material': analysis.material,
            'function': analysis.function,
            'target_user': analysis.target_user,
            'size_category': analysis.size_category,
            'key_features': analysis.key_features,
            'alternative_hs6': analysis.alternative_hs6,
            'reasoning': analysis.reasoning
        }
    
    def _get_alternative_suggestions(self, us_hs_code: str) -> List[str]:
        """유사한 HS 코드 대안 제시"""
        if self.us_data is None:
            return []
        
        suggestions = []
        
        # 1. 앞 6자리 기준 유사 코드
        if len(us_hs_code) >= 6:
            hs6 = us_hs_code[:6]
            similar_6 = self.us_data[self.us_data['hs_code'].str.startswith(hs6)]
            suggestions.extend(similar_6['hs_code'].head(3).tolist())
        
        # 2. 앞 4자리 기준 유사 코드
        if len(us_hs_code) >= 4 and len(suggestions) < 3:
            hs4 = us_hs_code[:4]
            similar_4 = self.us_data[self.us_data['hs_code'].str.startswith(hs4)]
            suggestions.extend(similar_4['hs_code'].head(5-len(suggestions)).tolist())
        
        # 3. 장(Chapter) 기준 유사 코드
        if len(us_hs_code) >= 2 and len(suggestions) < 3:
            chapter = us_hs_code[:2]
            similar_chapter = self.us_data[self.us_data['chapter'] == chapter]
            suggestions.extend(similar_chapter['hs_code'].head(5-len(suggestions)).tolist())
        
        return list(set(suggestions))  # 중복 제거
    
    def get_system_statistics(self) -> Dict:
        """시스템 통계 반환 (LLM 정보 포함)"""
        stats = {
            'system_status': {
                'initialized': self.initialized,
                'us_data_loaded': self.us_data is not None,
                'korea_data_loaded': self.korea_data is not None,
                'semantic_model_loaded': self.semantic_model is not None,
                'openai_available': self.openai_client is not None,
                'llm_available': self.llm_available,
                'conversion_cache_size': len(self.conversion_cache),
                'llm_analysis_cache_size': len(self.llm_analysis_cache),
                'llm_ranking_cache_size': len(self.llm_ranking_cache)
            }
        }

        if self.us_data is not None:
            stats['us_data'] = {
                'total_codes': len(self.us_data),
                'unique_hs6': len(self.us_hs6_index),
                'unique_chapters': len(self.us_data['chapter'].unique()),
                'has_korean_names': (~self.us_data['korean_name'].isna()).sum(),
                'hs6_descriptions': len(self.hs6_descriptions)
            }

        if self.korea_data is not None:
            stats['korea_data'] = {
                'total_codes': len(self.korea_data),
                'unique_hs6': len(self.korea_hs6_index),
                'unique_chapters': len(self.korea_data['chapter'].unique())
            }

        # HS 6자리 교집합 분석
        if self.us_hs6_index and self.korea_hs6_index:
            us_hs6_set = set(self.us_hs6_index.keys())
            korea_hs6_set = set(self.korea_hs6_index.keys())
            stats['hs6_analysis'] = {
                'us_only_hs6': len(us_hs6_set - korea_hs6_set),
                'korea_only_hs6': len(korea_hs6_set - us_hs6_set),
                'common_hs6': len(us_hs6_set & korea_hs6_set),
                'coverage_rate': len(us_hs6_set & korea_hs6_set) / len(us_hs6_set) * 100 if us_hs6_set else 0
            }

        return stats

    def clear_cache(self):
        """변환 캐시 초기화"""
        cache_size = len(self.conversion_cache)
        llm_cache_size = len(self.llm_analysis_cache) + len(self.llm_ranking_cache)
        self.conversion_cache.clear()
        self.llm_analysis_cache.clear()
        self.llm_ranking_cache.clear()
        return cache_size + llm_cache_size


def main():
    """대화형 HS 코드 변환 시스템 (LLM 강화)"""
    print("="*80)
    print("🚀 HS Code Converter - 미국→한국 HS코드 변환 시스템 (LLM 강화)")
    print("="*80)
    
    # .env 파일 로드 및 OpenAI API 키 가져오기
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"환경 변수 파일 로드: {env_file}")
    else:
        print(f"환경 변수 파일이 없음: {env_file}")
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        print("📊 기본 모드로 실행합니다 (환경변수에서 OpenAI API 키를 찾을 수 없음).")
    else:
        print("🤖 LLM 강화 모드로 실행합니다 (환경변수에서 OpenAI API 키 로드).")
    
    # 변환 시스템 초기화
    us_tariff_file = project_root / "us_tariff_table_20250714.xlsx"
    
    # 한국 추천 시스템 로드 시도
    korea_recommender = None
    try:
        from hs_recommender import HSCodeRecommender
        
        cache_dir = project_root /"cache"/ "hs_code_cache"
        korea_recommender = HSCodeRecommender(cache_dir=str(cache_dir))
        if korea_recommender.load_data():
            print("✅ 한국 추천 시스템 로드 완료")
        else:
            print("⚠️ 한국 추천 시스템 로드 실패")
            korea_recommender = None
    except ImportError:
        print("⚠️ 한국 추천 시스템 모듈을 찾을 수 없음")
        korea_recommender = None
    
    # LLM 강화 변환기 초기화
    converter = HSCodeConverterService(
        str(us_tariff_file), 
        korea_recommender, 
        openai_api_key if openai_api_key else None
    )
    
    # 시스템 초기화
    print("\n🚀 시스템 초기화 중...")
    success, message = converter.initialize_system()
    print(f"🚀 {message}")
    
    if not success:
        print("❌ 시스템 초기화 실패로 프로그램을 종료합니다.")
        return
    
    # 시스템 상태 표시
    print_system_status(converter)
    
    # 대화형 변환 시작
    print("\n" + "="*80)
    print("🎯 대화형 HS 코드 변환 시작")
    print("="*80)
    print("💡 사용법:")
    print("- 미국 HS 코드를 입력하세요 (4-10자리 숫자)")
    print("- 상품명은 선택사항입니다 (LLM 사용시 더 정확한 분석 가능)")
    print("- 'quit', 'exit', 'q' 입력시 종료")
    print("- 'status' 입력시 시스템 상태 확인")
    print("- 'cache' 입력시 캐시 정보 확인")
    print("="*80)
    
    while True:
        try:
            print("\n" + "-"*50)
            
            # HS 코드 입력
            us_hs_code = input("🔢 미국 HS 코드를 입력하세요: ").strip()
            
            # 종료 명령어 확인
            if us_hs_code.lower() in ['quit', 'exit', 'q']:
                print("👋 프로그램을 종료합니다.")
                break
            
            # 특별 명령어 처리
            if us_hs_code.lower() == 'status':
                print_system_status(converter)
                continue
            
            if us_hs_code.lower() == 'cache':
                print_cache_info(converter)
                continue
            
            # HS 코드 유효성 검사
            if not us_hs_code:
                print("❌ HS 코드를 입력해주세요.")
                continue
            
            if not re.match(r'^\d{4,10}$', us_hs_code):
                print("❌ 올바른 HS 코드를 입력하세요 (4-10자리 숫자)")
                print("💡 예시: 8471300000, 9507109000")
                continue
            
            # 상품명 입력 (선택사항)
            llm_hint = " (LLM 분석에 도움됨)" if converter.llm_available else ""
            product_name = input(f"📦 상품명 (선택사항{llm_hint}): ").strip()
            
            print(f"\n변환 중... [{us_hs_code}" + (f" - {product_name}" if product_name else "") + "]")
            print("-"*50)
            
            # 변환 실행
            result = converter.convert_hs_code(us_hs_code, product_name)
            
            # 결과 출력
            if result['status'] == 'success':
                print_enhanced_success_result(result, converter)
            elif result['status'] == 'error':
                print_error_result(result)
            elif result['status'] == 'no_hs6_match':
                print_no_match_result(result, converter)
            else:
                print(f"❌ 알 수 없는 오류: {result.get('message', '오류 정보 없음')}")
            
            # 계속할지 묻기
            print("\n" + "-"*50)
            continue_choice = input("다른 코드를 변환하시겠습니까? (Enter: 계속, q: 종료): ").strip()
            if continue_choice.lower() in ['q', 'quit', 'exit']:
                print("👋 프로그램을 종료합니다.")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 사용자에 의해 프로그램이 종료되었습니다.")
            break
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
            continue

def print_system_status(converter):
    """시스템 상태 출력 (LLM 정보 포함)"""
    print("\n" + "="*50)
    print("📊 시스템 상태")
    print("="*50)
    
    stats = converter.get_system_statistics()
    
    print("✅ **기본 상태**")
    print(f"- 초기화: {'✅ 완료' if converter.initialized else '❌ 미완료'}")
    print(f"- 미국 데이터: {'✅ 로드됨' if converter.us_data is not None else '❌ 없음'}")
    print(f"- 한국 데이터: {'✅ 로드됨' if converter.korea_data is not None else '❌ 없음'}")
    print(f"- 시맨틱 모델: {'✅ 로드됨' if converter.semantic_model is not None else '❌ 없음'}")
    print(f"- LLM 기능: {'🤖 활성화' if converter.llm_available else '❌ 비활성화'}")
    print(f"- 동작 모드: {'🚀 LLM 강화' if converter.llm_available else '📊 기본 모드'}")
    
    if converter.us_data is not None:
        print(f"\n📊 **미국 데이터**")
        print(f"- 총 코드 수: {len(converter.us_data):,}개")
        print(f"- HS 6자리 종류: {len(converter.us_hs6_index):,}개")
        print(f"- 장(Chapter) 종류: {len(converter.us_data['chapter'].unique())}개")
    
    if converter.korea_data is not None:
        print(f"\n📊 **한국 데이터**")
        print(f"- 총 코드 수: {len(converter.korea_data):,}개")
        print(f"- HS 6자리 종류: {len(converter.korea_hs6_index):,}개")
    
    if converter.llm_available:
        print(f"\n🤖 **LLM 캐시**")
        print(f"- 상품 분석 캐시: {len(converter.llm_analysis_cache)}개")
        print(f"- 순위 분석 캐시: {len(converter.llm_ranking_cache)}개")

def print_cache_info(converter):
    """캐시 정보 출력 (LLM 캐시 포함)"""
    print("\n" + "="*50)
    print("💾 캐시 정보")
    print("="*50)
    
    cache_size = len(converter.conversion_cache)
    llm_analysis_size = len(converter.llm_analysis_cache)
    llm_ranking_size = len(converter.llm_ranking_cache)
    
    print(f"- 변환 캐시: {cache_size}개 항목")
    if converter.llm_available:
        print(f"- LLM 분석 캐시: {llm_analysis_size}개 항목")
        print(f"- LLM 순위 캐시: {llm_ranking_size}개 항목")
    
    if cache_size > 0:
        print(f"\n📋 **최근 변환 내역** (최대 5개)")
        for i, (cache_key, result) in enumerate(list(converter.conversion_cache.items())[-5:], 1):
            us_code, product_name = cache_key.split(':', 1)
            status = result.get('status', 'unknown')
            method = result.get('method', 'unknown')
            print(f"{i}. {us_code}" + (f" ({product_name})" if product_name else "") + f" - {status} ({method})")
        
        clear_choice = input("\n🗑️ 모든 캐시를 초기화하시겠습니까? (y/N): ").strip()
        if clear_choice.lower() in ['y', 'yes']:
            cleared_count = converter.clear_cache()
            print(f"✅ 캐시 초기화 완료 ({cleared_count}개 항목 삭제)")

def is_other_item(text):
    """텍스트에서 기타 항목 여부 확인"""
    if not text:
        return False
    
    text_lower = str(text).lower().strip()
    
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
        return korea_name or ""
    
    if is_other_item(korea_name):
        return f"{hs6_description} 분야의 기타 항목"
    else:
        return korea_name

def get_display_width(text):
    """텍스트의 실제 표시 폭 계산 (한글 2, 영문/숫자 1)"""
    if not text:
        return 0
    
    width = 0
    for char in str(text):
        # 한글, 한자, 일본어 등은 폭이 2
        if ord(char) > 127:
            width += 2
        else:
            width += 1
    return width

def truncate_text_to_width(text, max_width):
    """지정된 폭에 맞게 텍스트 자르기"""
    if not text:
        return ""
    
    text = str(text)
    current_width = 0
    result = ""
    
    for char in text:
        char_width = 2 if ord(char) > 127 else 1
        if current_width + char_width > max_width:
            if max_width >= 3:  # "..." 추가할 공간이 있으면
                # 기존 텍스트에서 "..." 공간 확보
                while get_display_width(result + "...") > max_width and result:
                    result = result[:-1]
                result += "..."
            break
        result += char
        current_width += char_width
    
    return result

def pad_text_to_width(text, target_width):
    """텍스트를 지정된 폭에 맞게 패딩"""
    if not text:
        text = ""
    
    current_width = get_display_width(text)
    padding_needed = target_width - current_width
    
    if padding_needed > 0:
        return text + " " * padding_needed
    else:
        return text

def print_candidates_table(candidates, hs6_description):
    """후보 목록을 정렬된 테이블로 출력"""
    
    # 테이블 폭 설정
    rank_width = 4
    code_width = 13
    name_width = 36  # 상품명 폭
    similarity_width = 8
    
    # 헤더 출력
    print("┌" + "─" * rank_width + "┬" + "─" * code_width + "┬" + "─" * name_width + "┬" + "─" * similarity_width + "┐")
    
    # 헤더 텍스트
    rank_header = pad_text_to_width("순위", rank_width)
    code_header = pad_text_to_width("HSK 코드", code_width)
    name_header = pad_text_to_width("상품명", name_width)
    similarity_header = pad_text_to_width("유사도", similarity_width)
    
    print(f"│{rank_header}│{code_header}│{name_header}│{similarity_header}│")
    print("├" + "─" * rank_width + "┼" + "─" * code_width + "┼" + "─" * name_width + "┼" + "─" * similarity_width + "┤")
    
    # 데이터 행 출력
    for i, candidate in enumerate(candidates, 1):
        final_score = candidate.get('final_score', 0.0)
        
        # 후보 상품명도 맥락 정보와 함께 표시
        candidate_name = enhance_product_name_with_context(
            candidate['name_kr'], 
            hs6_description
        )
        
        # 각 컬럼 데이터 포맷팅
        rank_text = pad_text_to_width(str(i), rank_width)
        code_text = pad_text_to_width(candidate['hs_code'], code_width)
        
        # 상품명은 길이에 맞게 자르고 패딩
        name_truncated = truncate_text_to_width(candidate_name, name_width)
        name_text = pad_text_to_width(name_truncated, name_width)
        
        similarity_text = pad_text_to_width(f"{final_score:.1%}", similarity_width)
        
        print(f"│{rank_text}│{code_text}│{name_text}│{similarity_text}│")
    
    # 하단 경계
    print("└" + "─" * rank_width + "┴" + "─" * code_width + "┴" + "─" * name_width + "┴" + "─" * similarity_width + "┘")

def print_enhanced_success_result(result, converter):
    """성공 결과 출력 (LLM 강화 버전)"""
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
    
    # 결과 헤더
    method_icon = "🤖" if result.get('method') == 'llm_enhanced' else "📊"
    method_text = "LLM 강화 변환 성공!" if result.get('method') == 'llm_enhanced' else "기본 변환 성공!"
    print(f"{method_icon} **{method_text}**\n")
    
    # 캐시 정보
    if result.get('from_cache'):
        print("💾 (캐시에서 로드됨)\n")
    
    print("📋 **미국 HS 코드 정보**")
    print(f"- 코드: {result['us_hs_code']}")
    print(f"- 영문명: {us_info['english_name']}")
    print(f"- 한글명: {us_info.get('korean_name', '없음')}")
    
    # LLM 분석 결과 표시
    if result.get('product_analysis'):
        analysis = result['product_analysis']
        print(f"\n🧠 **LLM 상품 분석**")
        print(f"- 재질: {analysis['material']}")
        print(f"- 기능: {analysis['function']}")
        print(f"- 대상: {analysis['target_user']}")
        print(f"- 크기: {analysis['size_category']}")
        if analysis['key_features']:
            print(f"- 특징: {', '.join(analysis['key_features'])}")
    
    print(f"\n🎯 **추천 한국 HSK 코드**")
    print(f"- 코드: {korea_rec['hs_code']}")
    print(f"- 상품명: {enhanced_korea_name}")
    print(f"- 신뢰도: {korea_rec['confidence']:.1%}")
    print(f"- 데이터 출처: {korea_rec.get('data_source', '통합')}")
    
    # 대안 분류 정보
    if korea_rec.get('is_alternative_classification'):
        print(f"- 분류 유형: 대안 분류 (HS {korea_rec['source_hs6']})")
    
    print(f"\n📊 **분석 정보**")
    print(f"- HS 6자리 매칭: ✅ 완료 ({hs_analysis['us_hs6']})")
    print(f"- 구조 유사도: {hs_analysis['hs_similarity']:.1%}")
    print(f"- 의미 유사도: {hs_analysis['semantic_similarity']:.1%}")
    print(f"- 후보군 수: {hs_analysis['total_candidates']}개")
    
    # LLM 설명
    if result.get('explanation'):
        print(f"\n💬 **매칭 설명**")
        print(f"{result['explanation']}")
    
    # 기타 항목인 경우 맥락 설명 추가
    if is_other_item(us_info.get('english_name', '')) or is_other_item(korea_rec.get('name_kr', '')):
        print(f"\n💡 **분야 맥락**")
        print(f"- HS {hs6} 분류: {hs6_description}")
        print(f"- 해석: 이는 '{hs6_description} 분야의 기타 항목'을 의미합니다.")
    
    # 상위 후보 목록 (개선된 테이블) - 3개 모두 표시
    if 'all_candidates' in result and result['all_candidates']:
        print(f"\n🎯 **상위 후보 목록**")
        print_candidates_table(result['all_candidates'][:3], hs6_description)

def print_success_result(result, converter):
    """기존 성공 결과 출력 (호환성 유지)"""
    print_enhanced_success_result(result, converter)

def print_error_result(result):
    """오류 결과 출력"""
    print("❌ **오류 발생**\n")
    print(f"메시지: {result['message']}")
    
    if 'suggestions' in result and result['suggestions']:
        print(f"\n💡 **유사한 코드 제안:**")
        for suggestion in result['suggestions'][:3]:
            print(f"- {suggestion}")

def print_no_match_result(result, converter):
    """HS 6자리 매칭 실패 결과 출력"""
    print("❌ **HS 6자리 매칭 실패**\n")
    print(f"미국 HS 코드 '{result['us_hs_code']}'의 HS 6자리 '{result['hs6']}'에 해당하는 한국 코드가 없습니다.\n")
    
    print("📋 **미국 코드 정보**")
    print(f"- 영문명: {result['us_info']['english_name']}")
    print(f"- 한글명: {result['us_info'].get('korean_name', '없음')}")
    
    # LLM 분석 결과가 있으면 표시
    if result.get('product_analysis'):
        analysis = result['product_analysis']
        print(f"\n🧠 **LLM 상품 분석**")
        print(f"- 재질: {analysis['material']}")
        print(f"- 기능: {analysis['function']}")
        print(f"- 분석: {analysis['reasoning']}")
    
    print(f"\n💡 **분야 맥락**")
    hs6_description = converter.get_hs6_description(result['hs6'])
    print(f"- HS {result['hs6']} 분류: {hs6_description}")
    print(f"- 이 상품은 {hs6_description} 분야에 속하지만 한국에서는 다른 분류 체계를 사용하거나")
    print(f"  해당 상품이 취급되지 않을 가능성이 있습니다.")

if __name__ == "__main__":
    main()

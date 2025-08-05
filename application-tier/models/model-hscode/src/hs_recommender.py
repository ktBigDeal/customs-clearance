
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import os

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

from data_processor import DataProcessor
from search_engine import SearchEngine
from cache_manager import CacheManager
from config import SYSTEM_CONFIG

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class HSCodeRecommender:
    """HS 코드 추천 시스템 메인 클래스 (final_combined_text 지원)"""
    
    def __init__(self, semantic_model_name: str = None, top_k: int = None, cache_dir: str = './cache'):
        self.semantic_model_name = semantic_model_name or SYSTEM_CONFIG['semantic_model']
        self.top_k = top_k or SYSTEM_CONFIG['top_k']
        self.cache_dir = cache_dir
        
        # 컴포넌트 초기화
        self.data_processor = DataProcessor(debug_mode=False)
        self.search_engine = SearchEngine(self.semantic_model_name)
        self.cache_manager = CacheManager(cache_dir)
        
        # 상태 변수
        self.is_initialized = False
        self.openai_client = None
        self.integrated_df = None
        
        print(f"HS 코드 추천 시스템 초기화")
        print(f"  의미 모델: {self.semantic_model_name}")
        print(f"  상위 결과 수: {self.top_k}")
        print(f"  캐시 디렉토리: {self.cache_dir}")
    
    def initialize_openai(self) -> bool:
        """OpenAI API 초기화"""
        if not OPENAI_AVAILABLE:
            print("OpenAI 라이브러리가 설치되지 않았습니다")
            return False
        
        try:
            api_file = SYSTEM_CONFIG.get('openai_api_file', 'openai_api.txt')
            
            if os.path.exists(api_file):
                with open(api_file, 'r', encoding='utf-8') as f:
                    api_key = f.read().strip()
                
                self.openai_client = openai.OpenAI(api_key=api_key)
                
                # 간단한 테스트 호출
                test_response = self.openai_client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": "안녕하세요"}],
                    max_tokens=10
                )
                
                print("OpenAI API 초기화 성공")
                return True
            else:
                print(f"API 키 파일이 없습니다: {api_file}")
                return False
                
        except Exception as e:
            print(f"OpenAI API 초기화 실패: {e}")
            return False
    
    def load_data(self, force_rebuild: bool = False) -> bool:
        """데이터 로드 및 인덱스 구축 (final_combined_text 지원)"""
        try:
            # 캐시 확인
            if not force_rebuild and self.cache_manager.is_cache_valid(self.semantic_model_name):
                print("유효한 캐시 발견 - 캐시에서 로드")
                cache_data = self.cache_manager.load_cache()
                
                if cache_data:
                    self.integrated_df = cache_data['integrated_df']
                    
                    # final_combined_text 컬럼 확인
                    if 'final_combined_text' not in self.integrated_df.columns:
                        print("  ❌ 캐시된 데이터에 final_combined_text 컬럼이 없습니다!")
                        print("  데이터를 다시 로드합니다...")
                        force_rebuild = True
                    else:
                        # 검색 엔진에 데이터 로드
                        if self.search_engine.load_data(
                            self.integrated_df,
                            cache_data.get('standard_mapping', {}),
                            cache_data.get('reverse_mapping', {}),
                            cache_data.get('chapter_descriptions', {})
                        ):
                            # 인덱스 복원
                            self.search_engine.tfidf_matrix = cache_data['tfidf_matrix']
                            self.search_engine.tfidf_vectorizer = cache_data['tfidf_vectorizer']
                            self.search_engine.semantic_embeddings = cache_data['semantic_embeddings']
                            
                            self.is_initialized = True
                            print("캐시에서 데이터 로드 완료!")
                            return True
                        else:
                            force_rebuild = True
            
            # 캐시가 유효하지 않거나 강제 재구축
            if force_rebuild or not self.is_initialized:
                print("데이터 새로 로드 및 인덱스 구축 중...")
                
                # 1. 데이터 로드 및 통합
                if not self.data_processor.load_all_data():
                    print("데이터 로드 실패")
                    return False
                
                self.integrated_df = self.data_processor.get_integrated_data()
                chapter_descriptions = self.data_processor.get_chapter_descriptions()
                
                # final_combined_text 컬럼 확인
                if 'final_combined_text' not in self.integrated_df.columns:
                    print("❌ 로드된 데이터에 final_combined_text 컬럼이 없습니다!")
                    return False
                
                print(f"✅ 데이터 로드 완료: {len(self.integrated_df)}개 항목")
                
                # 2. 표준품명 매핑 구축
                standard_mapping, reverse_mapping = self._build_standard_mappings()
                
                # 3. 검색 엔진에 데이터 로드 및 인덱스 구축
                if not self.search_engine.load_data(self.integrated_df, standard_mapping, reverse_mapping, chapter_descriptions):
                    print("검색 엔진 데이터 로드 실패")
                    return False
                
                self.search_engine.build_index()
                
                # 4. 캐시 저장
                self.cache_manager.save_cache(
                    self.integrated_df,
                    self.search_engine.semantic_embeddings,
                    self.search_engine.tfidf_matrix,
                    self.search_engine.tfidf_vectorizer,
                    standard_mapping,
                    reverse_mapping,
                    chapter_descriptions,
                    self.semantic_model_name
                )
                
                self.is_initialized = True
                print("✅ 모든 초기화 완료!")
            
            return True
            
        except Exception as e:
            print(f"데이터 로드 중 오류 발생: {e}")
            return False
    
    def _build_standard_mappings(self) -> tuple:
        """표준품명 매핑 구축"""
        print("표준품명 매핑 구축 중...")
        
        standard_mapping = {}
        reverse_mapping = {}
        
        if self.integrated_df is None:
            return standard_mapping, reverse_mapping
        
        # 표준품명 관련 컬럼 찾기
        std_columns = []
        for col in self.integrated_df.columns:
            if any(keyword in col.lower() for keyword in ['표준품명', 'standard', '품명']):
                if col not in ['HS_KEY', 'final_combined_text', 'data_source']:
                    std_columns.append(col)
        
        mapping_count = 0
        
        for _, row in self.integrated_df.iterrows():
            hs_key = row.get('HS_KEY', '')
            if not hs_key:
                continue
            
            # 표준품명들 수집
            standard_names = set()
            for col in std_columns:
                if pd.notna(row[col]):
                    name = str(row[col]).strip().lower()
                    if name and len(name) > 1:
                        standard_names.add(name)
            
            # 매핑 구축
            for std_name in standard_names:
                if std_name not in standard_mapping:
                    standard_mapping[std_name] = []
                if hs_key not in standard_mapping[std_name]:
                    standard_mapping[std_name].append(hs_key)
                
                if hs_key not in reverse_mapping:
                    reverse_mapping[hs_key] = []
                if std_name not in reverse_mapping[hs_key]:
                    reverse_mapping[hs_key].append(std_name)
                
                mapping_count += 1
        
        print(f"  매핑 완료: {len(standard_mapping)}개 표준품명, {mapping_count}개 매핑")
        return standard_mapping, reverse_mapping
    
    def recommend(self, query: str, material: str = "", usage: str = "", 
                  use_llm: bool = False, final_count: int = 3) -> Dict:
        """HS 코드 추천 실행"""
        if not self.is_initialized:
            raise ValueError("시스템이 초기화되지 않았습니다. load_data()를 먼저 실행하세요.")
        
        print(f"\n{'='*60}")
        print(f"HS 코드 추천 실행")
        print(f"{'='*60}")
        print(f"쿼리: '{query}'")
        if material:
            print(f"재질: '{material}'")
        if usage:
            print(f"용도: '{usage}'")
        print(f"LLM 분석: {'사용' if use_llm else '미사용'}")
        
        try:
            # 1. 하이브리드 검색 실행
            search_results = self.search_engine.search(query, material, usage)
            
            if len(search_results) == 0:
                return {
                    'query': query,
                    'material': material,
                    'usage': usage,
                    'recommendations': [],
                    'search_info': {'total_candidates': 0, 'llm_analysis': None}
                }
            
            # 2. LLM 분석 (선택적)
            llm_analysis = None
            if use_llm and self.openai_client:
                llm_analysis = self._analyze_with_llm(query, material, usage, search_results.head(10))
            
            # 3. 최종 추천 결과 생성
            recommendations = self._format_recommendations(search_results.head(final_count * 2), llm_analysis, final_count)
            
            return {
                'query': query,
                'material': material,
                'usage': usage,
                'recommendations': recommendations[:final_count],
                'search_info': {
                    'total_candidates': len(search_results),
                    'semantic_model': self.semantic_model_name,
                    'llm_analysis': llm_analysis,
                    'expanded_query': search_results.iloc[0]['expanded_query'] if len(search_results) > 0 else query
                }
            }
            
        except Exception as e:
            print(f"추천 중 오류 발생: {e}")
            return {
                'query': query,
                'material': material,
                'usage': usage,
                'recommendations': [],
                'search_info': {'error': str(e), 'total_candidates': 0}
            }
    
    def _analyze_with_llm(self, query: str, material: str, usage: str, candidates: pd.DataFrame) -> Optional[Dict]:
        """LLM을 활용한 후보 분석"""
        try:
            # 후보 정보 준비
            candidate_info = []
            for idx, row in candidates.head(3).iterrows():
                hs_key = row.get('HS_KEY', '')
                hs_code = row.get('HS부호', hs_key)
                
                # 이름 정보
                name_kr = ''
                for col in ['한글품목명', '세번10단위품명', '표준품명']:
                    if col in row and pd.notna(row[col]):
                        name_kr = str(row[col])
                        break
                
                # 설명 정보
                description = ''
                if 'final_combined_text' in row and pd.notna(row['final_combined_text']):
                    description = str(row['final_combined_text'])[:200]
                
                candidate_info.append({
                    'hs_code': hs_code,
                    'name_kr': name_kr,
                    'description': description,
                    'score': row.get('hybrid_score', 0)
                })
            
            # LLM 프롬프트 구성
            prompt = f"""다음 상품에 대한 HS 코드 추천을 분석해주세요:

상품 정보:
- 상품명: {query}
- 재질: {material if material else '명시되지 않음'}
- 용도: {usage if usage else '명시되지 않음'}

추천 후보들:
"""
            
            for i, candidate in enumerate(candidate_info, 1):
                prompt += f"""
{i}. HS코드: {candidate['hs_code']}
   한글명: {candidate['name_kr']}
   설명: {candidate['description'][:100]}...
   점수: {candidate['score']:.3f}
"""
            
            prompt += """
각 후보에 대해 분석 후 JSON 형식으로 응답해주세요:
{
  "analysis": [
    {
      "hs_code": "코드",
      "fitness_score": 점수(1-10),
      "reason": "추천 이유",
      "caution": "주의사항"
    }
  ],
  "recommendation": "전체적인 추천 의견"
}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "당신은 HS 코드 분류 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            try:
                import json
                return json.loads(response.choices[0].message.content)
            except:
                return {"analysis": [], "recommendation": response.choices[0].message.content}
                
        except Exception as e:
            print(f"LLM 분석 실패: {e}")
            return None
    
    def _format_recommendations(self, search_results: pd.DataFrame, llm_analysis: Optional[Dict], final_count: int) -> List[Dict]:
        """추천 결과 포맷팅"""
        recommendations = []
        
        # LLM 분석 결과를 딕셔너리로 변환
        llm_scores = {}
        if llm_analysis and 'analysis' in llm_analysis:
            for item in llm_analysis['analysis']:
                hs_code = item.get('hs_code', '')
                llm_scores[hs_code] = {
                    'fitness_score': item.get('fitness_score', 0),
                    'reason': item.get('reason', ''),
                    'caution': item.get('caution', '')
                }
        
        for idx, row in search_results.iterrows():
            hs_key = row.get('HS_KEY', '')
            hs_code = row.get('HS부호', hs_key)
            
            # 이름 정보
            name_kr = self._extract_best_name(row, ['한글품목명', '세번10단위품명', '표준품명'])
            name_en = self._extract_best_name(row, ['영문품목명', '표준품명영문'])
            
            # 설명 정보
            description = ''
            if 'final_combined_text' in row and pd.notna(row['final_combined_text']):
                description = str(row['final_combined_text'])
            
            # 점수 및 신뢰도
            hybrid_score = row.get('hybrid_score', 0)
            confidence = min(hybrid_score, 1.0)
            
            # LLM 점수 반영
            llm_info = llm_scores.get(hs_code, {})
            if llm_info.get('fitness_score'):
                llm_fitness = llm_info['fitness_score'] / 10.0
                confidence = (confidence + llm_fitness) / 2
            
            recommendation = {
                'hs_code': hs_code,
                'hs_key': hs_key,
                'name_kr': name_kr,
                'name_en': name_en,
                'description': description[:500] if description else '',
                'chapter': row.get('chapter', hs_key[:2] if hs_key else ''),
                'heading': row.get('heading', hs_key[:4] if hs_key else ''),
                'confidence': round(confidence, 4),
                'scores': {
                    'hybrid': round(hybrid_score, 4),
                    'keyword': round(row.get('keyword_score', 0), 4),
                    'semantic': round(row.get('semantic_score', 0), 4)
                },
                'data_source': row.get('data_source', ''),
                'is_standard_match': row.get('is_standard_match', False)
            }
            
            if llm_info:
                recommendation['llm_analysis'] = llm_info
            
            recommendations.append(recommendation)
            
            if len(recommendations) >= final_count:
                break
        
        return recommendations
    
    def _extract_best_name(self, row: pd.Series, column_candidates: List[str]) -> str:
        """우선순위에 따라 최적의 이름 추출"""
        for col in column_candidates:
            if col in row and pd.notna(row[col]):
                name = str(row[col]).strip()
                if name and len(name) > 1:
                    return name
        return ''
    
    def print_results(self, results: Dict, query: str):
        """추천 결과 출력"""
        print(f"\n{'='*80}")
        print(f"'{query}' 검색 결과")
        print(f"{'='*80}")
        
        recommendations = results.get('recommendations', [])
        
        if not recommendations:
            print("추천 결과가 없습니다.")
            return
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. HS 코드: {rec['hs_code']}")
            print(f"   한글명: {rec['name_kr']}")
            if rec['name_en']:
                print(f"   영문명: {rec['name_en']}")
            print(f"   신뢰도: {rec['confidence']:.3f}")
            print(f"   장: {rec['chapter']}, 호: {rec['heading']}")
            
            if rec.get('description'):
                desc = rec['description']
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                print(f"   설명: {desc}")
            
            # LLM 분석 결과
            if rec.get('llm_analysis'):
                llm = rec['llm_analysis']
                if llm.get('reason'):
                    print(f"   AI 분석: {llm['reason']}")
                if llm.get('caution'):
                    print(f"   주의사항: {llm['caution']}")
            
            print(f"   데이터 소스: {rec.get('data_source', '')}")
        
        # 검색 정보
        search_info = results.get('search_info', {})
        print(f"\n검색 정보:")
        print(f"  총 후보: {search_info.get('total_candidates', 0)}개")
        print(f"  의미 모델: {search_info.get('semantic_model', '')}")
        
        if search_info.get('llm_analysis') and search_info['llm_analysis'].get('recommendation'):
            print(f"\n전체 AI 추천 의견:")
            print(f"  {search_info['llm_analysis']['recommendation']}")
    
    def get_statistics(self) -> Dict:
        """시스템 통계 반환"""
        stats = {
            'system_initialized': self.is_initialized,
            'openai_available': self.openai_client is not None,
            'semantic_model': self.semantic_model_name,
            'cache_dir': self.cache_dir
        }
        
        if self.integrated_df is not None:
            stats.update({
                'total_items': len(self.integrated_df),
                'chapters': len(self.integrated_df['chapter'].unique()) if 'chapter' in self.integrated_df.columns else 0,
                'data_sources': self.integrated_df['data_source'].value_counts().to_dict() if 'data_source' in self.integrated_df.columns else {}
            })
            
            # 표준품명 커버리지
            if 'data_source' in self.integrated_df.columns:
                with_std = self.integrated_df['data_source'].str.contains('std', na=False).sum()
                coverage = (with_std / len(self.integrated_df)) * 100
                stats['standard_coverage'] = coverage
        
        # 캐시 정보
        cache_info = self.cache_manager.get_cache_info(self.semantic_model_name)
        stats['cache_info'] = cache_info
        
        return stats
    
    def get_cache_info(self) -> Dict:
        """캐시 정보 반환"""
        return self.cache_manager.get_cache_info(self.semantic_model_name)
    
    def clear_cache(self) -> int:
        """캐시 삭제"""
        return self.cache_manager.clear_cache()
    
    def copy_cache_from_colab(self, colab_cache_dir: str) -> bool:
        """코랩에서 캐시 복사"""
        return self.cache_manager.copy_from_colab(colab_cache_dir)
    
 
    
    def _parse_llm_candidates(self, llm_response: str) -> List[Dict]:
        """LLM 응답에서 HS 코드 후보 파싱"""
        try:
            import json
            # JSON 부분만 추출
            start = llm_response.find('{')
            end = llm_response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = llm_response[start:end]
                data = json.loads(json_str)
                return data.get('candidates', [])
        except:
            # JSON 파싱 실패시 텍스트에서 추출 시도
            candidates = []
            lines = llm_response.split('\n')
            for line in lines:
                if any(char.isdigit() for char in line) and len([c for c in line if c.isdigit()]) >= 10:
                    # 10자리 숫자가 포함된 라인에서 HS 코드 추출 시도
                    import re
                    hs_match = re.search(r'\b(\d{10})\b', line)
                    if hs_match:
                        candidates.append({
                            'hs_code': hs_match.group(1),
                            'confidence': 7,  # 기본값
                            'reasoning': line.strip(),
                            'chapter': hs_match.group(1)[:2],
                            'category': 'LLM 제안'
                        })
            return candidates[:5]  # 최대 5개
        
        return []
    

    def recommend_ultimate(self, query: str, material: str = "", usage: str = "", 
                          final_count: int = 5) -> Dict:
        """LLM 통합 추천 시스템"""
        if not self.is_initialized:
            raise ValueError("시스템이 초기화되지 않았습니다. load_data()를 먼저 실행하세요.")
        
        if not self.openai_client:
            print("⚠️ OpenAI가 활성화되지 않았습니다. 기본 추천을 사용합니다.")
            return self.recommend(query, material, usage, use_llm=False, final_count=final_count)
        
        print(f"\n{'='*60}")
        print(f"🧠 LLM 통합 추천 시스템")
        print(f"{'='*60}")
        print(f"쿼리: '{query}'")
        if material:
            print(f"재질: '{material}'")
        if usage:
            print(f"용도: '{usage}'")
        
        try:
            # 1. LLM 직접 후보 생성
            print(f"\n1. LLM 직접 후보 생성...")
            llm_candidates = self._get_llm_candidates(query, material, usage)
            print(f"  LLM 후보 통합: {len(llm_candidates)}개")
            
            # 2. 검색엔진 후보 생성
            print(f"\n2. 검색엔진 후보 생성...")
            search_results = self.search_engine.search(query, material, usage)
            print(f"  검색 후보: {len(search_results)}개")
            
            # 3. LLM 후보와 검색 결과 통합
            print(f"\n3. LLM 후보와 검색 결과 통합...")
            integrated_results = self._integrate_llm_and_search(llm_candidates, search_results)
            print(f"  통합 후보: {len(integrated_results)}개")
            
            # 4. LLM 재순위 분석
            print(f"\n4. LLM 재순위 분석...")
            reranked_results = self._llm_rerank(query, material, usage, integrated_results.head(20))
            print(f"  LLM 재순위 분석: {len(reranked_results)}개 후보")
            
            # 5. 최종 추천 결과 생성
            print(f"\n5. 최종 추천 결과 생성...")
            recommendations = self._format_ultimate_recommendations(reranked_results, final_count)
            
            return {
                'query': query,
                'material': material,
                'usage': usage,
                'recommendations': recommendations,
                'search_info': {
                    'method': 'ultimate_llm_hybrid',
                    'llm_candidates': len(llm_candidates),
                    'search_candidates': len(search_results),
                    'total_candidates': len(integrated_results),
                    'semantic_model': self.semantic_model_name,
                    'llm_model': 'gpt-4.1-mini',
                }
            }
            
        except Exception as e:
            print(f"LLM 통합 추천 중 오류 발생: {e}")
            print("기본 추천 시스템으로 대체합니다...")
            return self.recommend(query, material, usage, use_llm=True, final_count=final_count)
    
    def _get_llm_candidates(self, query: str, material: str, usage: str) -> List[Dict]:
        """LLM이 직접 HS 코드 후보를 제안"""
        try:
            # LLM 프롬프트 구성
            prompt = f"""다음 상품에 대한 HS 코드를 분석하여 가장 적합한 후보 3개를 제안해주세요:

상품 정보:
- 상품명: {query}
- 재질: {material if material else '명시되지 않음'}
- 용도: {usage if usage else '명시되지 않음'}

요구사항:
1. 한국 관세법상 HS 코드 10자리를 정확히 제안하세요
2. 각 후보에 대해 1-10점 확신도를 부여하세요
3. 제안 이유를 간단히 설명하세요

응답 형식 (JSON):
{{
  "candidates": [
    {{
      "hs_code": "1234567890",
      "confidence": 9,
      "reason": "제안 이유"
    }}
  ]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "당신은 한국 관세법 및 HS 코드 분류 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            try:
                import json
                result = json.loads(response.choices[0].message.content)
                candidates = result.get('candidates', [])
                
                # 후보들을 점수순으로 정렬
                candidates.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                
                # 검색엔진에서 해당 HS 코드들의 상세 정보 조회
                enriched_candidates = []
                for candidate in candidates[:5]:
                    hs_code = candidate.get('hs_code', '')
                    if len(hs_code) == 10:
                        # 데이터에서 해당 HS 코드 찾기
                        matching_rows = self.integrated_df[
                            (self.integrated_df['HS_KEY'] == hs_code) |
                            (self.integrated_df.get('HS부호', '') == hs_code)
                        ]
                        
                        if not matching_rows.empty:
                            row = matching_rows.iloc[0]
                            enriched_candidates.append({
                                'hs_code': hs_code,
                                'confidence': candidate.get('confidence', 0),
                                'reason': candidate.get('reason', ''),
                                'row_data': row,
                                'source': 'llm_direct'
                            })
                        else:
                            # 데이터에 없는 경우도 후보로 포함 (LLM 전용)
                            enriched_candidates.append({
                                'hs_code': hs_code,
                                'confidence': candidate.get('confidence', 0),
                                'reason': candidate.get('reason', ''),
                                'row_data': None,
                                'source': 'llm_only'
                            })
                
                print(f"    ✅ LLM 직접 제안: {len(enriched_candidates)}개")
                for i, cand in enumerate(enriched_candidates, 1):
                    match_status = "✅ 데이터 매칭" if cand['row_data'] is not None else "🆕 LLM 전용"
                    print(f"    {i}. {cand['hs_code']} (확신도: {cand['confidence']}) - {match_status}")
                
                return enriched_candidates
                
            except json.JSONDecodeError:
                print("    ❌ LLM 응답 파싱 실패")
                return []
                
        except Exception as e:
            print(f"    ❌ LLM 후보 생성 실패: {e}")
            return []
    
    def _integrate_llm_and_search(self, llm_candidates: List[Dict], search_results: pd.DataFrame) -> pd.DataFrame:
        """LLM 후보와 검색 결과를 통합"""
        integrated_rows = []
        used_hs_codes = set()
        
        # 1. LLM 후보들을 우선 처리
        for llm_candidate in llm_candidates:
            hs_code = llm_candidate['hs_code']
            
            if llm_candidate['row_data'] is not None:
                # 데이터에 있는 LLM 후보
                row = llm_candidate['row_data'].copy()
                
                # 검색 결과와 매칭되는지 확인
                search_match = search_results[
                    (search_results['HS_KEY'] == hs_code) |
                    (search_results.get('HS부호', '') == hs_code)
                ]
                
                if not search_match.empty:
                    # LLM + 검색 매칭: 높은 가중치
                    search_row = search_match.iloc[0]
                    hybrid_score = search_row.get('hybrid_score', 0)
                    confidence_score = llm_candidate['confidence'] / 10.0
                    ultimate_score = (hybrid_score * 0.6) + (confidence_score * 0.4)
                    
                    row['ultimate_score'] = ultimate_score
                    row['llm_confidence'] = llm_candidate['confidence']
                    row['llm_reason'] = llm_candidate['reason']
                    row['match_type'] = 'llm_search_match'
                    row['hybrid_score'] = hybrid_score
                    
                    print(f"    ✅ LLM+검색 매칭: {hs_code} (점수: {ultimate_score:.3f})")
                else:
                    # LLM 전용 후보: 중간 가중치
                    confidence_score = llm_candidate['confidence'] / 10.0
                    ultimate_score = confidence_score * 0.7
                    
                    row['ultimate_score'] = ultimate_score
                    row['llm_confidence'] = llm_candidate['confidence']
                    row['llm_reason'] = llm_candidate['reason']
                    row['match_type'] = 'llm_only_with_data'
                    row['hybrid_score'] = 0.0
                    
                    print(f"    🔍 LLM 데이터 후보: {hs_code} (점수: {ultimate_score:.3f})")
                
                integrated_rows.append(row)
                used_hs_codes.add(hs_code)
            else:
                # 데이터에 없는 LLM 전용 후보
                confidence_score = llm_candidate['confidence'] / 10.0
                ultimate_score = confidence_score * 0.5
                
                # 가상의 행 생성
                fake_row = pd.Series({
                    'HS_KEY': hs_code,
                    'HS부호': hs_code,
                    '한글품목명': f"LLM 제안: {hs_code}",
                    '영문품목명': f"LLM Suggested: {hs_code}",
                    'ultimate_score': ultimate_score,
                    'llm_confidence': llm_candidate['confidence'],
                    'llm_reason': llm_candidate['reason'],
                    'match_type': 'llm_only_no_data',
                    'hybrid_score': 0.0,
                    'chapter': hs_code[:2] if len(hs_code) >= 2 else '',
                    'heading': hs_code[:4] if len(hs_code) >= 4 else '',
                    'data_source': 'llm_generated',
                    'final_combined_text': f"LLM이 제안한 HS 코드: {hs_code}. 이유: {llm_candidate['reason']}"
                })
                
                integrated_rows.append(fake_row)
                used_hs_codes.add(hs_code)
                print(f"    🆕 LLM 전용 후보: {hs_code} (확신도: {llm_candidate['confidence']})")
        
        # 2. 검색 결과에서 LLM에 없는 것들 추가
        for _, search_row in search_results.iterrows():
            hs_key = search_row.get('HS_KEY', '')
            hs_code = search_row.get('HS부호', hs_key)
            
            if hs_code not in used_hs_codes:
                # 검색 전용 후보: 낮은 가중치
                hybrid_score = search_row.get('hybrid_score', 0)
                ultimate_score = hybrid_score * 0.8
                
                row = search_row.copy()
                row['ultimate_score'] = ultimate_score
                row['llm_confidence'] = 0
                row['llm_reason'] = ''
                row['match_type'] = 'search_only'
                
                integrated_rows.append(row)
                used_hs_codes.add(hs_code)
        
        # DataFrame으로 변환하고 정렬
        if integrated_rows:
            integrated_df = pd.DataFrame(integrated_rows)
            integrated_df = integrated_df.sort_values('ultimate_score', ascending=False).reset_index(drop=True)
            return integrated_df
        else:
            return pd.DataFrame()
    
    def _llm_rerank(self, query: str, material: str, usage: str, candidates: pd.DataFrame) -> pd.DataFrame:
        """LLM을 활용한 후보 재순위 결정"""
        if len(candidates) == 0:
            return candidates
        
        try:
            # 상위 후보들 정보 준비
            candidate_info = []
            for idx, row in candidates.head(10).iterrows():
                hs_code = row.get('HS_KEY') or row.get('HS부호', '')
                name_kr = row.get('한글품목명', '')
                description = row.get('final_combined_text', '')[:150]
                current_score = row.get('ultimate_score', 0)
                match_type = row.get('match_type', '')
                
                candidate_info.append({
                    'hs_code': hs_code,
                    'name_kr': name_kr,
                    'description': description,
                    'current_score': current_score,
                    'match_type': match_type
                })
            
            # LLM 재순위 프롬프트
            prompt = f"""다음 상품에 대한 HS 코드 후보들을 재순위하여 평가해주세요:

상품 정보:
- 상품명: {query}
- 재질: {material if material else '명시되지 않음'}
- 용도: {usage if usage else '명시되지 않음'}

후보 목록:
"""
            
            for i, cand in enumerate(candidate_info, 1):
                prompt += f"""
{i}. HS코드: {cand['hs_code']}
   한글명: {cand['name_kr']}
   설명: {cand['description']}
   현재점수: {cand['current_score']:.3f}
   매칭유형: {cand['match_type']}
"""
            
            prompt += """
각 후보를 다음 기준으로 1-10점 평가하고 재순위를 매겨주세요:
1. 재질 정확성
2. 용도 적합성  
3. HS 체계상 정확성
4. 실무 사용 빈도

응답 형식 (JSON):
{
  "rankings": [
    {
      "hs_code": "코드",
      "rank": 1,
      "rerank_score": 9.5,
      "reason": "재순위 근거"
    }
  ]
}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "당신은 HS 코드 분류 및 무역 실무 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            try:
                import json
                result = json.loads(response.choices[0].message.content)
                rankings = result.get('rankings', [])
                
                # 재순위 정보를 딕셔너리로 변환
                rerank_info = {}
                for rank_item in rankings:
                    hs_code = rank_item.get('hs_code', '')
                    rerank_info[hs_code] = {
                        'llm_rank': rank_item.get('rank', 999),
                        'llm_rerank_score': rank_item.get('rerank_score', 0),
                        'llm_rerank_reason': rank_item.get('reason', '')
                    }
                
                # 원본 데이터에 재순위 정보 추가
                reranked_candidates = candidates.copy()
                
                for idx, row in reranked_candidates.iterrows():
                    hs_code = row.get('HS_KEY') or row.get('HS부호', '')
                    
                    if hs_code in rerank_info:
                        rerank_data = rerank_info[hs_code]
                        
                        # 최종 점수 계산 (기존 점수 + LLM 재순위 점수)
                        current_score = row.get('ultimate_score', 0)
                        llm_rerank_score = rerank_data['llm_rerank_score'] / 10.0
                        final_score = (current_score * 0.6) + (llm_rerank_score * 0.4)
                        
                        reranked_candidates.at[idx, 'ultimate_score'] = final_score
                        reranked_candidates.at[idx, 'llm_rank'] = rerank_data['llm_rank']
                        reranked_candidates.at[idx, 'llm_rerank_score'] = rerank_data['llm_rerank_score']
                        reranked_candidates.at[idx, 'llm_rerank_reason'] = rerank_data['llm_rerank_reason']
                
                # 최종 점수로 재정렬
                reranked_candidates = reranked_candidates.sort_values('ultimate_score', ascending=False).reset_index(drop=True)
                
                print(f"    ✅ LLM 재순위 완료")
                return reranked_candidates
                
            except json.JSONDecodeError:
                print(f"    ⚠️ LLM 재순위 파싱 실패, 원본 순서 유지")
                return candidates
                
        except Exception as e:
            print(f"    ⚠️ LLM 재순위 실패: {e}, 원본 순서 유지")
            return candidates
    
    def _format_ultimate_recommendations(self, results: pd.DataFrame, final_count: int) -> List[Dict]:
        """ 추천 결과 포맷팅 (nan 문제 해결)"""
        recommendations = []
        
        for idx, row in results.head(final_count * 2).iterrows():
            # 🔧 nan 문제 해결: 안전한 HS 코드 추출
            hs_key = row.get('HS_KEY', '')
            hs_code = row.get('HS부호', '')
            
            # nan 값 처리
            if pd.isna(hs_key) or hs_key == '' or str(hs_key) == 'nan':
                hs_key = hs_code
            
            if pd.isna(hs_code) or hs_code == '' or str(hs_code) == 'nan':
                hs_code = hs_key
                
            # 둘 다 비어있으면 LLM 정보에서 가져오기
            if not hs_code or str(hs_code) == 'nan':
                # LLM 후보에서 원래 코드 찾기
                if hasattr(row, 'name') and 'llm_confidence' in row:
                    # 이건 LLM 생성 데이터일 가능성
                    for col in row.index:
                        if 'hs' in col.lower() and pd.notna(row[col]) and str(row[col]) != 'nan':
                            hs_code = str(row[col])
                            hs_key = hs_code
                            break
            
            # 최종 안전장치
            if not hs_code or str(hs_code) == 'nan':
                hs_code = f"알 수 없음_{idx}"
                hs_key = hs_code
            
            # 이름 정보
            name_kr = self._extract_best_name(row, ['한글품목명', '세번10단위품명', '표준품명'])
            name_en = self._extract_best_name(row, ['영문품목명', '표준품명영문'])
            
            # 설명 정보
            description = ''
            if 'final_combined_text' in row and pd.notna(row['final_combined_text']):
                description = str(row['final_combined_text'])
            
            # 점수 정보 (nan 처리)
            ultimate_score = row.get('ultimate_score', 0)
            hybrid_score = row.get('hybrid_score', 0)
            
            # nan 값들을 0으로 대체
            if pd.isna(ultimate_score):
                ultimate_score = 0
            if pd.isna(hybrid_score):
                hybrid_score = 0
                
            confidence = min(max(ultimate_score, 0), 1.0)  # 0-1 범위로 제한
            
            # 장/호 정보 (nan 처리)
            chapter = str(row.get('chapter', ''))
            if chapter == 'nan' or pd.isna(row.get('chapter')):
                chapter = hs_key[:2] if len(str(hs_key)) >= 2 else ''
                
            heading = str(row.get('heading', ''))
            if heading == 'nan' or pd.isna(row.get('heading')):
                heading = hs_key[:4] if len(str(hs_key)) >= 4 else ''
            
            recommendation = {
                'hs_code': str(hs_code),
                'hs_key': str(hs_key),
                'name_kr': name_kr,
                'name_en': name_en,
                'description': description[:500] if description else '',
                'chapter': chapter,
                'heading': heading,
                'confidence': round(confidence, 4),
                'scores': {
                    'ultimate': round(ultimate_score, 4),
                    'hybrid': round(hybrid_score, 4),
                    'keyword': round(row.get('keyword_score', 0) if pd.notna(row.get('keyword_score', 0)) else 0, 4),
                    'semantic': round(row.get('semantic_score', 0) if pd.notna(row.get('semantic_score', 0)) else 0, 4)
                },
                'data_source': str(row.get('data_source', '')),
                'match_type': str(row.get('match_type', '')),
                'is_standard_match': bool(row.get('is_standard_match', False))
            }
            
            # LLM 정보 추가 (nan 처리)
            llm_info = {}
            llm_confidence = row.get('llm_confidence', 0)
            if pd.notna(llm_confidence) and llm_confidence > 0:
                llm_info['llm_direct'] = {
                    'confidence': int(llm_confidence),
                    'reason': str(row.get('llm_reason', ''))
                }
            
            llm_rerank_score = row.get('llm_rerank_score', 0)
            if pd.notna(llm_rerank_score) and llm_rerank_score > 0:
                llm_info['llm_rerank'] = {
                    'score': float(llm_rerank_score),
                    'rank': int(row.get('llm_rank', 999)) if pd.notna(row.get('llm_rank')) else 999,
                    'reason': str(row.get('llm_rerank_reason', ''))
                }
            
            if llm_info:
                recommendation['llm_analysis'] = llm_info
            
            recommendations.append(recommendation)
            
            if len(recommendations) >= final_count:
                break
        
        return recommendations
    
    def print_results(self, results: Dict, query: str):
            """추천 결과 출력 (LLM 통합 정보 포함)"""
            print(f"\n{'='*80}")
            print(f"'{query}' 검색 결과")
            print(f"{'='*80}")
            
            recommendations = results.get('recommendations', [])
            
            if not recommendations:
                print("추천 결과가 없습니다.")
                return
            
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. HS 코드: {rec['hs_code']}")
                print(f"   한글명: {rec['name_kr']}")
                if rec['name_en']:
                    print(f"   영문명: {rec['name_en']}")
                print(f"   신뢰도: {rec['confidence']:.3f}")
                print(f"   장: {rec['chapter']}, 호: {rec['heading']}")
                
                if rec.get('description'):
                    desc = rec['description']
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    print(f"   설명: {desc}")
                
                # LLM 분석 결과 
                if rec.get('llm_analysis'):
                    llm = rec['llm_analysis']
                    
                    # LLM 직접 제안 정보
                    if 'llm_direct' in llm:
                        direct = llm['llm_direct']
                        print(f"   🧠 LLM 분석:")
                        print(f"     ✨ LLM 직접 제안 (확신도: {direct['confidence']}/10)")
                        print(f"     📝 제안 이유: {direct['reason']}")
                    
                    # LLM 재순위 정보
                    if 'llm_rerank' in llm:
                        rerank = llm['llm_rerank']
                        print(f"     🔄 재순위 점수: {rerank['score']}/10")
                        print(f"     📊 재순위 근거: {rerank['reason']}")
                        print(f"     📍 LLM 순위: {rerank['rank']}위")
                
                # 기존 LLM 분석 (호환성)
                elif rec.get('llm_analysis'):
                    llm = rec['llm_analysis']
                    if llm.get('reason'):
                        print(f"   AI 분석: {llm['reason']}")
                    if llm.get('caution'):
                        print(f"   주의사항: {llm['caution']}")
                
                # 매칭 타입 표시
                match_type = rec.get('match_type', '')
                if match_type == 'llm_search_match':
                    print(f"   🎯 매칭: LLM + 검색엔진 일치")
                elif match_type == 'llm_only_with_data':
                    print(f"   🔍 매칭: LLM 전용 (데이터 있음)")
                elif match_type == 'llm_only_no_data':
                    print(f"   🆕 매칭: LLM 전용 (신규 제안)")
                elif match_type == 'search_only':
                    print(f"   🔎 매칭: 검색엔진 전용")
                
                # 점수 정보 (ultimate 점수 포함)
                scores = rec['scores']
                if 'ultimate' in scores:
                    print(f"   점수: U={scores['ultimate']:.3f}, H={scores['hybrid']:.3f}, "
                        f"K={scores['keyword']:.3f}, S={scores['semantic']:.3f}")
                else:
                    print(f"   점수: H={scores['hybrid']:.3f}, K={scores['keyword']:.3f}, S={scores['semantic']:.3f}")
                
                print(f"   데이터 소스: {rec.get('data_source', '')}")
            
            # 검색 정보
            search_info = results.get('search_info', {})
            print(f"\n검색 정보:")
            print(f"  총 후보: {search_info.get('total_candidates', 0)}개")
            
            method = search_info.get('method', '')
            if method == 'ultimate_llm_hybrid':
                print(f"  🧠 방법: LLM 통합 추천")
                print(f"  LLM 모델: {search_info.get('llm_model', '')}")
            else:
                print(f"  의미 모델: {search_info.get('semantic_model', '')}")
            
            if search_info.get('llm_analysis') and search_info['llm_analysis'].get('recommendation'):
                print(f"\n전체 AI 추천 의견:")
                print(f"  {search_info['llm_analysis']['recommendation']}")

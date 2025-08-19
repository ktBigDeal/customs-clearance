
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import os

import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# 프로젝트 루트를 sys.path에 추가 (model-hscode 폴더)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

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
            api_key = None
            
            # 1. 환경변수에서 API 키 확인 (우선순위)
            env_api_key = os.getenv('OPENAI_API_KEY')
            if env_api_key:
                api_key = env_api_key.strip()
                print("환경변수에서 OpenAI API 키 로드")
            else:
                # 2. 파일에서 API 키 확인 (대체)
                api_file = SYSTEM_CONFIG.get('openai_api_file', 'openai_api.txt')
                if os.path.exists(api_file):
                    with open(api_file, 'r', encoding='utf-8') as f:
                        api_key = f.read().strip()
                    print(f"파일에서 OpenAI API 키 로드: {api_file}")
                else:
                    print(f"환경변수 OPENAI_API_KEY와 API 키 파일 {api_file} 모두 없습니다")
                    return False
            
            if not api_key:
                print("유효한 OpenAI API 키를 찾을 수 없습니다")
                return False
                
            self.openai_client = openai.OpenAI(api_key=api_key)
            
            # 간단한 테스트 호출
            test_response = self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": "안녕하세요"}],
                max_tokens=10
            )
            
            print("OpenAI API 초기화 성공")
            return True
                
        except Exception as e:
            print(f"OpenAI API 초기화 실패: {e}")
            self.openai_client = None
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
            
            # 4.5. LLM 고득점 후보 우선 반영 (NEW!)
            print(f"\n4.5. LLM 고득점 후보 우선 반영...")
            final_results = self._boost_high_scoring_llm_candidates(llm_candidates, reranked_results, query, material, usage)
            print(f"  고득점 후보 반영 완료: {len(final_results)}개 후보")
            
            # 5. 최종 추천 결과 생성
            print(f"\n5. 최종 추천 결과 생성...")
            
            # 최종 정렬 상태 확인
            print(f"    🏆 최종 후보 상위 10개:")
            for i, (idx, row) in enumerate(final_results.head(10).iterrows()):
                hs_code = row.get('HS_KEY') or row.get('HS부호', '')
                ultimate_score = row.get('ultimate_score', 0)
                llm_rerank_score = row.get('llm_rerank_score', 0)
                match_type = row.get('match_type', '')
                print(f"    {i+1:2d}. {hs_code}: {ultimate_score:.4f} (LLM재순위: {llm_rerank_score}, 유형: {match_type})")
            
            recommendations = self._format_ultimate_recommendations(final_results, final_count)
            
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
                    # LLM + 검색 매칭: 개선된 균형 가중치
                    search_row = search_match.iloc[0]
                    hybrid_score = search_row.get('hybrid_score', 0)
                    confidence_score = llm_candidate['confidence'] / 10.0
                    
                    # 개선된 가중치 로직: LLM 확신도에 따라 동적 조정
                    if llm_candidate['confidence'] >= 8:
                        # 고확신 LLM: LLM 점수 더 높은 비중
                        llm_weight = 0.7
                        search_weight = 0.3
                    elif llm_candidate['confidence'] >= 6:
                        # 중확신 LLM: 균형 잡힌 비중
                        llm_weight = 0.5
                        search_weight = 0.5
                    else:
                        # 저확신 LLM: 검색 점수 더 높은 비중
                        llm_weight = 0.3
                        search_weight = 0.7
                    
                    ultimate_score = (hybrid_score * search_weight) + (confidence_score * llm_weight)
                    
                    row['ultimate_score'] = ultimate_score
                    row['llm_confidence'] = llm_candidate['confidence']
                    row['llm_reason'] = llm_candidate['reason']
                    row['match_type'] = 'llm_search_match'
                    row['hybrid_score'] = hybrid_score
                    
                    print(f"    ✅ LLM+검색 매칭: {hs_code} (점수: {ultimate_score:.3f}, LLM가중치: {llm_weight})")
                else:
                    # LLM 전용 후보: 확신도에 따른 동적 가중치
                    confidence_score = llm_candidate['confidence'] / 10.0
                    
                    if llm_candidate['confidence'] >= 8:
                        # 고확신: 높은 점수 부여
                        ultimate_score = confidence_score * 0.9
                    elif llm_candidate['confidence'] >= 6:
                        # 중확신: 중간 점수
                        ultimate_score = confidence_score * 0.75
                    else:
                        # 저확신: 낮은 점수
                        ultimate_score = confidence_score * 0.6
                    
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
                llm_response_content = response.choices[0].message.content
                print(f"    🤖 LLM 응답 원본: {llm_response_content[:200]}...")
                
                result = json.loads(llm_response_content)
                rankings = result.get('rankings', [])
                print(f"    📝 파싱된 rankings 수: {len(rankings)}")
                
                # 재순위 정보를 딕셔너리로 변환
                rerank_info = {}
                for rank_item in rankings:
                    hs_code = rank_item.get('hs_code', '')
                    rerank_info[hs_code] = {
                        'llm_rank': rank_item.get('rank', 999),
                        'llm_rerank_score': rank_item.get('rerank_score', 0),
                        'llm_rerank_reason': rank_item.get('reason', '')
                    }
                
                print(f"    🔍 LLM이 평가한 HS코드들: {list(rerank_info.keys())}")
                
                # 원본 데이터에 재순위 정보 추가
                reranked_candidates = candidates.copy()
                matched_count = 0
                unmatched_count = 0
                
                for idx, row in reranked_candidates.iterrows():
                    hs_code = row.get('HS_KEY') or row.get('HS부호', '')
                    
                    # 1차 정확 매칭
                    if hs_code in rerank_info:
                        rerank_data = rerank_info[hs_code]
                        
                        # 최종 점수 계산 (LLM 재순위를 더 높은 비중으로)
                        current_score = row.get('ultimate_score', 0)
                        llm_rerank_score = rerank_data['llm_rerank_score'] / 10.0
                        
                        # LLM 재순위 점수가 높을 때 더 큰 영향력 부여
                        if rerank_data['llm_rerank_score'] >= 8.0:
                            # 고득점: LLM 80% + 기존 20%
                            final_score = (current_score * 0.2) + (llm_rerank_score * 0.8)
                        elif rerank_data['llm_rerank_score'] >= 6.0:
                            # 중간점수: LLM 60% + 기존 40%
                            final_score = (current_score * 0.4) + (llm_rerank_score * 0.6)
                        else:
                            # 낮은점수: LLM 40% + 기존 60%
                            final_score = (current_score * 0.6) + (llm_rerank_score * 0.4)
                        
                        reranked_candidates.at[idx, 'ultimate_score'] = final_score
                        reranked_candidates.at[idx, 'llm_rank'] = rerank_data['llm_rank']
                        reranked_candidates.at[idx, 'llm_rerank_score'] = rerank_data['llm_rerank_score']
                        reranked_candidates.at[idx, 'llm_rerank_reason'] = rerank_data['llm_rerank_reason']
                        matched_count += 1
                        print(f"    ✅ 정확 매칭: {hs_code} (점수: {rerank_data['llm_rerank_score']})")
                    else:
                        # 2차 유사 매칭 시도 (앞 8자리, 6자리 매칭)
                        matched_similar = False
                        
                        for llm_hs_code, llm_data in rerank_info.items():
                            # 8자리 매칭 (세번까지 동일)
                            if len(hs_code) >= 8 and len(llm_hs_code) >= 8:
                                if hs_code[:8] == llm_hs_code[:8]:
                                    # 유사 매칭으로 낮은 가중치 적용
                                    current_score = row.get('ultimate_score', 0)
                                    llm_rerank_score = llm_data['llm_rerank_score'] / 10.0
                                    final_score = (current_score * 0.8) + (llm_rerank_score * 0.2)  # 낮은 가중치
                                    
                                    reranked_candidates.at[idx, 'ultimate_score'] = final_score
                                    reranked_candidates.at[idx, 'llm_rank'] = llm_data['llm_rank'] + 100  # 순위 페널티
                                    reranked_candidates.at[idx, 'llm_rerank_score'] = llm_data['llm_rerank_score'] * 0.7  # 점수 할인
                                    reranked_candidates.at[idx, 'llm_rerank_reason'] = f"유사매칭(8자리): {llm_data['llm_rerank_reason']}"
                                    matched_count += 1
                                    matched_similar = True
                                    print(f"    🔄 유사 매칭(8자리): {hs_code} ↔ {llm_hs_code} (점수: {llm_data['llm_rerank_score']*0.7})")
                                    break
                        
                        # 3차 더 넓은 유사 매칭 (6자리)
                        if not matched_similar:
                            for llm_hs_code, llm_data in rerank_info.items():
                                # 6자리 매칭 (호까지 동일)
                                if len(hs_code) >= 6 and len(llm_hs_code) >= 6:
                                    if hs_code[:6] == llm_hs_code[:6]:
                                        # 더 낮은 가중치 적용
                                        current_score = row.get('ultimate_score', 0)
                                        llm_rerank_score = llm_data['llm_rerank_score'] / 10.0
                                        final_score = (current_score * 0.9) + (llm_rerank_score * 0.1)  # 더 낮은 가중치
                                        
                                        reranked_candidates.at[idx, 'ultimate_score'] = final_score
                                        reranked_candidates.at[idx, 'llm_rank'] = llm_data['llm_rank'] + 200  # 더 큰 순위 페널티
                                        reranked_candidates.at[idx, 'llm_rerank_score'] = llm_data['llm_rerank_score'] * 0.5  # 더 큰 점수 할인
                                        reranked_candidates.at[idx, 'llm_rerank_reason'] = f"광범위매칭(6자리): {llm_data['llm_rerank_reason']}"
                                        matched_count += 1
                                        matched_similar = True
                                        print(f"    🌐 광범위 매칭(6자리): {hs_code} ↔ {llm_hs_code} (점수: {llm_data['llm_rerank_score']*0.5})")
                                        break
                        
                        if not matched_similar:
                            unmatched_count += 1
                            print(f"    ❌ 매칭 실패: {hs_code} (LLM 응답에 없음)")
                
                print(f"    📊 매칭 결과: 성공 {matched_count}개, 실패 {unmatched_count}개")
                
                # 최종 점수로 재정렬
                reranked_candidates = reranked_candidates.sort_values('ultimate_score', ascending=False).reset_index(drop=True)
                
                print(f"    ✅ LLM 재순위 완료")
                return reranked_candidates
                
            except json.JSONDecodeError as e:
                print(f"    ⚠️ LLM 재순위 파싱 실패: {e}")
                print(f"    📄 응답 내용: {response.choices[0].message.content}")
                print(f"    🔄 원본 순서 유지")
                return candidates
                
        except Exception as e:
            print(f"    ⚠️ LLM 재순위 실패: {e}, 원본 순서 유지")
            return candidates
    
    def _search_hs_code_in_data(self, hs_code: str) -> pd.Series:
        """HS 코드를 데이터에서 검색하여 해당 행 데이터를 반환"""
        try:
            print(f"    🔍 HS코드 검색 시도: {hs_code}")
            
            if not hasattr(self, 'df') or self.df is None:
                print(f"    ❌ 데이터프레임 없음")
                return None
            
            print(f"    📊 전체 데이터 행수: {len(self.df)}")
            print(f"    📋 컬럼 목록: {list(self.df.columns)}")
                
            # 정확 매칭 시도
            exact_match = self.df[self.df['HS부호'] == hs_code]
            print(f"    🎯 정확 매칭 (HS부호 == {hs_code}): {len(exact_match)}개")
            if not exact_match.empty:
                print(f"    ✅ 정확 매칭 성공!")
                return exact_match.iloc[0]
            
            # HS_KEY로 매칭 시도
            if 'HS_KEY' in self.df.columns:
                key_match = self.df[self.df['HS_KEY'] == hs_code]
                print(f"    🔑 HS_KEY 매칭 (HS_KEY == {hs_code}): {len(key_match)}개")
                if not key_match.empty:
                    print(f"    ✅ HS_KEY 매칭 성공!")
                    return key_match.iloc[0]
            
            # 8자리 매칭 시도
            if len(hs_code) >= 8:
                partial_match = self.df[self.df['HS부호'].str.startswith(hs_code[:8])]
                print(f"    🔢 8자리 매칭 ({hs_code[:8]}로 시작): {len(partial_match)}개")
                if not partial_match.empty:
                    print(f"    ✅ 8자리 매칭 성공!")
                    return partial_match.iloc[0]
            
            # 6자리 매칭 시도
            if len(hs_code) >= 6:
                broad_match = self.df[self.df['HS부호'].str.startswith(hs_code[:6])]
                print(f"    🌐 6자리 매칭 ({hs_code[:6]}로 시작): {len(broad_match)}개")
                if not broad_match.empty:
                    print(f"    ✅ 6자리 매칭 성공!")
                    return broad_match.iloc[0]
            
            # 더 광범위한 검색 (392로 시작)
            if hs_code.startswith('392'):
                prefix_match = self.df[self.df['HS부호'].str.startswith('392')]
                print(f"    🔍 392 접두어 매칭: {len(prefix_match)}개")
                if not prefix_match.empty:
                    # 가장 유사한 것 선택 (3924류 우선)
                    similar_3924 = prefix_match[prefix_match['HS부호'].str.startswith('3924')]
                    if not similar_3924.empty:
                        print(f"    ✅ 3924류 유사 매칭 성공!")
                        return similar_3924.iloc[0]
                    else:
                        print(f"    ⚠️ 392류 첫번째 매칭 사용")
                        return prefix_match.iloc[0]
                    
            print(f"    ❌ 모든 매칭 시도 실패")
            return None
            
        except Exception as e:
            print(f"    ❌ HS코드 검색 실패: {e}")
            return None
        
    def _get_top_rerank_candidates(self, reranked_results: pd.DataFrame, top_n: int = 2) -> Dict[str, Dict]:
        """LLM 재순위 상위권 후보 추출"""
        top_candidates = {}
        
        for idx, row in reranked_results.iterrows():
            hs_code = row.get('HS_KEY') or row.get('HS부호', '')
            llm_rank = row.get('llm_rank', 999)
            llm_rerank_score = row.get('llm_rerank_score', 0)
            
            # 재순위 1-3위이면서 8점 이상인 후보
            if (pd.notna(llm_rank) and llm_rank <= top_n and 
                pd.notna(llm_rerank_score) and llm_rerank_score >= 8.0):
                top_candidates[hs_code] = {
                    'rank': llm_rank,
                    'score': llm_rerank_score,
                    'reason': row.get('llm_rerank_reason', '')
                }
                print(f"    🏆 재순위 상위권: {hs_code} (순위: {llm_rank}, 점수: {llm_rerank_score})")
        
        return top_candidates
    
    def _boost_high_scoring_llm_candidates(self, llm_candidates: List[Dict], reranked_results: pd.DataFrame, query: str = "", material: str = "", usage: str = "") -> pd.DataFrame:
        """🚀 단순화된 점수 기반 부스팅: LLM 고득점 후보들의 점수를 배수로 증폭"""
        try:
            print(f"    🔧 점수 기반 부스팅 시작...")
            
            # 1. 모든 후보를 하나의 리스트로 통합
            all_candidates = reranked_results.copy()
            
            # 2. LLM 직접 제안 고득점 후보 추가 (기존에 없는 경우)
            high_score_threshold = 8.0
            new_candidates = []
            
            # 2-1. LLM 직접 제안 후보들 처리
            for llm_candidate in llm_candidates:
                confidence = llm_candidate.get('confidence', 0)
                hs_code = llm_candidate.get('hs_code', '')
                
                # 높은 확신도 후보이면서 기존 결과에 없는 경우
                if confidence >= high_score_threshold:
                    existing = all_candidates[
                        (all_candidates['HS_KEY'] == hs_code) |
                        (all_candidates.get('HS부호', '') == hs_code)
                    ]
                    
                    if existing.empty and llm_candidate.get('row_data') is not None:
                        # 새로운 LLM 고확신 후보 추가 (적절한 초기 점수로 설정)
                        new_row = llm_candidate['row_data'].copy()
                        new_row['ultimate_score'] = min(0.85, confidence / 10.0)  # 최대 0.85로 제한 완화
                        new_row['llm_confidence'] = confidence
                        new_row['llm_reason'] = llm_candidate.get('reason', '')
                        new_row['match_type'] = 'llm_high_score_new'
                        new_row['llm_rerank_score'] = confidence
                        new_row['llm_rank'] = 1
                        new_row['llm_rerank_reason'] = f"LLM 고확신 직접 제안 (확신도: {confidence}/10)"
                        new_candidates.append(new_row)
                        print(f"    ➕ 신규 고확신 후보 추가: {hs_code} (확신도: {confidence}, 점수: {min(0.85, confidence / 10.0):.3f})")
            
            # 2-2. LLM 재순위에서 누락된 고득점 코드 직접 추가 ⭐ 핵심 해결!
            if query and self.openai_client:
                try:
                    print(f"    🔍 LLM 재순위 누락 고득점 코드 탐색...")
                    
                    # LLM에게 직접 최고 추천 코드를 요청
                    prompt = f"""다음 상품에 대한 가장 적합한 HS 코드 3개를 추천해주세요:

상품 정보:
- 상품명: {query}
- 재질: {material if material else '명시되지 않음'}
- 용도: {usage if usage else '명시되지 않음'}

각 코드에 대해 1-10점으로 확신도를 매겨주세요.

응답 형식 (JSON):
{{
  "recommendations": [
    {{
      "hs_code": "3924100000",
      "confidence": 9.5,
      "reason": "추천 근거"
    }}
  ]
}}"""
                    
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "system", "content": "당신은 HS 코드 분류 전문가입니다."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=800,
                        temperature=0.2
                    )
                    
                    import json
                    direct_response = json.loads(response.choices[0].message.content)
                    recommendations = direct_response.get('recommendations', [])
                    
                    for rec in recommendations:
                        hs_code = rec.get('hs_code', '')
                        confidence = rec.get('confidence', 0)
                        reason = rec.get('reason', '')
                        
                        if confidence >= 9.0:  # 9점 이상 고확신도만
                            # 기존 후보에 없는지 확인
                            existing = all_candidates[
                                (all_candidates['HS_KEY'] == hs_code) |
                                (all_candidates.get('HS부호', '') == hs_code)
                            ]
                            
                            if existing.empty:
                                # HS 코드를 실제 데이터에서 검색하여 row_data 생성
                                hs_data = self._search_hs_code_in_data(hs_code)
                                if hs_data is not None:
                                    new_row = hs_data.copy()
                                    new_row['ultimate_score'] = min(0.9, confidence / 10.0)
                                    new_row['llm_confidence'] = confidence
                                    new_row['llm_reason'] = reason
                                    new_row['match_type'] = 'llm_rerank_missing'
                                    new_row['llm_rerank_score'] = confidence
                                    new_row['llm_rank'] = 1
                                    new_row['llm_rerank_reason'] = f"LLM 재순위 누락 고득점 (확신도: {confidence}/10)"
                                    new_candidates.append(new_row)
                                    print(f"    🎯 재순위 누락 고득점 추가: {hs_code} (확신도: {confidence}, 점수: {min(0.9, confidence / 10.0):.3f})")
                                else:
                                    print(f"    ❌ HS코드 데이터 없음: {hs_code}")
                    
                except Exception as e:
                    print(f"    ⚠️ 재순위 누락 처리 실패: {e}")
            
            # 새로운 후보들 통합
            if new_candidates:
                new_df = pd.DataFrame(new_candidates)
                all_candidates = pd.concat([all_candidates, new_df], ignore_index=True)
            
            # 3. 균형 잡힌 점수 기반 부스팅 적용
            boosted_count = 0
            search_max_score = all_candidates[all_candidates.get('match_type', '') != 'llm_high_score_new']['ultimate_score'].max() if not all_candidates.empty else 0.8
            print(f"    📊 검색 결과 최고 점수: {search_max_score:.3f}")
            
            for idx, row in all_candidates.iterrows():
                hs_code = row.get('HS_KEY') or row.get('HS부호', '')
                current_score = row.get('ultimate_score', 0)
                llm_rerank_score = row.get('llm_rerank_score', 0)
                llm_confidence = row.get('llm_confidence', 0)
                match_type = row.get('match_type', '')
                
                boost_multiplier = 1.0  # 기본 배수
                boost_reason = ""
                
                # 🎯 LLM 신규 고확신 후보: 확신도에 따른 적극적 부스팅
                if match_type in ['llm_high_score_new', 'llm_rerank_missing']:
                    confidence = row.get('llm_confidence', 0)
                    if confidence >= 9.5:
                        # 9.5점 이상 최고 확신도: 검색 최고점의 140%로 설정 (확실한 1위)
                        adjusted_score = search_max_score * 1.4
                        boost_reason = f"최고확신도 신규후보 ({current_score:.3f} → {adjusted_score:.3f})"
                    elif confidence >= 9.0:
                        # 9점 이상 최고 확신도: 검색 최고점의 125%로 설정
                        adjusted_score = search_max_score * 1.2
                        boost_reason = f"최고확신도 신규후보 ({current_score:.3f} → {adjusted_score:.3f})"
                    elif confidence >= 8.5:
                        # 8.5점 이상 고확신도: 검색 최고점의 110%로 설정
                        adjusted_score = search_max_score * 1.1
                        boost_reason = f"고확신도 신규후보 ({current_score:.3f} → {adjusted_score:.3f})"
                    else:
                        # 8.0점 이상: 검색 최고점 수준으로 설정
                        adjusted_score = search_max_score
                        boost_reason = f"신규 LLM 후보 균형 조정 ({current_score:.3f} → {adjusted_score:.3f})"
                    
                    all_candidates.at[idx, 'ultimate_score'] = adjusted_score
                    boosted_count += 1
                    print(f"    ⚖️  적극 부스팅: {hs_code} {boost_reason}")
                
                # 🚀 기존 후보 부스팅 (적당한 강도)
                elif pd.notna(llm_rerank_score) and llm_rerank_score >= 9.0:
                    # LLM 재순위 최고점 (8.5점 이상)
                    boost_multiplier = 1.3  # 20% 증폭으로 강화
                    boost_reason = f"재순위 최고점({llm_rerank_score})"
               
                elif pd.notna(llm_rerank_score) and llm_rerank_score >= 8.0:
                    # LLM 재순위 고점 (8.0점 이상)
                    boost_multiplier = 1.15  # 15% 증폭
                    boost_reason = f"재순위 고점({llm_rerank_score})"
                    
                elif pd.notna(llm_confidence) and llm_confidence >= 8.5:
                    # LLM 직접 제안 최고 확신도
                    boost_multiplier = 1.18  # 18% 증폭으로 강화
                    boost_reason = f"직접 제안 최고확신도({llm_confidence})"
                elif pd.notna(llm_confidence) and llm_confidence >= 8.0:
                    # LLM 직접 제안 고확신도
                    boost_multiplier = 1.12  # 12% 증폭
                    boost_reason = f"직접 제안 고확신도({llm_confidence})"
                
                # 부스팅 적용
                if boost_multiplier > 1.0:
                    boosted_score = current_score * boost_multiplier
                    all_candidates.at[idx, 'ultimate_score'] = boosted_score
                    boosted_count += 1
                    print(f"    🚀 점수 부스팅: {hs_code} ({current_score:.3f} → {boosted_score:.3f}) [{boost_reason}]")
            
            # 4. 최종 점수로 정렬
            final_results = all_candidates.sort_values('ultimate_score', ascending=False).reset_index(drop=True)
            
            print(f"    ✅ 점수 부스팅 완료: {boosted_count}개 후보 부스팅됨")
            
            return final_results
                
        except Exception as e:
            print(f"    ❌ 점수 부스팅 실패: {e}")
            return reranked_results

    
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
            
            # 1. LLM 직접 제안 정보 (항상 포함 가능)
            llm_confidence = row.get('llm_confidence', 0)
            if pd.notna(llm_confidence) and llm_confidence > 0:
                llm_info['llm_direct'] = {
                    'confidence': int(llm_confidence),
                    'reason': str(row.get('llm_reason', ''))
                }
                print(f"    📍 {hs_code} LLM 직접 제안 정보 추가 (확신도: {llm_confidence})")
            
            # 2. LLM 재순위 정보 (매칭 성공시만)
            llm_rerank_score = row.get('llm_rerank_score', 0)
            print(f"    🔍 {hs_code} llm_rerank_score: {llm_rerank_score} (type: {type(llm_rerank_score)})")
            
            if pd.notna(llm_rerank_score) and llm_rerank_score > 0:
                llm_info['llm_rerank'] = {
                    'score': float(llm_rerank_score),
                    'rank': int(row.get('llm_rank', 999)) if pd.notna(row.get('llm_rank')) else 999,
                    'reason': str(row.get('llm_rerank_reason', ''))
                }
                print(f"    ✅ {hs_code} LLM 재순위 정보 추가됨!")
            else:
                print(f"    ⚠️ {hs_code} LLM 재순위 정보 없음 (score={llm_rerank_score})")
            
            # 3. 매칭 실패한 경우를 위한 개선된 폴백 처리
            if not llm_info:
                # LLM 정보가 전혀 없는 경우, 구체적인 분석 정보 제공
                match_type = row.get('match_type', '')
                data_source = row.get('data_source', '')
                
                # 매칭 유형별 구체적인 설명 생성
                analysis_reason = self._generate_detailed_analysis_reason(
                    hs_code, match_type, data_source, confidence, row
                )
                
                llm_info['enhanced_search'] = {
                    'confidence': min(max(confidence * 10, 1), 10),  # 0-1 -> 1-10 변환
                    'reason': analysis_reason,
                    'analysis_type': self._get_analysis_type_label(match_type),
                    'data_quality': self._assess_data_quality(row)
                }
                print(f"    🔄 {hs_code} 개선된 폴백 정보 추가 ({self._get_analysis_type_label(match_type)})")
            
            if llm_info:
                recommendation['llm_analysis'] = llm_info
                print(f"    ✅ {hs_code} llm_analysis 최종 포함!")
            else:
                print(f"    ❌ {hs_code} llm_analysis 최종 제외")
            
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
                        print(f"     🔄재순위 점수: {rerank['score']}/10")
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
    
    def _generate_detailed_analysis_reason(self, hs_code: str, match_type: str, data_source: str, 
                                         confidence: float, row: pd.Series) -> str:
        """매칭 유형별 구체적인 분석 설명 생성"""
        try:
            # 기본 정보 추출
            name_kr = self._extract_best_name(row, ['한글품목명', '세번10단위품명', '표준품명'])
            chapter = hs_code[:2] if len(hs_code) >= 2 else ''
            heading = hs_code[:4] if len(hs_code) >= 4 else ''
            
            # 매칭 유형별 구체적인 설명
            if 'hybrid' in match_type:
                return f"키워드 매칭과 의미 분석을 결합하여 찾은 결과입니다. " \
                       f"'{name_kr}' (제{chapter}류, 호 {heading})는 검색어와 높은 관련성을 보입니다. " \
                       f"신뢰도: {confidence:.1%}"
            
            elif 'semantic' in match_type:
                return f"의미 분석(AI 임베딩)을 통해 찾은 유사 항목입니다. " \
                       f"검색어와 의미적으로 연관된 '{name_kr}' 항목으로, " \
                       f"제{chapter}류에 분류됩니다. 의미 유사도: {confidence:.1%}"
            
            elif 'keyword' in match_type:
                return f"키워드 매칭을 통해 찾은 직접 연관 항목입니다. " \
                       f"'{name_kr}'는 검색어와 직접적인 키워드 일치를 보이며, " \
                       f"HS코드 체계상 제{chapter}류에 해당합니다. 키워드 점수: {confidence:.1%}"
            
            elif 'standard' in match_type:
                return f"표준 품명 데이터베이스에서 찾은 공식 분류입니다. " \
                       f"'{name_kr}'는 관세청 표준 품명으로 등록된 항목이며, " \
                       f"HS코드 {hs_code} (제{chapter}류)로 정확히 분류됩니다."
            
            else:
                # 기본 설명
                keyword_score = row.get('keyword_score', 0)
                semantic_score = row.get('semantic_score', 0)
                
                analysis_parts = []
                if keyword_score and pd.notna(keyword_score) and keyword_score > 0:
                    analysis_parts.append(f"키워드 유사도 {keyword_score:.1%}")
                if semantic_score and pd.notna(semantic_score) and semantic_score > 0:
                    analysis_parts.append(f"의미 유사도 {semantic_score:.1%}")
                
                score_info = ", ".join(analysis_parts) if analysis_parts else f"전체 신뢰도 {confidence:.1%}"
                
                return f"검색엔진 분석 결과 '{name_kr}' 항목을 추천합니다. " \
                       f"HS코드 {hs_code} (제{chapter}류, 호 {heading})로 분류되며, " \
                       f"{score_info}로 검색어와 관련성이 있습니다."
                       
        except Exception as e:
            return f"검색엔진 분석을 통해 추천된 항목입니다 (HS코드: {hs_code})"
    
    def _get_analysis_type_label(self, match_type: str) -> str:
        """매칭 유형별 라벨 반환"""
        type_labels = {
            'llm_search_match': 'AI+검색 통합',
            'llm_only_with_data': 'AI 직접 제안',
            'llm_only': 'AI 전용',
            'llm_high_score_boost': 'AI 고확신',
            'llm_high_score_only': 'AI 고확신 전용',
            'llm_high_score_existing': 'AI 고확신 기존',
            'search_only': '검색엔진 기반',
            'hybrid_search': '하이브리드 검색',
            'semantic_search': '의미 분석',
            'keyword_search': '키워드 매칭',
            'standard_match': '표준 품명'
        }
        return type_labels.get(match_type, '통합 분석')
    
    def _assess_data_quality(self, row: pd.Series) -> str:
        """데이터 품질 평가"""
        try:
            # 데이터 완성도 확인
            name_kr = row.get('한글품목명', '')
            name_en = row.get('영문품목명', '')
            description = row.get('final_combined_text', '')
            data_source = row.get('data_source', '')
            
            quality_score = 0
            if name_kr and pd.notna(name_kr) and len(str(name_kr)) > 1:
                quality_score += 25
            if name_en and pd.notna(name_en) and len(str(name_en)) > 1:
                quality_score += 25  
            if description and pd.notna(description) and len(str(description)) > 10:
                quality_score += 25
            if data_source and 'standard' in data_source:
                quality_score += 25
            
            if quality_score >= 75:
                return '높음'
            elif quality_score >= 50:
                return '보통'
            else:
                return '기본'
                
        except Exception:
            return '기본'

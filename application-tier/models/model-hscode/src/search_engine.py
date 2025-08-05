# search_engine.py - 검색 엔진 담당 (final_combined_text 대응)

import pandas as pd
import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (model-hscode 폴더)
sys.path.append(str(Path(__file__).parent.parent))
from config import SYSTEM_CONFIG

class SearchEngine:
    """하이브리드 검색 엔진 클래스 (final_combined_text 지원)"""
    
    def __init__(self, semantic_model_name: str = None):
        self.semantic_model_name = semantic_model_name or SYSTEM_CONFIG['semantic_model']
        self.top_k = SYSTEM_CONFIG['top_k']
        
        # 모델 초기화
        self.tfidf_vectorizer = TfidfVectorizer(**SYSTEM_CONFIG['tfidf_config'])
        
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.semantic_model = SentenceTransformer(self.semantic_model_name, device=device)
        
        # 데이터 및 인덱스
        self.integrated_df = None
        self.tfidf_matrix = None
        self.semantic_embeddings = None
        
        # 매핑 데이터
        self.standard_mapping = {}
        self.reverse_mapping = {}
        self.chapter_descriptions = {}
        self.hs_hierarchy = None
        
        # 동의어 사전
        self.synonym_dict = self._build_synonym_dictionary()
        
        print(f"검색 엔진 초기화: {self.semantic_model_name}")
        print(f"동의어 사전: {len(self.synonym_dict)}개 카테고리")
    
    def _build_synonym_dictionary(self) -> Dict:
        """동의어/유사어 사전 구축"""
        return {
            # 나사/볼트류
            'fasteners': {
                'keywords': ['나사', '볼트', '스크류', '너트', '와셔', 'screw', 'bolt', 'nut', 'washer', 
                           '체결구', '조임쇠', '고정구', 'fastener', 'fixing', '볼트너트', '육각볼트',
                           '십자나사', '일자나사', '목나사', '철나사', '기계나사', '태핑나사', 'tapping'],
                'boost_chapters': ['73'],
                'boost_headings': ['7318'],
                'negative_keywords': ['파이프', '관', '드릴', 'pipe', 'tube', 'drill']
            },
            
            # 전자/전기제품
            'electronics': {
                'keywords': ['전자', '전기', '디지털', 'electronic', 'electric', 'digital',
                           '반도체', 'semiconductor', 'IC', '칩', 'chip', '회로', 'circuit',
                           '트랜지스터', 'transistor', '다이오드', 'diode', '저항', 'resistor',
                           '콘덴서', 'capacitor', '센서', 'sensor'],
                'boost_chapters': ['84', '85'],
                'boost_headings': ['8471', '8473', '8517', '8518', '8541', '8542']
            },
            
            # 컴퓨터/IT
            'computer': {
                'keywords': ['컴퓨터', '노트북', '모니터', '키보드', '마우스', 'computer', 'laptop', 
                           'monitor', 'keyboard', 'mouse', 'PC', '프린터', 'printer', '스캐너', 'scanner',
                           '서버', 'server', '하드디스크', 'HDD', 'SSD', 'USB', '메모리', 'memory',
                           '그래픽카드', 'GPU', 'CPU', '마더보드', 'motherboard'],
                'boost_chapters': ['84', '85'],
                'boost_headings': ['8471', '8443', '8517', '8523']
            },
            
            # 인쇄/토너
            'printing': {
                'keywords': ['토너', '카트리지', '잉크', 'toner', 'cartridge', 'ink', '인쇄', 'print',
                           '프린터', 'printer', '복사기', 'copier', '팩스', 'fax', '스캐너', 'scanner',
                           '잉크젯', 'inkjet', '레이저', 'laser', '드럼', 'drum', '정착기', 'fuser'],
                'boost_chapters': ['84'],
                'boost_headings': ['8443', '8471']
            },
            
       
            
            # 화학제품
            'chemical': {
                'keywords': ['화학', '화합물', '용액', '용매', 'chemical', 'compound', 'solution', 'solvent',
                           '산', 'acid', '염기', 'base', '촉매', 'catalyst', '시약', 'reagent',
                           '접착제', 'adhesive', '도료', 'paint', '잉크', 'ink', '세제', 'detergent'],
                'boost_chapters': ['28', '29', '32', '34', '38'],
                'boost_headings': []
            },
            
            # 플라스틱
            'plastic': {
                'keywords': ['플라스틱', '수지', '폴리머', 'plastic', 'resin', 'polymer', 'PE', 'PP', 'PVC',
                           '합성수지', 'synthetic', 'ABS', 'PC', '폴리카보네이트', 'polycarbonate',
                           '아크릴', 'acrylic', 'PET', '폴리에틸렌', 'polyethylene'],
                'boost_chapters': ['39'],
                'boost_headings': []
            },
            
            # 금속
            'metal': {
                'keywords': ['금속', '철', '강', '알루미늄', '구리', 'metal', 'iron', 'steel', 'aluminum', 'copper',
                           '스테인레스', 'stainless', '합금', 'alloy', '황동', 'brass', '청동', 'bronze',
                           '아연', 'zinc', '니켈', 'nickel', '티타늄', 'titanium', '마그네슘', 'magnesium'],
                'boost_chapters': ['72', '73', '74', '75', '76', '78', '79', '81'],
                'boost_headings': []
            },
            
            # 보석/귀금속
            'jewelry': {
                'keywords': ['금', '은', '백금', '귀금속', '보석', '다이아몬드', '반지', '목걸이', '귀걸이', 
                           'gold', 'silver', 'platinum', 'jewelry', 'diamond', 'ring', 'necklace', 'earring',
                           '장신구', '팔찌', 'bracelet', '브로치', 'brooch', '시계', 'watch',
                           '진주', 'pearl', '루비', 'ruby', '사파이어', 'sapphire', '에메랄드', 'emerald'],
                'boost_chapters': ['71'],
                'boost_headings': ['7113', '7114', '7115', '7116', '7117']
            },
            
            # 출판물/도서
            'books': {
                'keywords': ['책', '도서', '서적', '만화', '소설', '교과서', '참고서', 'book', 'novel', 'textbook',
                           '만화책', '웹툰', '라이트노벨', '코믹', 'comic', 'manga', 'webtoon',
                           '출판물', '인쇄물', '잡지', 'magazine', '신문', 'newspaper', '카탈로그', 'catalog',
                           '포스터', 'poster', '전단지', 'leaflet', '브로셔', 'brochure', '팜플렛', 'pamphlet',
                           '지도', 'map', '도면', 'drawing', '악보', 'music sheet'],
                'boost_chapters': ['49'],
                'boost_headings': ['4901', '4902', '4903', '4904', '4905', '4906', '4909', '4911']
            },
            
            # 자동차 부품
            'automotive': {
                'keywords': ['자동차', '차량', '엔진', '타이어', 'automotive', 'vehicle', 'engine', 'tire',
                           '브레이크', 'brake', '배터리', 'battery', '부품', 'parts', '필터', 'filter',
                           '점화플러그', 'spark plug', '오일', 'oil', '쿨런트', 'coolant', '벨트', 'belt',
                           '호스', 'hose', '범퍼', 'bumper', '헤드라이트', 'headlight'],
                'boost_chapters': ['84', '87'],
                'boost_headings': ['8407', '8408', '8483', '8507', '8708']
            },
            
            # 의료기기
            'medical': {
                'keywords': ['의료', '의료기기', '병원', '치료', 'medical', 'hospital', 'treatment',
                           '수술', 'surgery', '진단', 'diagnosis', '혈압계', '체온계', '청진기',
                           '주사기', 'syringe', '붕대', 'bandage', '마스크', 'mask'],
                'boost_chapters': ['90'],
                'boost_headings': ['9018', '9019', '9020', '9021', '9022']
            },
            
            # 스포츠/레저
            'sports': {
                'keywords': ['스포츠', '운동', '헬스', '피트니스', 'sports', 'fitness', 'exercise',
                           '골프', 'golf', '테니스', 'tennis', '축구', 'soccer', '농구', 'basketball',
                           '수영', 'swimming', '자전거', 'bicycle', '등산', 'climbing'],
                'boost_chapters': ['95'],
                'boost_headings': ['9506', '9507']
            }
        }
    
    def load_data(self, integrated_df: pd.DataFrame, 
                  standard_mapping: Dict = None,
                  reverse_mapping: Dict = None,
                  chapter_descriptions: Dict = None):
        """검색에 필요한 데이터 로드 (final_combined_text 지원)"""
        print("검색 엔진에 데이터 로드 중...")
        
        self.integrated_df = integrated_df.copy()
        self.standard_mapping = standard_mapping or {}
        self.reverse_mapping = reverse_mapping or {}
        self.chapter_descriptions = chapter_descriptions or {}
        
        # 🔍 데이터 구조 확인
        print(f"  로드된 데이터: {len(self.integrated_df)}개 항목")
        print(f"  사용 가능한 컬럼: {list(self.integrated_df.columns)}")
        
        # final_combined_text 컬럼 확인
        if 'final_combined_text' not in self.integrated_df.columns:
            print("  ❌ final_combined_text 컬럼이 없습니다!")
            # 대체 텍스트 컬럼 찾기
            text_candidates = ['combined_text', '한글품목명', '표준품명']
            for candidate in text_candidates:
                if candidate in self.integrated_df.columns:
                    print(f"  ➡️ 대체 텍스트 컬럼 사용: {candidate}")
                    self.integrated_df['final_combined_text'] = self.integrated_df[candidate].fillna('')
                    break
            else:
                print("  ❌ 사용 가능한 텍스트 컬럼이 없습니다!")
                return False
        
        # 계층 구조 구축
        self._build_hierarchy()
        
        print(f"  데이터 로드 완료: {len(self.integrated_df)}개 항목")
        print(f"  표준품명 매핑: {len(self.standard_mapping)}개")
        return True
    
    def _build_hierarchy(self):
        """HS 계층 구조 구축"""
        self.hs_hierarchy = {
            'chapters': defaultdict(list),
            'headings': defaultdict(list),
            'subheadings': defaultdict(list)
        }
        
        # chapter, heading, subheading 컬럼이 없으면 HS_KEY에서 추출
        if 'chapter' not in self.integrated_df.columns:
            self.integrated_df['chapter'] = self.integrated_df['HS_KEY'].str[:2]
        if 'heading' not in self.integrated_df.columns:
            self.integrated_df['heading'] = self.integrated_df['HS_KEY'].str[:4]
        if 'subheading' not in self.integrated_df.columns:
            self.integrated_df['subheading'] = self.integrated_df['HS_KEY'].str[:6]
        
        for chapter, group in self.integrated_df.groupby('chapter'):
            self.hs_hierarchy['chapters'][chapter] = group.index.tolist()
            
        for heading, group in self.integrated_df.groupby('heading'):
            self.hs_hierarchy['headings'][heading] = group.index.tolist()
            
        for subheading, group in self.integrated_df.groupby('subheading'):
            self.hs_hierarchy['subheadings'][subheading] = group.index.tolist()
    
    def build_index(self):
        """검색 인덱스 구축 (final_combined_text 기반)"""
        if self.integrated_df is None:
            raise ValueError("데이터가 로드되지 않았습니다")
        
        print("검색 인덱스 구축 중...")
        
        # final_combined_text 사용
        if 'final_combined_text' not in self.integrated_df.columns:
            raise ValueError("final_combined_text 컬럼이 없습니다")
        
        # 텍스트 준비
        texts = self.integrated_df['final_combined_text'].fillna('').astype(str).tolist()
        texts = [text if text.strip() else 'empty_text' for text in texts]
        
        print(f"  총 {len(texts)}개 텍스트 처리")
        print(f"  평균 텍스트 길이: {np.mean([len(text) for text in texts]):.1f}자")
        
        # TF-IDF 인덱스 구축
        print("  TF-IDF 매트릭스 생성...")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        
        # 의미 임베딩 구축
        print("  의미 임베딩 생성...")
        self.semantic_embeddings = self.semantic_model.encode(
            texts, 
            convert_to_tensor=True,
            show_progress_bar=True,
            batch_size=32
        )
        
        print("검색 인덱스 구축 완료!")
        print(f"  TF-IDF 매트릭스: {self.tfidf_matrix.shape}")
        print(f"  의미 임베딩: {self.semantic_embeddings.shape}")
    
    def expand_query(self, query: str) -> str:
        """쿼리 확장 - 동의어/유사어 추가"""
        expanded_terms = [query]
        query_lower = query.lower()
        
        for category, data in self.synonym_dict.items():
            keywords = data['keywords']
            
            # 쿼리에 포함된 키워드 찾기
            matched_keywords = []
            for keyword in keywords:
                if keyword.lower() in query_lower or query_lower in keyword.lower():
                    matched_keywords.append(keyword)
            
            # 매칭된 키워드가 있으면 관련 용어들 추가
            if matched_keywords:
                for keyword in keywords:
                    if keyword.lower() not in query_lower:
                        expanded_terms.append(keyword)
                
                print(f"  '{category}' 카테고리 확장: {len(keywords)}개 용어 추가")
                break
        
        unique_terms = list(dict.fromkeys(expanded_terms))
        expanded_query = ' '.join(unique_terms)
        
        if len(unique_terms) > 1:
            print(f"  쿼리 확장: '{query}' -> {len(unique_terms)}개 용어")
        
        return expanded_query
    
    def get_category_boost_info(self, query: str) -> Dict:
        """카테고리별 부스트 정보 반환"""
        query_lower = query.lower()
        boost_info = {'chapters': [], 'headings': []}
        
        for category, data in self.synonym_dict.items():
            keywords = data['keywords']
            
            if any(keyword.lower() in query_lower or query_lower in keyword.lower() 
                   for keyword in keywords):
                boost_info['chapters'].extend(data.get('boost_chapters', []))
                boost_info['headings'].extend(data.get('boost_headings', []))
                print(f"  '{category}' 카테고리 부스트 적용")
                break
        
        return boost_info
    
    def search_with_standard_names(self, query: str) -> List[str]:
        """표준품명 매핑을 활용한 직접 검색"""
        queries_to_search = [query.lower().strip()]
        
        # 쿼리 확장
        expanded_query = self.expand_query(query)
        if expanded_query != query:
            expanded_terms = expanded_query.split()
            queries_to_search.extend([term.lower().strip() for term in expanded_terms])
        
        direct_matches = []
        
        for search_query in queries_to_search:
            # 정확한 매칭
            if search_query in self.standard_mapping:
                direct_matches.extend(self.standard_mapping[search_query])
                
            # 부분 매칭
            for std_name, hs_codes in self.standard_mapping.items():
                if search_query in std_name or std_name in search_query:
                    direct_matches.extend(hs_codes)
                    
        return list(set(direct_matches))
    
    def calculate_dynamic_weights(self, query: str) -> Tuple[float, float]:
        """동적 가중치 계산"""
        words = query.split()
        query_length = len(words)
        
        if query_length <= 2:
            return 0.7, 0.3  # 짧은 쿼리 - 키워드 중심
        elif query_length >= 8:
            return 0.6, 0.4  # 키워드 비중 유지
        elif query_length >= 5:
            return 0.4, 0.6  # 긴 쿼리 - 의미 중심
        else:
            return 0.5, 0.5  # 중간 - 균형
    
    def search(self, query: str, material: str = "", usage: str = "") -> pd.DataFrame:
        """하이브리드 검색 실행 (final_combined_text 기반)"""
        if self.integrated_df is None or self.tfidf_matrix is None:
            raise ValueError("검색 인덱스가 구축되지 않았습니다")
        
        print(f"하이브리드 검색 실행: '{query}'")
        
        try:
            # 1. 쿼리 확장
            expanded_query = self.expand_query(query)
            
            # 2. 카테고리별 부스트 정보
            boost_info = self.get_category_boost_info(query)
            
            # 3. 표준품명 직접 매칭
            direct_hs_codes = self.search_with_standard_names(query)
            if direct_hs_codes:
                print(f"  표준품명 매칭: {len(direct_hs_codes)}개 HS 코드")
            
            # 4. 동적 가중치 계산
            keyword_weight, semantic_weight = self.calculate_dynamic_weights(expanded_query)
            print(f"  동적 가중치: 키워드={keyword_weight:.2f}, 의미={semantic_weight:.2f}")
            
            # 5. 전체 검색 쿼리 구성
            full_query = f"{expanded_query} {material} {usage}".strip()
            
            # 6. TF-IDF 검색
            query_tfidf = self.tfidf_vectorizer.transform([full_query])
            keyword_scores = cosine_similarity(query_tfidf, self.tfidf_matrix).flatten()
            
            # 7. 의미 검색
            semantic_queries = [query, expanded_query] if expanded_query != query else [query]
            semantic_scores_list = []
            
            for sq in semantic_queries:
                sq_full = f"{sq} {material} {usage}".strip()
                query_embedding = self.semantic_model.encode([sq_full], convert_to_tensor=True)
                scores = cosine_similarity(
                    query_embedding.cpu().numpy(),
                    self.semantic_embeddings.cpu().numpy()
                ).flatten()
                semantic_scores_list.append(scores)
            
            semantic_scores = np.mean(semantic_scores_list, axis=0)
            
            # 8. 하이브리드 스코어 계산
            hybrid_scores = (keyword_weight * keyword_scores + 
                            semantic_weight * semantic_scores)
            
            # 9. 표준품명 기반 보너스
            if direct_hs_codes:
                # HS부호 컬럼 찾기
                hs_code_col = None
                for col in ['HS부호', 'HS_KEY']:
                    if col in self.integrated_df.columns:
                        hs_code_col = col
                        break
                
                if hs_code_col:
                    for hs_code in direct_hs_codes:
                        mask = self.integrated_df[hs_code_col] == hs_code
                        indices = self.integrated_df[mask].index
                        for idx in indices:
                            if idx < len(hybrid_scores):
                                hybrid_scores[idx] *= 2.0  # 100% 보너스
            
            # 10. 표준품명 전용 항목 보너스
            if 'data_source' in self.integrated_df.columns:
                standard_only_mask = self.integrated_df['data_source'].str.contains('std', na=False)
                if standard_only_mask.any():
                    hybrid_scores[standard_only_mask] *= 1.3  # 30% 보너스
            
            # 11. 카테고리별 부스트 적용
            if boost_info['chapters']:
                for chapter in boost_info['chapters']:
                    mask = self.integrated_df['chapter'] == chapter
                    hybrid_scores[mask] *= 1.5  # 50% 부스트
            
            if boost_info['headings']:
                for heading in boost_info['headings']:
                    mask = self.integrated_df['heading'] == heading
                    hybrid_scores[mask] *= 2.0  # 100% 부스트
            
            # 12. 결과 생성
            results = self.integrated_df.copy()
            results['keyword_score'] = keyword_scores
            results['semantic_score'] = semantic_scores
            results['hybrid_score'] = hybrid_scores
            results['is_standard_match'] = results.get('HS부호', results.get('HS_KEY', '')).isin(direct_hs_codes)
            results['expanded_query'] = expanded_query
            
            # 13. 네거티브 필터링
            for category, data in self.synonym_dict.items():
                if any(word.lower() in query.lower() for word in data['keywords']):
                    negative_keywords = data.get('negative_keywords', [])
                    for neg_keyword in negative_keywords:
                        # 한글품목명 컬럼 찾기
                        for col in ['한글품목명', 'final_combined_text']:
                            if col in results.columns:
                                mask = results[col].str.contains(neg_keyword, case=False, na=False)
                                results.loc[mask, 'hybrid_score'] *= 0.2  # 80% 감점
                                break
            
        except Exception as e:
            print(f"  검색 중 오류 발생: {e}")
            print("  기본 검색으로 폴백...")
            
            # 폴백: 기본 TF-IDF 검색만
            query_tfidf = self.tfidf_vectorizer.transform([query])
            keyword_scores = cosine_similarity(query_tfidf, self.tfidf_matrix).flatten()
            
            results = self.integrated_df.copy()
            results['hybrid_score'] = keyword_scores
            results['keyword_score'] = keyword_scores
            results['semantic_score'] = 0.0
            results['is_standard_match'] = False
        
        # 14. 정렬 및 상위 선택
        results = results.sort_values('hybrid_score', ascending=False)
        
        # 15. 이상치 필터링
        if len(results) >= 10:
            top_10_chapters = results.head(10)['chapter'].value_counts()
            dominant_chapters = top_10_chapters[top_10_chapters >= 2].index.tolist()
            
            if dominant_chapters:
                print(f"  주요 장 감지: {dominant_chapters}")
                
                main_chapter_scores = results[results['chapter'].isin(dominant_chapters)]['hybrid_score']
                other_chapter_scores = results[~results['chapter'].isin(dominant_chapters)]['hybrid_score']
                
                if len(main_chapter_scores) > 0 and len(other_chapter_scores) > 0:
                    main_avg = main_chapter_scores.mean()
                    other_avg = other_chapter_scores.mean()
                    
                    if main_avg > other_avg * 1.5:
                        results = results[results['chapter'].isin(dominant_chapters)]
                        print(f"  {len(results)}개 항목으로 필터링됨")
        
        # 16. 최종 상위 선택
        max_results = min(self.top_k, len(results))
        results = results.head(max_results)
        
        print(f"  최종 후보: {len(results)}개")
        if len(results) > 0:
            print(f"    점수 범위: {results['hybrid_score'].min():.3f} ~ {results['hybrid_score'].max():.3f}")
            chapters = results['chapter'].value_counts()
            print(f"    장 분포: {dict(chapters.head(3))}")
        
        return results
    
    def get_search_stats(self) -> Dict:
        """검색 엔진 통계 반환"""
        stats = {
            'model_name': self.semantic_model_name,
            'synonym_categories': len(self.synonym_dict),
            'standard_mappings': len(self.standard_mapping),
            'chapter_descriptions': len(self.chapter_descriptions)
        }
        
        if self.integrated_df is not None:
            stats['total_items'] = len(self.integrated_df)
            stats['chapters'] = len(self.integrated_df['chapter'].unique())
        
        if self.tfidf_matrix is not None:
            stats['tfidf_features'] = self.tfidf_matrix.shape[1]
            stats['tfidf_density'] = self.tfidf_matrix.nnz / (self.tfidf_matrix.shape[0] * self.tfidf_matrix.shape[1])
        
        if self.semantic_embeddings is not None:
            stats['embedding_dim'] = self.semantic_embeddings.shape[1]
        
        return stats
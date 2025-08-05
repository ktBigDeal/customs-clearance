# data_processor.py - 데이터 로딩 및 전처리 담당 (병합 확인 기능 추가)

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import (
    FILE_PATHS, HS_CODE_COLUMNS, STANDARD_NAME_COLUMNS, 
    HSK_CLASSIFICATION_COLUMNS
)


class DataProcessor:
    """데이터 로딩 및 전처리 담당 클래스 (HSK 중심, 23개 필드 정확 추출)"""
    
    def __init__(self, debug_mode=True):  # [DEBUG] 디버그 모드 추가
        # [TARGET] HSK 데이터를 중심으로 설정
        self.hsk_classification_data = None  # 중심 데이터
        self.hs_data = None                  # 보조 데이터
        self.standard_data = None            # 보조 데이터
        self.integrated_df = None
        self.chapter_descriptions = {}
        self.debug_mode = debug_mode  # [DEBUG] 디버그 모드 플래그
        
    def _show_merge_debug_info(self, stage, before_df, after_df, merge_key='HS_KEY'):
        """[DEBUG] 병합 디버그 정보 출력"""
        if not self.debug_mode:
            return
            
        print(f"\n[DEBUG] [{stage}] 병합 디버그 정보:")
        print("="*50)
        
        # 기본 정보
        print(f"병합 전 레코드: {len(before_df):,}개")
        print(f"병합 후 레코드: {len(after_df):,}개")
        
        # 컬럼 변화
        before_cols = set(before_df.columns)
        after_cols = set(after_df.columns)
        new_cols = after_cols - before_cols
        
        if new_cols:
            print(f"추가된 컬럼: {list(new_cols)}")
        
        # 샘플 데이터 (상위 3개)
        print(f"\n[INFO] 병합 후 샘플 데이터:")
        display_cols = [merge_key, 'final_combined_text', 'data_source']
        if 'final_combined_text' not in after_df.columns:
            display_cols = [c for c in display_cols if c in after_df.columns]
            display_cols.append('combined_text' if 'combined_text' in after_df.columns else after_df.columns[-1])
        
        sample_data = after_df[display_cols].head(3)
        for idx, row in sample_data.iterrows():
            print(f"\n[{idx}]")
            for col in display_cols:
                value = str(row[col])
                if len(value) > 100:
                    value = value[:100] + "..."
                print(f"  {col}: {value}")
        
        print("="*50)
    
    def _show_data_source_distribution(self, df):
        """[DEBUG] 데이터 소스별 분포 상세 출력"""
        if not self.debug_mode:
            return
            
        print(f"\n[INFO] 데이터 소스별 상세 분포:")
        print("-"*40)
        
        if 'data_source' in df.columns:
            source_dist = df['data_source'].value_counts()
            total = len(df)
            
            for source, count in source_dist.items():
                pct = count / total * 100
                print(f"  {source}: {count:,}개 ({pct:.1f}%)")
                
                # 각 소스별 샘플 HS_KEY 보기
                sample_keys = df[df['data_source'] == source]['HS_KEY'].head(3).tolist()
                print(f"    샘플 HS_KEY: {sample_keys}")
        
        print("-"*40)
    
    def load_hsk_classification_data(self) -> bool:
        """[TARGET] 중심 데이터: HSK 분류 데이터 로드 (15개 필드만)"""
        print("중심 데이터 로딩: HSK 분류 데이터...")
        
        try:
            if not os.path.exists(FILE_PATHS['hsk_classification']):
                print(f"HSK 분류 파일을 찾을 수 없습니다: {FILE_PATHS['hsk_classification']}")
                return False
            
            # 데이터 로드
            self.hsk_classification_data = pd.read_excel(
                FILE_PATHS['hsk_classification'], 
                sheet_name=0
            )
            print(f"  원본 데이터: {len(self.hsk_classification_data)}개 항목")
            print(f"  사용 가능한 컬럼: {list(self.hsk_classification_data.columns)[:10]}...")
            
            # 🔐 HS_KEY 매핑 키 생성 (HS10단위부호 → HS_KEY)
            hs_col = None
            hs_candidates = HSK_CLASSIFICATION_COLUMNS['hs_code_candidates']
            
            for candidate in hs_candidates:
                for col in self.hsk_classification_data.columns:
                    if candidate in col:
                        hs_col = col
                        break
                if hs_col:
                    break
            
            if not hs_col:
                print("  HS 코드 컬럼을 찾을 수 없습니다")
                return False
            
            # HS_KEY 생성 (10자리 표준화)
            self.hsk_classification_data['HS_KEY'] = (
                self.hsk_classification_data[hs_col].astype(str).str.zfill(10)
            )
            print(f"  [OK] HS_KEY 생성: {hs_col} → HS_KEY")
            
            # [DEBUG] 디버그: HS_KEY 생성 확인
            if self.debug_mode:
                print(f"\n[DEBUG] HS_KEY 생성 샘플:")
                sample_keys = self.hsk_classification_data[['HS_KEY', hs_col]].head(3)
                for idx, row in sample_keys.iterrows():
                    print(f"  {row[hs_col]} → {row['HS_KEY']}")
            
            # 📄 정의된 15개 검색 벡터 필드만 추출
            defined_fields = [
                # 세번 분류 (4개)
                '세번2단위품명', '세번4단위품명', '세번6단위품명', '세번10단위품명',
                # 신성질별 분류 (5개)
                '관세청 신성질별 분류대분류명', '관세청 신성질별 분류중분류명', 
                '관세청 신성질별 분류소분류명', '관세청 신성질별 분류세분류명', 
                '관세청 신성질별 분류세세분류명',
                # 현행 수입 성질별 분류 (4개)
                '관세청 현행 수입 성질별 분류현행수입1단위분류',
                '관세청 현행 수입 성질별 분류현행수입3단위분류',
                '관세청 현행 수입 성질별 분류현행수입소분류',
                '관세청 현행 수입 성질별 분류현행수입세분류',
                # 현행 수출 성질별 분류 (2개)
                '관세청 현행 수출 성질별 분류현행수출소분류',
                '관세청 현행 수출 성질별 분류현행수출세분류'
            ]
            
            # 실제 존재하는 필드 찾기
            extracted_fields = []
            field_mapping = {}
            
            for target_field in defined_fields:
                found_col = self._find_matching_column(target_field, self.hsk_classification_data.columns)
                
                if found_col:
                    extracted_fields.append(found_col)
                    field_mapping[target_field] = found_col
                    print(f"  [OK] {target_field}: {found_col}")
                else:
                    print(f"  [ERROR] {target_field}: 찾을 수 없음")
            
            print(f"  [INFO] 추출된 필드: {len(extracted_fields)}/15개")
            
            # [TARGET] 필요한 컬럼만 선택 (HS_KEY + 추출된 필드만)
            keep_columns = ['HS_KEY'] + extracted_fields
            before_df = self.hsk_classification_data.copy()
            self.hsk_classification_data = self.hsk_classification_data[keep_columns].copy()
            
            # [DEBUG] 디버그: 컬럼 선택 결과
            if self.debug_mode:
                print(f"\n[DEBUG] 컬럼 선택 결과:")
                print(f"  선택 전: {len(before_df.columns)}개 컬럼")
                print(f"  선택 후: {len(self.hsk_classification_data.columns)}개 컬럼")
                print(f"  최종 컬럼: {list(self.hsk_classification_data.columns)}")
            
            # 챕터 설명 추출
            self._extract_chapter_descriptions(extracted_fields, field_mapping)
            
            # combined_text 생성 (임시)
            self._create_hsk_combined_text(extracted_fields, field_mapping)
            
            print(f"  전처리 완료: {len(self.hsk_classification_data)}개 항목")
            return True
            
        except Exception as e:
            print(f"HSK 분류 데이터 로드 실패: {e}")
            return False
    
    def load_hs_code_data(self) -> bool:
        """🔗 보조 데이터: HS 코드 데이터 로드 (5개 필드만)"""
        print("\n보조 데이터 로딩: HS 코드 데이터...")
        
        try:
            if not os.path.exists(FILE_PATHS['hs_codes']):
                print(f"HS 코드 파일을 찾을 수 없습니다: {FILE_PATHS['hs_codes']}")
                return False
            
            # 데이터 로드
            self.hs_data = pd.read_csv(FILE_PATHS['hs_codes'], encoding='utf-8')
            print(f"  원본 데이터: {len(self.hs_data)}개 항목")
            
            # HS_KEY 생성 (HS부호 → HS_KEY)
            if 'HS부호' not in self.hs_data.columns:
                print("  [ERROR] HS부호 컬럼이 없습니다")
                return False
            
            self.hs_data['HS_KEY'] = self.hs_data['HS부호'].astype(str).str.zfill(10)
            
            # [DEBUG] 디버그: HS_KEY 생성 확인
            if self.debug_mode:
                print(f"\n[DEBUG] HS 데이터 HS_KEY 생성 샘플:")
                sample_keys = self.hs_data[['HS_KEY', 'HS부호']].head(3)
                for idx, row in sample_keys.iterrows():
                    print(f"  {row['HS부호']} → {row['HS_KEY']}")
            
            # 📄 정의된 5개 검색 벡터 필드만 추출
            defined_fields = [
                '한글품목명', '영문품목명', 'HS부호내용', 
                '한국표준무역분류명', '성질통합분류코드명'
            ]
            
            # 실제 존재하는 필드 확인
            extracted_fields = []
            for field in defined_fields:
                if field in self.hs_data.columns:
                    extracted_fields.append(field)
                    print(f"  [OK] {field}")
                else:
                    print(f"  [ERROR] {field}: 없음")
            
            # [TARGET] 필요한 컬럼만 선택
            keep_columns = ['HS_KEY'] + extracted_fields
            
            # 유효기간 필터링 (선택적)
            if all(col in self.hs_data.columns for col in ['적용시작일자', '적용종료일자']):
                current_date = int(datetime.now().strftime('%Y%m%d'))
                initial_count = len(self.hs_data)
                
                self.hs_data = self.hs_data[
                    (self.hs_data['적용시작일자'] <= current_date) & 
                    (self.hs_data['적용종료일자'] >= current_date)
                ]
                print(f"  유효기간 필터링: {initial_count} -> {len(self.hs_data)}개")
            
            self.hs_data = self.hs_data[keep_columns].copy()
            
            # [DEBUG] 디버그: HS 데이터 최종 상태
            if self.debug_mode:
                print(f"\n[DEBUG] HS 데이터 최종 상태:")
                print(f"  최종 레코드: {len(self.hs_data):,}개")
                print(f"  최종 컬럼: {list(self.hs_data.columns)}")
                print(f"  샘플 데이터:")
                sample = self.hs_data.head(2)
                for idx, row in sample.iterrows():
                    print(f"    HS_KEY: {row['HS_KEY']}")
                    for col in extracted_fields:
                        if col in row:
                            value = str(row[col])[:50] + "..." if len(str(row[col])) > 50 else str(row[col])
                            print(f"    {col}: {value}")
                    print()
            
            print(f"  [INFO] 추출된 필드: {len(extracted_fields)}/5개")
            print(f"  전처리 완료: {len(self.hs_data)}개 항목")
            return True
            
        except Exception as e:
            print(f"HS 코드 데이터 로드 실패: {e}")
            return False
    
    def load_standard_name_data(self) -> bool:
        """🔗 보조 데이터: 표준품명 데이터 로드 (3개 필드만)"""
        print("\n보조 데이터 로딩: 표준품명 데이터...")
        
        try:
            if not os.path.exists(FILE_PATHS['standard_names']):
                print(f"표준품명 파일을 찾을 수 없습니다: {FILE_PATHS['standard_names']}")
                return False
            
            # 데이터 로드
            self.standard_data = pd.read_excel(FILE_PATHS['standard_names'])
            print(f"  원본 데이터: {len(self.standard_data)}개 항목")
            
            # HS_KEY 생성 (HS코드 → HS_KEY)
            hs_col = None
            for col in self.standard_data.columns:
                if 'HS' in col and ('코드' in col or '부호' in col):
                    hs_col = col
                    break
            
            if not hs_col:
                print("  [ERROR] HS코드 컬럼을 찾을 수 없습니다")
                return False
            
            self.standard_data['HS_KEY'] = self.standard_data[hs_col].astype(str).str.zfill(10)
            
            # [DEBUG] 디버그: 표준품명 데이터 HS_KEY 생성 확인
            if self.debug_mode:
                print(f"\n[DEBUG] 표준품명 데이터 HS_KEY 생성 샘플:")
                sample_keys = self.standard_data[['HS_KEY', hs_col]].head(3)
                for idx, row in sample_keys.iterrows():
                    print(f"  {row[hs_col]} → {row['HS_KEY']}")
            
            # 📄 정의된 3개 검색 벡터 필드만 추출
            defined_fields = ['표준품명', '표준품명영문', '세부분류']
            
            # 유연한 컬럼 매핑
            field_mapping = {}
            extracted_fields = []
            
            for target_field in defined_fields:
                found_col = None
                for col in self.standard_data.columns:
                    if target_field in col or (target_field == '표준품명' and '품명' in col and 'HS' not in col and '영문' not in col):
                        found_col = col
                        break
                
                if found_col:
                    extracted_fields.append(found_col)
                    field_mapping[target_field] = found_col
                    print(f"  [OK] {target_field}: {found_col}")
                else:
                    print(f"  [ERROR] {target_field}: 없음")
            
            if not field_mapping.get('표준품명'):
                print("  핵심 컬럼 '표준품명'이 없어 건너뜀")
                return False
            
            # [TARGET] 필요한 컬럼만 선택
            keep_columns = ['HS_KEY'] + extracted_fields
            self.standard_data = self.standard_data[keep_columns].copy()
            
            # 빈 표준품명 제거
            std_col = field_mapping['표준품명']
            initial_count = len(self.standard_data)
            self.standard_data = self.standard_data[
                self.standard_data[std_col].notna() & 
                (self.standard_data[std_col].str.strip() != '')
            ]
            print(f"  빈 표준품명 제거: {initial_count} -> {len(self.standard_data)}개")
            
            # [DEBUG] 디버그: 표준품명 데이터 최종 상태
            if self.debug_mode:
                print(f"\n[DEBUG] 표준품명 데이터 최종 상태:")
                print(f"  최종 레코드: {len(self.standard_data):,}개")
                print(f"  최종 컬럼: {list(self.standard_data.columns)}")
                print(f"  샘플 데이터:")
                sample = self.standard_data.head(2)
                for idx, row in sample.iterrows():
                    print(f"    HS_KEY: {row['HS_KEY']}")
                    for col in extracted_fields:
                        if col in row:
                            value = str(row[col])[:50] + "..." if len(str(row[col])) > 50 else str(row[col])
                            print(f"    {col}: {value}")
                    print()
            
            print(f"  [INFO] 추출된 필드: {len(extracted_fields)}/3개")
            print(f"  전처리 완료: {len(self.standard_data)}개 항목")
            return True
            
        except Exception as e:
            print(f"표준품명 데이터 로드 실패: {e}")
            return False
    
    def integrate_data(self) -> bool:
        """[TARGET] HSK를 중심으로 모든 데이터를 통합하여 final_combined_text 생성"""
        print("\n" + "="*60)
        print("데이터 통합 프로세스 시작 (HSK 중심)")
        print("="*60)
        
        if self.hsk_classification_data is None:
            print("중심 데이터(HSK)가 없습니다")
            return False
        
        # 1단계: HSK 데이터를 기본 틀로 시작
        print("1단계: HSK 데이터를 기본 틀로 설정")
        self.integrated_df = self.hsk_classification_data.copy()
        
        # HSK의 combined_text를 final_combined_text로 시작
        self.integrated_df['final_combined_text'] = self.integrated_df['combined_text']
        self.integrated_df['data_source'] = 'hsk_main'
        print(f"  기본 데이터: {len(self.integrated_df)}개 항목")
        
        # [DEBUG] 1단계 디버그
        if self.debug_mode:
            print(f"\n[DEBUG] 1단계 후 데이터 상태:")
            print(f"  레코드 수: {len(self.integrated_df):,}개")
            print(f"  컬럼 수: {len(self.integrated_df.columns)}개")
            print(f"  HS_KEY 샘플: {self.integrated_df['HS_KEY'].head(3).tolist()}")
        
        # 2단계: HS 코드 데이터 Left Join
        if self.hs_data is not None:
            print("\n2단계: HS 코드 데이터 Left Join")
            
            # HS 데이터에서 텍스트 필드만 가져오기
            hs_text_fields = [col for col in self.hs_data.columns if col != 'HS_KEY']
            hs_to_merge = self.hs_data[['HS_KEY'] + hs_text_fields]
            
            print(f"  병합할 HS 데이터: {len(hs_to_merge)}개")
            print(f"  HS 텍스트 필드: {hs_text_fields}")
            
            # [DEBUG] 병합 전 키 매칭 확인
            if self.debug_mode:
                common_keys = set(self.integrated_df['HS_KEY']) & set(hs_to_merge['HS_KEY'])
                print(f"\n[DEBUG] HS 데이터 병합 전 키 매칭:")
                print(f"  HSK 데이터 고유 HS_KEY: {self.integrated_df['HS_KEY'].nunique():,}개")
                print(f"  HS 데이터 고유 HS_KEY: {hs_to_merge['HS_KEY'].nunique():,}개")
                print(f"  공통 HS_KEY: {len(common_keys):,}개")
                print(f"  매칭률: {len(common_keys) / len(self.integrated_df) * 100:.1f}%")
            
            # Left Join 수행
            before_merge = self.integrated_df.copy()
            self.integrated_df = pd.merge(
                self.integrated_df,
                hs_to_merge,
                on='HS_KEY',
                how='left'
            )
            
            # [DEBUG] 2단계 병합 디버그
            self._show_merge_debug_info("HS 데이터 병합", before_merge, self.integrated_df)
            
            # HS 텍스트 정보를 final_combined_text에 추가
            hs_text_addition = self._create_hs_text_for_integration(hs_text_fields)
            
            has_hs_text = hs_text_addition != ''
            if has_hs_text.any():
                self.integrated_df.loc[has_hs_text, 'final_combined_text'] = (
                    self.integrated_df.loc[has_hs_text, 'final_combined_text'] + ' ' + 
                    hs_text_addition[has_hs_text]
                ).str.strip()
                
                self.integrated_df.loc[has_hs_text, 'data_source'] = 'hsk_with_hs'
                print(f"  - {has_hs_text.sum()}개 항목에 HS 정보 추가")
            
            # [DEBUG] 2단계 후 데이터 소스 분포
            self._show_data_source_distribution(self.integrated_df)
        
        # 3단계: 표준품명 데이터 Left Join
        if self.standard_data is not None:
            print("\n3단계: 표준품명 데이터 Left Join")
            
            # 표준품명 데이터에서 텍스트 필드만 가져오기
            std_text_fields = [col for col in self.standard_data.columns if col != 'HS_KEY']
            std_to_merge = self.standard_data[['HS_KEY'] + std_text_fields]
            
            print(f"  병합할 표준품명 데이터: {len(std_to_merge)}개")
            print(f"  표준품명 텍스트 필드: {std_text_fields}")
            
            # [DEBUG] 병합 전 키 매칭 확인
            if self.debug_mode:
                common_keys = set(self.integrated_df['HS_KEY']) & set(std_to_merge['HS_KEY'])
                print(f"\n[DEBUG] 표준품명 데이터 병합 전 키 매칭:")
                print(f"  현재 통합 데이터 고유 HS_KEY: {self.integrated_df['HS_KEY'].nunique():,}개")
                print(f"  표준품명 데이터 고유 HS_KEY: {std_to_merge['HS_KEY'].nunique():,}개")
                print(f"  공통 HS_KEY: {len(common_keys):,}개")
                print(f"  매칭률: {len(common_keys) / len(self.integrated_df) * 100:.1f}%")
            
            # Left Join 수행
            before_merge = self.integrated_df.copy()
            self.integrated_df = pd.merge(
                self.integrated_df,
                std_to_merge,
                on='HS_KEY',
                how='left'
            )
            
            # [DEBUG] 3단계 병합 디버그
            self._show_merge_debug_info("표준품명 데이터 병합", before_merge, self.integrated_df)
            
            # 표준품명 텍스트 정보를 final_combined_text에 추가
            std_text_addition = self._create_std_text_for_integration(std_text_fields)
            
            has_std_text = std_text_addition != ''
            if has_std_text.any():
                self.integrated_df.loc[has_std_text, 'final_combined_text'] = (
                    self.integrated_df.loc[has_std_text, 'final_combined_text'] + ' ' + 
                    std_text_addition[has_std_text]
                ).str.strip()
                
                # 데이터 소스 업데이트
                current_source = self.integrated_df.loc[has_std_text, 'data_source']
                self.integrated_df.loc[has_std_text, 'data_source'] = current_source + '_with_std'
                
                print(f"  - {has_std_text.sum()}개 항목에 표준품명 정보 추가")
            
            # [DEBUG] 3단계 후 데이터 소스 분포
            self._show_data_source_distribution(self.integrated_df)
        
        # 4단계: 최종 데이터 정리
        print("\n4단계: 최종 데이터 정리")
        
        # [CLEANUP] 중간 combined_text 제거 (final_combined_text만 남김)
        if 'combined_text' in self.integrated_df.columns:
            self.integrated_df = self.integrated_df.drop(columns=['combined_text'])
            print("  - 중간 combined_text 제거됨")
        
        # final_combined_text 정리
        self.integrated_df['final_combined_text'] = (
            self.integrated_df['final_combined_text']
            .fillna('')
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
        )
        
        # 빈 텍스트를 HS_KEY 또는 챕터 설명으로 대체
        empty_mask = (
            (self.integrated_df['final_combined_text'] == '') | 
            (self.integrated_df['final_combined_text'].isna())
        )
        
        if empty_mask.any():
            print(f"  - 빈 텍스트 {empty_mask.sum()}개를 보완 중...")
            
            for idx in self.integrated_df[empty_mask].index:
                hs_key = self.integrated_df.loc[idx, 'HS_KEY']
                chapter = hs_key[:2] if len(hs_key) >= 2 else '00'
                
                if chapter in self.chapter_descriptions:
                    desc = self.chapter_descriptions[chapter]
                    self.integrated_df.loc[idx, 'final_combined_text'] = f"{desc} {hs_key}"
                else:
                    self.integrated_df.loc[idx, 'final_combined_text'] = hs_key
        
        # 계층 정보 추가
        self.integrated_df['chapter'] = self.integrated_df['HS_KEY'].str[:2]
        self.integrated_df['heading'] = self.integrated_df['HS_KEY'].str[:4]
        self.integrated_df['subheading'] = self.integrated_df['HS_KEY'].str[:6]
        
        # [DEBUG] 최종 결과 디버그
        if self.debug_mode:
            print(f"\n[DEBUG] 최종 통합 결과:")
            print(f"  최종 레코드: {len(self.integrated_df):,}개")
            print(f"  최종 컬럼: {len(self.integrated_df.columns)}개")
            print(f"  컬럼 목록: {list(self.integrated_df.columns)}")
            
            # 텍스트 길이 분포
            text_lengths = self.integrated_df['final_combined_text'].str.len()
            print(f"\n  📏 텍스트 길이 분포:")
            print(f"    평균: {text_lengths.mean():.1f}자")
            print(f"    최소: {text_lengths.min()}자")
            print(f"    최대: {text_lengths.max()}자")
            print(f"    빈 텍스트: {(text_lengths == 0).sum()}개")
            
            # 최종 샘플 데이터
            print(f"\n  [INFO] 최종 통합 샘플 데이터 (상위 3개):")
            sample_cols = ['HS_KEY', 'final_combined_text', 'data_source', 'chapter']
            sample = self.integrated_df[sample_cols].head(3)
            
            for idx, row in sample.iterrows():
                print(f"\n  [{idx}]")
                print(f"    HS_KEY: {row['HS_KEY']}")
                print(f"    Chapter: {row['chapter']}")
                print(f"    Data Source: {row['data_source']}")
                text = str(row['final_combined_text'])
                if len(text) > 150:
                    text = text[:150] + "..."
                print(f"    Final Text: {text}")
        
        # 최종 통계
        print(f"\n통합 완료: {len(self.integrated_df)}개 항목")
        
        # 데이터 소스별 통계
        source_stats = self.integrated_df['data_source'].value_counts()
        print("\n데이터 소스별 분포:")
        for source, count in source_stats.items():
            print(f"  - {source}: {count:,}개")
        
        # 텍스트 품질 통계
        text_lengths = self.integrated_df['final_combined_text'].str.len()
        print(f"\n텍스트 품질:")
        print(f"  - 평균 길이: {text_lengths.mean():.1f}자")
        print(f"  - 빈 텍스트: {(text_lengths == 0).sum()}개")
        
        print("="*60)
        return True

   
    
    def _find_matching_column(self, target_field, available_columns):
        """필드명 유연한 매칭"""
        # 정확한 매칭 먼저
        if target_field in available_columns:
            return target_field
        
        # 키워드 기반 매칭
        for col in available_columns:
            if self._match_hsk_field(target_field, col):
                return col
        
        return None
    
    def _match_hsk_field(self, target_field, actual_col):
        """HSK 필드명 유연한 매칭"""
        # 세번 분류
        if '세번' in target_field and '품명' in target_field:
            if '세번' in actual_col and '품명' in actual_col:
                if '2단위' in target_field:
                    return '2단위' in actual_col
                elif '4단위' in target_field:
                    return '4단위' in actual_col
                elif '6단위' in target_field:
                    return '6단위' in actual_col
                elif '10단위' in target_field:
                    return '10단위' in actual_col
            return False
        
        # 신성질별 분류
        elif '신성질별' in target_field:
            if '신성질별' in actual_col:
                if '대분류명' in target_field:
                    return '대분류명' in actual_col
                elif '중분류명' in target_field:
                    return '중분류명' in actual_col
                elif '소분류명' in target_field:
                    return '소분류명' in actual_col
                elif '세분류명' in target_field:
                    return '세분류명' in actual_col and '세세분류명' not in actual_col
                elif '세세분류명' in target_field:
                    return '세세분류명' in actual_col
            return False
        
        # 현행 성질별 분류
        elif '현행' in target_field:
            if '현행' in actual_col:
                if '수입' in target_field:
                    return '수입' in actual_col
                elif '수출' in target_field:
                    return '수출' in actual_col
            return False
        
        return False
    
    def _extract_chapter_descriptions(self, extracted_fields, field_mapping):
        """챕터 설명 추출 (세번2단위품명)"""
        chapter_field = None
        for target, actual in field_mapping.items():
            if '세번2단위품명' in target:
                chapter_field = actual
                break
        
        if chapter_field:
            chapter_mapping = {}
            for _, row in self.hsk_classification_data.iterrows():
                if pd.notna(row['HS_KEY']) and pd.notna(row[chapter_field]):
                    chapter = row['HS_KEY'][:2]
                    desc = row[chapter_field]
                    if chapter not in chapter_mapping:
                        chapter_mapping[chapter] = desc
            
            self.chapter_descriptions = chapter_mapping
            print(f"  챕터 설명 추출: {len(self.chapter_descriptions)}개")
    
    def _create_hsk_combined_text(self, extracted_fields, field_mapping):
        """HSK 분류 데이터의 통합 텍스트 생성 (임시)"""
        print("  HSK 분류 통합 텍스트 생성 중...")
        
        # 가중치 설정
        field_weights = {
            '세번10단위품명': 4,
            '세번6단위품명': 3,
            '세번4단위품명': 2,
            '세번2단위품명': 2,
            '관세청 신성질별 분류세세분류명': 3,
            '관세청 신성질별 분류세분류명': 2,
            '관세청 신성질별 분류소분류명': 2,
            '관세청 신성질별 분류중분류명': 1,
            '관세청 신성질별 분류대분류명': 1,
        }
        
        combined_texts = []
        
        for _, row in self.hsk_classification_data.iterrows():
            text_parts = []
            
            for field in extracted_fields:
                if pd.notna(row[field]):
                    field_value = str(row[field]).strip()
                    if field_value:
                        # 원래 정의 필드 찾기
                        original_field = None
                        for orig, mapped in field_mapping.items():
                            if mapped == field:
                                original_field = orig
                                break
                        
                        weight = field_weights.get(original_field, 1)
                        for _ in range(weight):
                            text_parts.append(field_value)
            
            combined_text = ' '.join(text_parts) if text_parts else ''
            combined_texts.append(combined_text)
        
        self.hsk_classification_data['combined_text'] = combined_texts
        
        # 공백 정리
        self.hsk_classification_data['combined_text'] = (
            self.hsk_classification_data['combined_text']
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
    
    def _create_hs_text_for_integration(self, hs_fields):
        """HS 필드들로 텍스트 생성 (통합용)"""
        field_weights = {
            '한글품목명': 3,
            '영문품목명': 2, 
            'HS부호내용': 2,
            '한국표준무역분류명': 1,
            '성질통합분류코드명': 1
        }
        
        hs_texts = []
        for _, row in self.integrated_df.iterrows():
            text_parts = []
            
            for field in hs_fields:
                if field in row and pd.notna(row[field]):
                    field_value = str(row[field]).strip()
                    if field_value:
                        weight = field_weights.get(field, 1)
                        for _ in range(weight):
                            text_parts.append(field_value)
            
            hs_text = ' '.join(text_parts) if text_parts else ''
            hs_texts.append(hs_text)
        
        return pd.Series(hs_texts)
    
    def _create_std_text_for_integration(self, std_fields):
        """표준품명 필드들로 텍스트 생성 (통합용)"""
        field_weights = {}
        for field in std_fields:
            if '표준품명' in field and '영문' not in field:
                field_weights[field] = 3
            elif '영문' in field:
                field_weights[field] = 2
            else:
                field_weights[field] = 1
        
        std_texts = []
        for _, row in self.integrated_df.iterrows():
            text_parts = []
            
            for field in std_fields:
                if field in row and pd.notna(row[field]):
                    field_value = str(row[field]).strip()
                    if field_value:
                        weight = field_weights.get(field, 1)
                        for _ in range(weight):
                            text_parts.append(field_value)
            
            std_text = ' '.join(text_parts) if text_parts else ''
            std_texts.append(std_text)
        
        return pd.Series(std_texts)
    
    def get_integrated_data(self) -> Optional[pd.DataFrame]:
        """통합된 데이터프레임 반환"""
        return self.integrated_df
    
    def get_chapter_descriptions(self) -> Dict[str, str]:
        """챕터 설명 딕셔너리 반환"""
        return self.chapter_descriptions
    
    def load_all_data(self) -> bool:
        """모든 데이터 로드 및 통합 (HSK 중심)"""
        print("="*80)
        print("HS 코드 추천 시스템 - 데이터 로딩 시작 (HSK 중심, 디버그 모드)")
        print("="*80)
        
        # 1. HSK 분류 데이터 로드 (필수, 중심 데이터)
        if not self.load_hsk_classification_data():
            print("중심 데이터(HSK) 로드 실패 - 프로그램 종료")
            return False
        
        # 2. HS 코드 데이터 로드 (선택적, 보조 데이터)
        hs_success = self.load_hs_code_data()
        if hs_success:
            print("✓ HS 코드 데이터 로드 성공")
        else:
            print("[WARNING] HS 코드 데이터 로드 실패 (선택적 데이터)")
        
        # 3. 표준품명 데이터 로드 (선택적, 보조 데이터)
        std_success = self.load_standard_name_data()
        if std_success:
            print("✓ 표준품명 데이터 로드 성공")
        else:
            print("[WARNING] 표준품명 데이터 로드 실패 (선택적 데이터)")
        
        # 4. 데이터 통합
        if not self.integrate_data():
            print("데이터 통합 실패")
            return False
        
        print("="*80)
        print("데이터 로딩 및 통합 완료! (HSK 중심, 23개 필드)")
        print("="*80)
        
        return True
    
    def get_statistics(self) -> Dict:
        """데이터 통계 반환"""
        if self.integrated_df is None:
            return {}
        
        stats = {
            'total_items': len(self.integrated_df),
            'unique_hs_keys': self.integrated_df['HS_KEY'].nunique(),
            'chapters': len(self.integrated_df['chapter'].unique()),
            'data_sources': self.integrated_df['data_source'].value_counts().to_dict()
        }
        
        # 텍스트 품질 통계
        if 'final_combined_text' in self.integrated_df.columns:
            text_lengths = self.integrated_df['final_combined_text'].str.len()
            stats['text_quality'] = {
                'avg_length': text_lengths.mean(),
                'min_length': text_lengths.min(),
                'max_length': text_lengths.max(),
                'empty_texts': (text_lengths == 0).sum()
            }
        
        # 챕터 설명 통계
        stats['chapter_descriptions'] = len(self.chapter_descriptions)
        
        # 챕터별 분포
        if 'chapter' in self.integrated_df.columns:
            chapter_dist = self.integrated_df['chapter'].value_counts().head(10)
            stats['top_chapters'] = chapter_dist.to_dict()
        
        return stats

    def set_debug_mode(self, debug_mode: bool):
        """디버그 모드 설정"""
        self.debug_mode = debug_mode


def main():
    """메인 실행 함수"""
    print("🏭 HS 코드 데이터 처리기 실행")
    print("="*60)
    
    # 디버그 모드로 데이터 처리기 생성
    processor = DataProcessor(debug_mode=True)
    
    print("📋 데이터 로딩 및 통합 시작...")
    success = processor.load_all_data()
    
    if success:
        print("[OK] 데이터 처리 성공!")
        
        # 통계 정보 출력
        stats = processor.get_statistics()
        print(f"\n[INFO] 최종 통계:")
        print(f"   총 레코드: {stats.get('total_items', 0):,}개")
        print(f"   고유 HS_KEY: {stats.get('unique_hs_keys', 0):,}개")
        print(f"   챕터 수: {stats.get('chapters', 0)}개")
        
        # 샘플 데이터 보기
        integrated_df = processor.get_integrated_data()
        if integrated_df is not None:
            print(f"\n[INFO] 샘플 데이터 (상위 3개):")
            sample_cols = ['HS_KEY', 'final_combined_text', 'data_source']
            sample = integrated_df[sample_cols].head(3)
            
            for idx, row in sample.iterrows():
                print(f"\n[{idx}]")
                print(f"  HS_KEY: {row['HS_KEY']}")
                print(f"  Data Source: {row['data_source']}")
                text = str(row['final_combined_text'])
                if len(text) > 100:
                    text = text[:100] + "..."
                print(f"  Combined Text: {text}")
        
        # 저장할지 물어보기
        save_choice = input("\n[SAVE] 결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
        if save_choice == 'y':
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"integrated_hs_data_{timestamp}.xlsx"
                
                integrated_df.to_excel(output_path, index=False)
                print(f"[OK] 저장 완료: {output_path}")
            except Exception as e:
                print(f"[ERROR] 저장 실패: {e}")
    else:
        print("[ERROR] 데이터 처리 실패!")


if __name__ == "__main__":
    main()
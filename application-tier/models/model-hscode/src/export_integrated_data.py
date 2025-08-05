import pandas as pd
import os
from datetime import datetime


class CorrectedDataProcessor:
    def __init__(self):
        self.hs_file = "C:/Users/User/통관/관세청_HS부호_2025.csv"
        self.std_file = "C:/Users/User/통관/관세청_표준품명_20250101.xlsx"
        self.hsk_file = "C:/Users/User/통관/관세청_HSK별 신성질별_성질별 분류_20250101.xlsx"
        
        # 핵심: HSK 데이터를 중심으로 설정
        self.hsk_data = None  # 중심 데이터
        self.hs_data = None   # 보조 데이터
        self.standard_data = None  # 보조 데이터
        self.integrated_df = None
        
    def load_hsk_data_as_main(self):
        """🎯 중심 데이터: 관세청_HSK별 로딩 (15개 필드만)"""
        print("1. 중심 데이터 로딩: 관세청_HSK별 신성질별...")
        
        try:
            self.hsk_data = pd.read_excel(self.hsk_file, sheet_name=0)
            print(f"   원본: {len(self.hsk_data):,}개")
            print(f"   컬럼 수: {len(self.hsk_data.columns)}개")
            
            # 🔐 매핑 키 생성 (HS10단위부호 → HS_KEY)
            hs_col = None
            for col in self.hsk_data.columns:
                if 'HS10단위부호' in col or 'HS10자리' in col:
                    hs_col = col
                    break
            
            if not hs_col:
                print("   ❌ HS10단위부호 컬럼 없음")
                return False
            
            self.hsk_data['HS_KEY'] = self.hsk_data[hs_col].astype(str).str.zfill(10)
            print(f"   ✅ HS_KEY 생성: {hs_col} → HS_KEY")
            print(f"      샘플: {self.hsk_data[hs_col].iloc[0]} → {self.hsk_data['HS_KEY'].iloc[0]}")
            
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
            
            print(f"\n   📋 정의된 15개 필드 매칭 중...")
            
            # 실제 존재하는 필드 찾기 (유연한 매칭)
            extracted_fields = []
            field_mapping = {}
            
            for target_field in defined_fields:
                found_col = None
                # 정확한 매칭 먼저
                if target_field in self.hsk_data.columns:
                    found_col = target_field
                else:
                    # 키워드 기반 매칭
                    for col in self.hsk_data.columns:
                        if self._match_hsk_field(target_field, col):
                            found_col = col
                            break
                
                if found_col:
                    extracted_fields.append(found_col)
                    field_mapping[target_field] = found_col
                    print(f"   ✅ {target_field}")
                    print(f"      → {found_col}")
                else:
                    print(f"   ❌ {target_field}: 찾을 수 없음")
            
            print(f"\n   📊 추출 결과: {len(extracted_fields)}/15개 필드")
            
            # 🎯 필요한 컬럼만 선택 (HS_KEY + 추출된 필드만)
            keep_columns = ['HS_KEY'] + extracted_fields
            print(f"   🎯 최종 선택 컬럼: {len(keep_columns)}개")
            
            # 원본 데이터를 필요한 컬럼만으로 제한
            self.hsk_data = self.hsk_data[keep_columns].copy()
            
            print(f"   📏 최종 데이터 크기: {self.hsk_data.shape}")
            print(f"   🗂️ 최종 컬럼: {list(self.hsk_data.columns)}")
            
            # combined_text 생성 (나중에 제거될 예정)
            self._create_hsk_combined_text(extracted_fields, field_mapping)
            
            self.hsk_data['data_source'] = 'hsk_main'
            print(f"   ✅ 중심 데이터 처리 완료: {len(self.hsk_data):,}개")
            return True
            
        except Exception as e:
            print(f"   ❌ HSK 데이터 로드 실패: {e}")
            return False
    
    def _match_hsk_field(self, target_field, actual_col):
        """HSK 필드명 유연한 매칭"""
        # 세번 분류
        if '세번' in target_field and '품명' in target_field:
            if '세번' in actual_col and '품명' in actual_col:
                # 단위 매칭 확인
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
    
    def _create_hsk_combined_text(self, extracted_fields, field_mapping):
        """HSK combined_text 생성 (임시, 나중에 제거됨)"""
        print("   🔤 HSK 임시 combined_text 생성...")
        
        # 가중치 설정 (중요도에 따라)
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
        
        for _, row in self.hsk_data.iterrows():
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
        
        self.hsk_data['combined_text'] = combined_texts
        self.hsk_data['combined_text'] = (
            self.hsk_data['combined_text']
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
        
        # 빈 텍스트 확인
        empty_count = (self.hsk_data['combined_text'] == '').sum()
        print(f"      텍스트 생성 완료, 빈 텍스트: {empty_count}개")
    
    def load_hs_data_as_supplement(self):
        """🔗 보조 데이터: 관세청_HS부호 로딩 (5개 필드만)"""
        print("\n2. 보조 데이터 로딩: 관세청_HS부호...")
        
        try:
            self.hs_data = pd.read_csv(self.hs_file, encoding='utf-8')
            print(f"   원본: {len(self.hs_data):,}개")
            
            # HS_KEY 생성 (HS부호 → HS_KEY)
            if 'HS부호' not in self.hs_data.columns:
                print("   ❌ HS부호 컬럼 없음")
                return False
            
            self.hs_data['HS_KEY'] = self.hs_data['HS부호'].astype(str).str.zfill(10)
            print(f"   ✅ HS_KEY 생성: HS부호 → HS_KEY")
            
            # 📄 정의된 5개 검색 벡터 필드만 추출
            defined_fields = [
                '한글품목명', '영문품목명', 'HS부호내용', 
                '한국표준무역분류명', '성질통합분류코드명'
            ]
            
            print(f"   📋 정의된 5개 필드 확인 중...")
            
            extracted_fields = []
            for field in defined_fields:
                if field in self.hs_data.columns:
                    extracted_fields.append(field)
                    print(f"   ✅ {field}")
                else:
                    print(f"   ❌ {field}: 없음")
            
            # 🎯 필요한 컬럼만 선택
            keep_columns = ['HS_KEY'] + extracted_fields
            self.hs_data = self.hs_data[keep_columns].copy()
            
            print(f"   🎯 최종 컬럼: {list(self.hs_data.columns)}")
            print(f"   📊 추출된 필드: {len(extracted_fields)}/5개")
            print(f"   📏 데이터 크기: {self.hs_data.shape}")
            
            print(f"   ✅ 보조 데이터 처리 완료: {len(self.hs_data):,}개")
            return True
            
        except Exception as e:
            print(f"   ❌ HS 데이터 로드 실패: {e}")
            return False
    
    def load_standard_data_as_supplement(self):
        """🔗 보조 데이터: 관세청_표준품명 로딩 (3개 필드만)"""
        print("\n3. 보조 데이터 로딩: 관세청_표준품명...")
        
        try:
            self.standard_data = pd.read_excel(self.std_file)
            print(f"   원본: {len(self.standard_data):,}개")
            print(f"   컬럼 샘플: {list(self.standard_data.columns)[:5]}...")
            
            # HS_KEY 생성 (HS코드 → HS_KEY)
            hs_col = None
            for col in self.standard_data.columns:
                if 'HS' in col and ('코드' in col or '부호' in col):
                    hs_col = col
                    break
            
            if not hs_col:
                print("   ❌ HS코드 컬럼 없음")
                return False
            
            self.standard_data['HS_KEY'] = self.standard_data[hs_col].astype(str).str.zfill(10)
            print(f"   ✅ HS_KEY 생성: {hs_col} → HS_KEY")
            
            # 📄 정의된 3개 검색 벡터 필드만 추출
            defined_fields = ['표준품명', '표준품명영문', '세부분류']
            
            print(f"   📋 정의된 3개 필드 확인 중...")
            
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
                    print(f"   ✅ {target_field}")
                    print(f"      → {found_col}")
                else:
                    print(f"   ❌ {target_field}: 없음")
            
            if not field_mapping.get('표준품명'):
                print("   ❌ 핵심 컬럼 '표준품명'이 없어 건너뜀")
                return False
            
            # 🎯 필요한 컬럼만 선택
            keep_columns = ['HS_KEY'] + extracted_fields
            self.standard_data = self.standard_data[keep_columns].copy()
            
            print(f"   🎯 최종 컬럼: {list(self.standard_data.columns)}")
            print(f"   📊 추출된 필드: {len(extracted_fields)}/3개")
            
            # 빈 표준품명 제거
            if field_mapping.get('표준품명'):
                std_col = field_mapping['표준품명']
                before_clean = len(self.standard_data)
                self.standard_data = self.standard_data[
                    self.standard_data[std_col].notna() & 
                    (self.standard_data[std_col].str.strip() != '')
                ]
                print(f"   🧹 빈 표준품명 제거: {before_clean:,} → {len(self.standard_data):,}개")
            
            print(f"   📏 최종 데이터 크기: {self.standard_data.shape}")
            print(f"   ✅ 보조 데이터 처리 완료: {len(self.standard_data):,}개")
            return True
            
        except Exception as e:
            print(f"   ❌ 표준품명 데이터 로드 실패: {e}")
            return False
    
    def integrate_all_data(self):
        """🎯 HSK를 중심으로 다른 데이터 LEFT JOIN (single combined_text)"""
        print("\n4. 데이터 통합: HSK 중심 LEFT JOIN...")
        
        if self.hsk_data is None:
            print("   ❌ 중심 데이터(HSK)가 없음")
            return False
        
        # HSK 데이터를 기본으로 시작
        print("   🎯 HSK 데이터를 중심으로 설정")
        self.integrated_df = self.hsk_data.copy()
        
        # HSK의 combined_text를 final_combined_text로 시작
        self.integrated_df['final_combined_text'] = self.integrated_df['combined_text']
        print(f"      기본: {len(self.integrated_df):,}개")
        
        # HS 데이터 LEFT JOIN
        if self.hs_data is not None:
            print("   🔗 HS 데이터 LEFT JOIN...")
            
            # HS 데이터에서 텍스트 필드만 가져오기
            hs_text_fields = [col for col in self.hs_data.columns 
                             if col != 'HS_KEY']
            
            hs_to_merge = self.hs_data[['HS_KEY'] + hs_text_fields]
            
            before_merge = len(self.integrated_df)
            self.integrated_df = pd.merge(
                self.integrated_df,
                hs_to_merge,
                on='HS_KEY',
                how='left'
            )
            
            print(f"      병합 후: {before_merge:,} → {len(self.integrated_df):,}개")
            
            # HS 텍스트 정보를 직접 final_combined_text에 추가
            hs_text_addition = self._create_hs_text_for_integration(hs_text_fields)
            
            has_hs_text = hs_text_addition != ''
            if has_hs_text.any():
                self.integrated_df.loc[has_hs_text, 'final_combined_text'] = (
                    self.integrated_df.loc[has_hs_text, 'final_combined_text'] + ' ' + 
                    hs_text_addition[has_hs_text]
                ).str.strip()
                
                self.integrated_df.loc[has_hs_text, 'data_source'] = 'hsk_with_hs'
                print(f"      ✅ HS 정보 추가: {has_hs_text.sum():,}개")
        else:
            print("   ⚠️ HS 데이터 없음 - 건너뜀")
        
        # 표준품명 데이터 LEFT JOIN
        if self.standard_data is not None:
            print("   🔗 표준품명 데이터 LEFT JOIN...")
            
            # 표준품명 데이터에서 텍스트 필드만 가져오기
            std_text_fields = [col for col in self.standard_data.columns 
                              if col != 'HS_KEY']
            
            std_to_merge = self.standard_data[['HS_KEY'] + std_text_fields]
            
            before_merge = len(self.integrated_df)
            self.integrated_df = pd.merge(
                self.integrated_df,
                std_to_merge,
                on='HS_KEY',
                how='left'
            )
            
            print(f"      병합 후: {before_merge:,} → {len(self.integrated_df):,}개")
            
            # 표준품명 텍스트 정보를 직접 final_combined_text에 추가
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
                
                print(f"      ✅ 표준품명 정보 추가: {has_std_text.sum():,}개")
        else:
            print("   ⚠️ 표준품명 데이터 없음 - 건너뜀")
        
        # 🗑️ 중간 combined_text 제거 (final_combined_text만 남김)
        if 'combined_text' in self.integrated_df.columns:
            self.integrated_df = self.integrated_df.drop(columns=['combined_text'])
            print("   🗑️ 중간 combined_text 제거됨")
        
        # 최종 텍스트 정리
        self.integrated_df['final_combined_text'] = (
            self.integrated_df['final_combined_text']
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )
        
        # 빈 텍스트 확인
        empty_count = (self.integrated_df['final_combined_text'].str.len() == 0).sum()
        avg_length = self.integrated_df['final_combined_text'].str.len().mean()
        
        print(f"   ✅ 통합 완료: {len(self.integrated_df):,}개")
        print(f"   🎯 최종 텍스트 컬럼: final_combined_text만 유지")
        print(f"   📏 평균 텍스트 길이: {avg_length:.1f}자")
        print(f"   🔍 빈 텍스트: {empty_count}개")
        
        return True
    
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
        # 필드명에서 실제 타입 추출하여 가중치 설정
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
    
    def run_corrected_integration(self):
        """🔧 수정된 통합 프로세스 실행"""
        print("🔧 수정된 데이터 통합 프로세스")
        print("="*70)
        print("🎯 중심 데이터: 관세청_HSK별 (15개 필드)")
        print("🔗 보조 데이터: 관세청_HS부호 (5개 필드) + 관세청_표준품명 (3개 필드)")
        print("🔐 매핑 키: HS_KEY (10자리)")
        print("📄 결과: final_combined_text 단일 텍스트 컬럼")
        print("="*70)
        
        # 1. 중심 데이터 로드 (필수)
        if not self.load_hsk_data_as_main():
            print("❌ 중심 데이터 로드 실패")
            return None
        
        # 2. 보조 데이터 로드 (선택적)
        hs_success = self.load_hs_data_as_supplement()
        std_success = self.load_standard_data_as_supplement()
        
        # 3. 통합
        if not self.integrate_all_data():
            print("❌ 통합 실패")
            return None
        
        # 4. 최종 결과 정리
        print("\n" + "="*70)
        print("🎉 수정된 통합 완료!")
        
        # 데이터 소스별 분포
        source_dist = self.integrated_df['data_source'].value_counts()
        print("\n📊 데이터 소스별 분포:")
        for source, count in source_dist.items():
            pct = count / len(self.integrated_df) * 100
            print(f"   {source}: {count:,}개 ({pct:.1f}%)")
        
        print(f"\n📊 최종 통계:")
        print(f"   총 레코드: {len(self.integrated_df):,}개")
        print(f"   총 컬럼: {len(self.integrated_df.columns)}개")
        print(f"   고유 HS_KEY: {self.integrated_df['HS_KEY'].nunique():,}개")
        print("="*70)
        
        return self.integrated_df
    
    def show_final_structure(self):
        """최종 데이터 구조 표시"""
        if self.integrated_df is None:
            print("통합 데이터 없음")
            return
        
        print("\n📋 최종 데이터 구조:")
        print("="*50)
        
        # 핵심 컬럼
        core_cols = ['HS_KEY', 'final_combined_text', 'data_source']
        print("🎯 핵심 컬럼:")
        for col in core_cols:
            if col in self.integrated_df.columns:
                print(f"   ✅ {col}")
        
        # HSK 관련 컬럼
        hsk_cols = [col for col in self.integrated_df.columns 
                   if col not in core_cols and not col.startswith(('hs_', 'std_'))]
        
        if hsk_cols:
            print(f"\n🎯 HSK 필드 ({len(hsk_cols)}개):")
            for col in hsk_cols:
                print(f"   - {col}")
        
        # HS 관련 컬럼
        hs_cols = [col for col in self.integrated_df.columns if '한글품목명' in col or '영문품목명' in col or 'HS부호내용' in col or '한국표준무역분류명' in col or '성질통합분류코드명' in col]
        if hs_cols:
            print(f"\n🔗 HS 필드 ({len(hs_cols)}개):")
            for col in hs_cols:
                print(f"   - {col}")
        
        # 표준품명 관련 컬럼
        std_cols = [col for col in self.integrated_df.columns if '표준품명' in col or '세부분류' in col]
        if std_cols:
            print(f"\n🔗 표준품명 필드 ({len(std_cols)}개):")
            for col in std_cols:
                print(f"   - {col}")
        
        print(f"\n📊 전체 컬럼 수: {len(self.integrated_df.columns)}개")
        print(f"📊 전체 레코드 수: {len(self.integrated_df):,}개")
        
    def get_sample_data(self, n=5):
        """샘플 데이터 조회"""
        if self.integrated_df is None:
            return None
        
        sample_cols = ['HS_KEY', 'final_combined_text', 'data_source']
        return self.integrated_df[sample_cols].head(n)


class DataExporter:
    """데이터 내보내기 클래스"""
    
    def __init__(self, output_dir="./output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_integrated_data(self, integrated_df, processor):
        """통합된 데이터 내보내기"""
        if integrated_df is None:
            print("❌ 내보낼 데이터 없음")
            return False
        
        print(f"\n📤 데이터 내보내기 ({self.output_dir})")
        print("="*50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 메인 Excel 파일 (모든 시트 포함)
        excel_path = os.path.join(self.output_dir, f"integrated_hs_data_{timestamp}.xlsx")
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 전체 데이터 시트
            integrated_df.to_excel(writer, sheet_name='통합데이터_전체', index=False)
            
            # 데이터 소스별 시트
            for source in integrated_df['data_source'].unique():
                source_data = integrated_df[integrated_df['data_source'] == source]
                sheet_name = f"{source}"[:31]  # Excel 시트명 길이 제한
                source_data.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 샘플 시트 (각 소스별 상위 50개)
            for source in integrated_df['data_source'].unique():
                source_sample = integrated_df[integrated_df['data_source'] == source].head(50)
                sheet_name = f"샘플_{source}"[:31]
                source_sample.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 통계 시트
            stats_rows = [
                ['항목', '값'],
                ['전체 레코드 수', f"{len(integrated_df):,}"],
                ['고유 HS_KEY 수', f"{integrated_df['HS_KEY'].nunique():,}"],
                ['전체 컬럼 수', len(integrated_df.columns)],
                ['평균 텍스트 길이', f"{integrated_df['final_combined_text'].str.len().mean():.1f}자"],
                ['빈 텍스트 수', (integrated_df['final_combined_text'].str.len() == 0).sum()],
                [''],
                ['데이터 소스별 분포', ''],
            ]
            
            for source, count in integrated_df['data_source'].value_counts().items():
                pct = count / len(integrated_df) * 100
                stats_rows.append([f"  {source}", f"{count:,} ({pct:.1f}%)"])
            
            stats_df = pd.DataFrame(stats_rows)
            stats_df.to_excel(writer, sheet_name='통계정보', index=False, header=False)
        
        print(f"📄 Excel 파일: {excel_path}")
        
        # 2. 머신러닝용 CSV 파일 (핵심 컬럼만)
        csv_path = os.path.join(self.output_dir, f"ml_ready_data_{timestamp}.csv")
        ml_columns = ['HS_KEY', 'final_combined_text', 'data_source']
        
        integrated_df[ml_columns].to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"🤖 ML용 CSV: {csv_path}")
        
        # 3. 구조 정보 파일
        structure_path = os.path.join(self.output_dir, f"data_structure_{timestamp}.txt")
        with open(structure_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("HS 코드 통합 데이터 구조 정보\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"총 레코드: {len(integrated_df):,}개\n")
            f.write(f"총 컬럼: {len(integrated_df.columns)}개\n")
            f.write(f"고유 HS_KEY: {integrated_df['HS_KEY'].nunique():,}개\n\n")
            
            f.write("데이터 소스별 분포:\n")
            for source, count in integrated_df['data_source'].value_counts().items():
                pct = count / len(integrated_df) * 100
                f.write(f"  {source}: {count:,}개 ({pct:.1f}%)\n")
            
            f.write(f"\n전체 컬럼 목록:\n")
            for i, col in enumerate(integrated_df.columns, 1):
                f.write(f"  {i:2d}. {col}\n")
        
        print(f"📋 구조 정보: {structure_path}")
        
        print(f"\n✅ 내보내기 완료! 총 {len(integrated_df):,}개 레코드")
        print(f"📁 출력 디렉토리: {self.output_dir}")
        
        return True


def main():
    """메인 실행 함수"""
    print("🏭 HS 코드 데이터 통합 도구 v2.0")
    print("🎯 HSK별 신성질별 데이터 중심 통합")
    print("📄 정의된 23개 필드 정확 추출")
    print("🔐 HS_KEY 매핑 키 기반 통합")
    print("="*70)
    
    # 실행 옵션
    print("\n실행 옵션:")
    print("1. 데이터 통합만 실행 (미리보기)")
    print("2. 데이터 통합 + 파일 내보내기")
    
    choice = input("선택 (1 또는 2, 기본: 1): ").strip()
    
    # 데이터 통합 실행
    processor = CorrectedDataProcessor()
    integrated_df = processor.run_corrected_integration()
    
    if integrated_df is not None:
        # 구조 정보 표시
        processor.show_final_structure()
        
        # 샘플 데이터 표시
        print(f"\n📝 샘플 데이터 (상위 3개):")
        sample_data = processor.get_sample_data(3)
        if sample_data is not None:
            print(sample_data.to_string(max_colwidth=50))
        
        # 파일 내보내기 (옵션 2 선택시)
        if choice == "2":
            output_dir = input(f"\n📁 출력 디렉토리 (기본: ./output): ").strip()
            if not output_dir:
                output_dir = "./output"
            
            exporter = DataExporter(output_dir)
            success = exporter.export_integrated_data(integrated_df, processor)
            
            if success:
                print(f"\n🎉 완료! 모든 파일이 '{output_dir}'에 저장되었습니다.")
            else:
                print("\n❌ 내보내기 실패!")
        else:
            print(f"\n✅ 통합 완료! 총 {len(integrated_df):,}개 레코드")
            save_choice = input("파일로 저장하시겠습니까? (y/n): ").strip().lower()
            if save_choice == 'y':
                exporter = DataExporter()
                exporter.export_integrated_data(integrated_df, processor)
    
    else:
        print("❌ 통합 실패!")


if __name__ == "__main__":
    main()

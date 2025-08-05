import os
import json
import pickle
import hashlib
import numpy as np
import pandas as pd
import joblib
import torch
from datetime import datetime
from typing import Dict, Optional, Any
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (model-hscode 폴더)
sys.path.append(str(Path(__file__).parent.parent))
from config import FILE_PATHS

class CacheManager:
    """캐시 관리 담당 클래스 (final_combined_text 지원)"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # 기본 캐시 디렉토리를 절대 경로로 설정
            project_root = Path(__file__).parent.parent
            cache_dir = project_root /"model-hscode"/"cache"/ "hs_code_cache"
        self.cache_dir = cache_dir
        self.cache_paths = {
            'embeddings': os.path.join(cache_dir, 'semantic_embeddings.npy'),
            'tfidf_matrix': os.path.join(cache_dir, 'tfidf_matrix.pkl'),
            'tfidf_vectorizer': os.path.join(cache_dir, 'tfidf_vectorizer.pkl'),
            'integrated_df': os.path.join(cache_dir, 'integrated_df.pkl'),
            'metadata': os.path.join(cache_dir, 'cache_metadata.json'),
            'mappings': os.path.join(cache_dir, 'mappings.pkl'),
            'chapter_descriptions': os.path.join(cache_dir, 'chapter_descriptions.pkl')
        }
        
        # 캐시 디렉토리 생성
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def calculate_data_hash(self, semantic_model_name: str) -> str:
        """데이터 파일들의 해시값 계산"""
        hash_md5 = hashlib.md5()
        
        # 각 데이터 파일의 해시값 계산
        for file_key, file_path in FILE_PATHS.items():
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
            else:
                # 파일이 없으면 빈 문자열 해시
                hash_md5.update(b'')
        
        # 모델명도 해시에 포함
        hash_md5.update(semantic_model_name.encode())
        
        return hash_md5.hexdigest()
    
    def load_metadata(self) -> Dict:
        """캐시 메타데이터 로드"""
        if os.path.exists(self.cache_paths['metadata']):
            try:
                with open(self.cache_paths['metadata'], 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"메타데이터 로드 실패: {e}")
        
        return {}
    
    def save_metadata(self, metadata: Dict):
        """캐시 메타데이터 저장"""
        try:
            with open(self.cache_paths['metadata'], 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"메타데이터 저장 실패: {e}")
    
    def is_cache_valid(self, semantic_model_name: str) -> bool:
        """캐시 유효성 검사 (final_combined_text 구조 확인 포함)"""
        print("캐시 유효성 검사 중...")
        
        metadata = self.load_metadata()
        if not metadata:
            print("  캐시 메타데이터 없음")
            return False
        
        # 데이터 해시 비교
        current_hash = self.calculate_data_hash(semantic_model_name)
        cached_hash = metadata.get('data_hash')
        
        print(f"  현재 데이터 해시: {current_hash}")
        print(f"  저장된 캐시 해시: {cached_hash if cached_hash else '없음'}")
        
        if current_hash != cached_hash:
            print("  데이터 변경 감지 - 캐시 무효화")
            return False
        
        # 필수 캐시 파일 존재 확인
        required_files = ['embeddings', 'tfidf_matrix', 'tfidf_vectorizer', 'integrated_df']
        all_exist = True
        
        for file_key in required_files:
            path = self.cache_paths[file_key]
            exists = os.path.exists(path)
            print(f"  캐시 파일 '{file_key}': {'존재' if exists else '없음'}")
            if not exists:
                all_exist = False
        
        # [DEBUG] integrated_df 구조 확인 (final_combined_text 컬럼 존재 여부)
        if all_exist and os.path.exists(self.cache_paths['integrated_df']):
            try:
                cached_df = pd.read_pickle(self.cache_paths['integrated_df'])
                if 'final_combined_text' not in cached_df.columns:
                    print("  캐시된 데이터에 final_combined_text 컬럼 없음 - 캐시 무효화")
                    return False
                else:
                    print("  [OK] final_combined_text 컬럼 확인됨")
            except Exception as e:
                print(f"  캐시된 데이터프레임 확인 실패: {e} - 캐시 무효화")
                return False
        
        if all_exist:
            print("  모든 필수 캐시 파일 존재 및 구조 유효 - 캐시 유효")
            return True
        else:
            print("  필수 캐시 파일 일부 누락 - 캐시 무효화")
            return False
    
    def load_cache(self) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 로드 (final_combined_text 확인 포함)"""
        try:
            print("캐시에서 데이터 로딩 중...")
            
            cache_data = {}
            
            # 통합 데이터프레임 로드
            print("  통합 데이터프레임 로드...")
            cache_data['integrated_df'] = pd.read_pickle(self.cache_paths['integrated_df'])
            print(f"    {len(cache_data['integrated_df'])}개 항목")
            
            # [DEBUG] final_combined_text 컬럼 확인
            if 'final_combined_text' not in cache_data['integrated_df'].columns:
                print("    [ERROR] final_combined_text 컬럼이 없습니다!")
                
                # 대체 텍스트 컬럼 찾기
                text_candidates = ['combined_text', '한글품목명', '표준품명']
                for candidate in text_candidates:
                    if candidate in cache_data['integrated_df'].columns:
                        print(f"    [INFO] 대체 텍스트 컬럼 사용: {candidate}")
                        cache_data['integrated_df']['final_combined_text'] = (
                            cache_data['integrated_df'][candidate].fillna('')
                        )
                        break
                else:
                    print("    [ERROR] 사용 가능한 텍스트 컬럼이 없습니다!")
                    return None
            else:
                print("    [OK] final_combined_text 컬럼 확인됨")
            
            # 계층 구조 컬럼 확인 및 생성
            for col, length in [('chapter', 2), ('heading', 4), ('subheading', 6)]:
                if col not in cache_data['integrated_df'].columns:
                    if 'HS_KEY' in cache_data['integrated_df'].columns:
                        cache_data['integrated_df'][col] = cache_data['integrated_df']['HS_KEY'].str[:length]
                        print(f"    [INFO] {col} 컬럼 생성됨")
            
            # 의미 임베딩 로드
            print("  의미 임베딩 로드...")
            embeddings_array = np.load(self.cache_paths['embeddings'])
            cache_data['semantic_embeddings'] = torch.from_numpy(embeddings_array)
            print(f"    {cache_data['semantic_embeddings'].shape}")
            
            # TF-IDF 데이터 로드
            print("  TF-IDF 데이터 로드...")
            cache_data['tfidf_matrix'] = joblib.load(self.cache_paths['tfidf_matrix'])
            cache_data['tfidf_vectorizer'] = joblib.load(self.cache_paths['tfidf_vectorizer'])
            print(f"    매트릭스 크기: {cache_data['tfidf_matrix'].shape}")
            
            # 매핑 데이터 로드 (선택적)
            if os.path.exists(self.cache_paths['mappings']):
                print("  매핑 데이터 로드...")
                with open(self.cache_paths['mappings'], 'rb') as f:
                    mappings = pickle.load(f)
                    cache_data['standard_mapping'] = mappings.get('standard_mapping', {})
                    cache_data['reverse_mapping'] = mappings.get('reverse_mapping', {})
                print(f"    매핑: 표준품명 {len(cache_data['standard_mapping'])}개")
            else:
                cache_data['standard_mapping'] = {}
                cache_data['reverse_mapping'] = {}
            
            # 챕터 설명 로드 (선택적)
            if os.path.exists(self.cache_paths['chapter_descriptions']):
                print("  챕터 설명 로드...")
                with open(self.cache_paths['chapter_descriptions'], 'rb') as f:
                    cache_data['chapter_descriptions'] = pickle.load(f)
                print(f"    {len(cache_data['chapter_descriptions'])}개 챕터")
            else:
                cache_data['chapter_descriptions'] = {}
            
            print("캐시 데이터 로드 완료!")
            
            # [DEBUG] 로드된 데이터 상태 확인
            df = cache_data['integrated_df']
            print(f"  [INFO] 로드된 데이터 상태:")
            print(f"    총 레코드: {len(df):,}개")
            print(f"    컬럼 수: {len(df.columns)}개")
            print(f"    필수 컬럼 확인:")
            for col in ['HS_KEY', 'final_combined_text', 'data_source', 'chapter']:
                exists = col in df.columns
                print(f"      {col}: {'[OK]' if exists else '[ERROR]'}")
            
            # 텍스트 품질 확인
            if 'final_combined_text' in df.columns:
                text_lengths = df['final_combined_text'].str.len()
                empty_count = (text_lengths == 0).sum()
                print(f"    텍스트 품질:")
                print(f"      평균 길이: {text_lengths.mean():.1f}자")
                print(f"      빈 텍스트: {empty_count}개")
            
            return cache_data
            
        except Exception as e:
            print(f"캐시 로드 중 오류 발생: {e}")
            return None
    
    def save_cache(self, 
                   integrated_df: pd.DataFrame,
                   semantic_embeddings: torch.Tensor,
                   tfidf_matrix: Any,
                   tfidf_vectorizer: Any,
                   standard_mapping: Dict = None,
                   reverse_mapping: Dict = None,
                   chapter_descriptions: Dict = None,
                   semantic_model_name: str = '') -> bool:
        """데이터를 캐시에 저장 (final_combined_text 검증 포함)"""
        try:
            print("캐시에 데이터 저장 중...")
            
            # [DEBUG] 저장 전 데이터 검증
            if 'final_combined_text' not in integrated_df.columns:
                print("  [ERROR] final_combined_text 컬럼이 없습니다!")
                
                # 대체 텍스트 컬럼으로 생성 시도
                text_candidates = ['combined_text', '한글품목명', '표준품명']
                for candidate in text_candidates:
                    if candidate in integrated_df.columns:
                        print(f"  [INFO] {candidate}에서 final_combined_text 생성")
                        integrated_df = integrated_df.copy()
                        integrated_df['final_combined_text'] = (
                            integrated_df[candidate].fillna('')
                        )
                        break
                else:
                    print("  [ERROR] final_combined_text 생성 불가 - 저장 중단")
                    return False
            
            # 계층 구조 컬럼 확인 및 생성
            df_to_save = integrated_df.copy()
            for col, length in [('chapter', 2), ('heading', 4), ('subheading', 6)]:
                if col not in df_to_save.columns:
                    if 'HS_KEY' in df_to_save.columns:
                        df_to_save[col] = df_to_save['HS_KEY'].str[:length]
                        print(f"  [INFO] {col} 컬럼 생성됨")
            
            # 통합 데이터프레임 저장
            print("  통합 데이터프레임 저장...")
            df_to_save.to_pickle(self.cache_paths['integrated_df'])
            
            # 의미 임베딩 저장
            print("  의미 임베딩 저장...")
            if isinstance(semantic_embeddings, torch.Tensor):
                np.save(self.cache_paths['embeddings'], semantic_embeddings.cpu().numpy())
            else:
                np.save(self.cache_paths['embeddings'], semantic_embeddings)
            
            # TF-IDF 저장
            print("  TF-IDF 데이터 저장...")
            joblib.dump(tfidf_matrix, self.cache_paths['tfidf_matrix'])
            joblib.dump(tfidf_vectorizer, self.cache_paths['tfidf_vectorizer'])
            
            # 매핑 데이터 저장
            if standard_mapping is not None or reverse_mapping is not None:
                print("  매핑 데이터 저장...")
                mappings = {
                    'standard_mapping': standard_mapping or {},
                    'reverse_mapping': reverse_mapping or {}
                }
                with open(self.cache_paths['mappings'], 'wb') as f:
                    pickle.dump(mappings, f)
            
            # 챕터 설명 저장
            if chapter_descriptions:
                print("  챕터 설명 저장...")
                with open(self.cache_paths['chapter_descriptions'], 'wb') as f:
                    pickle.dump(chapter_descriptions, f)
            
            # 메타데이터 저장
            print("  메타데이터 저장...")
            
            # 텍스트 품질 통계
            text_lengths = df_to_save['final_combined_text'].str.len()
            
            metadata = {
                'data_hash': self.calculate_data_hash(semantic_model_name),
                'created_at': datetime.now().isoformat(),
                'model_name': semantic_model_name,
                'total_items': len(df_to_save),
                'cache_version': '2.1',  # final_combined_text 지원 버전
                'data_structure': {
                    'columns': len(df_to_save.columns),
                    'has_final_combined_text': True,
                    'text_quality': {
                        'avg_length': float(text_lengths.mean()),
                        'empty_count': int((text_lengths == 0).sum())
                    }
                },
                'file_info': {}
            }
            
            # 각 파일 크기 정보 추가
            for key, path in self.cache_paths.items():
                if os.path.exists(path):
                    size_mb = os.path.getsize(path) / (1024 * 1024)
                    metadata['file_info'][key] = f"{size_mb:.2f} MB"
            
            self.save_metadata(metadata)
            
            print("캐시 저장 완료!")
            print(f"  [INFO] 저장된 데이터:")
            print(f"    레코드: {len(df_to_save):,}개")
            print(f"    컬럼: {len(df_to_save.columns)}개")
            print(f"    텍스트 평균 길이: {text_lengths.mean():.1f}자")
            
            return True
            
        except Exception as e:
            print(f"캐시 저장 실패: {e}")
            return False
    
    def clear_cache(self) -> int:
        """캐시 파일들 삭제"""
        print("캐시 삭제 중...")
        
        deleted_count = 0
        for key, path in self.cache_paths.items():
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"  삭제: {key}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  삭제 실패 {key}: {e}")
        
        print(f"{deleted_count}개 캐시 파일 삭제 완료")
        return deleted_count
    
    def get_cache_info(self, semantic_model_name: str = '') -> Dict:
        """캐시 정보 반환 (final_combined_text 구조 정보 포함)"""
        metadata = self.load_metadata()
        
        cache_info = {
            'cache_dir': self.cache_dir,
            'cache_valid': self.is_cache_valid(semantic_model_name) if semantic_model_name else False,
            'metadata': metadata,
            'file_sizes': {},
            'total_size_mb': 0,
            'data_structure_info': {}
        }
        
        # 캐시 파일 크기 정보
        total_size = 0
        for key, path in self.cache_paths.items():
            if os.path.exists(path):
                size_bytes = os.path.getsize(path)
                size_mb = size_bytes / (1024 * 1024)
                cache_info['file_sizes'][key] = f"{size_mb:.2f} MB"
                total_size += size_bytes
            else:
                cache_info['file_sizes'][key] = "없음"
        
        cache_info['total_size_mb'] = total_size / (1024 * 1024)
        
        # 데이터 구조 정보 (메타데이터에서)
        if metadata and 'data_structure' in metadata:
            cache_info['data_structure_info'] = metadata['data_structure']
        
        # 실제 캐시된 데이터프레임 구조 확인 (빠른 확인)
        if os.path.exists(self.cache_paths['integrated_df']):
            try:
                # 헤더만 읽어서 구조 확인
                sample_df = pd.read_pickle(self.cache_paths['integrated_df'])
                cache_info['actual_structure'] = {
                    'total_records': len(sample_df),
                    'total_columns': len(sample_df.columns),
                    'has_final_combined_text': 'final_combined_text' in sample_df.columns,
                    'key_columns': {
                        'HS_KEY': 'HS_KEY' in sample_df.columns,
                        'data_source': 'data_source' in sample_df.columns,
                        'chapter': 'chapter' in sample_df.columns
                    }
                }
            except Exception as e:
                cache_info['actual_structure'] = {'error': str(e)}
        
        return cache_info
    
    def copy_from_colab(self, colab_cache_dir: str) -> bool:
        """코랩 캐시 디렉토리에서 로컬로 캐시 파일 복사"""
        import shutil
        
        print(f"코랩 캐시 복사: {colab_cache_dir} -> {self.cache_dir}")
        
        if not os.path.exists(colab_cache_dir):
            print(f"코랩 캐시 디렉토리 없음: {colab_cache_dir}")
            return False
        
        try:
            copied_count = 0
            for key, local_path in self.cache_paths.items():
                colab_file = os.path.join(colab_cache_dir, os.path.basename(local_path))
                
                if os.path.exists(colab_file):
                    shutil.copy2(colab_file, local_path)
                    print(f"  복사 완료: {key}")
                    copied_count += 1
                else:
                    print(f"  파일 없음: {key}")
            
            # 복사 후 구조 검증
            if copied_count > 0:
                print("  복사된 캐시 구조 검증 중...")
                if os.path.exists(self.cache_paths['integrated_df']):
                    try:
                        df = pd.read_pickle(self.cache_paths['integrated_df'])
                        if 'final_combined_text' not in df.columns:
                            print("  [WARNING] 복사된 캐시에 final_combined_text 컬럼 없음")
                            print("  이 캐시는 이전 버전일 수 있습니다.")
                        else:
                            print("  [OK] final_combined_text 컬럼 확인됨")
                    except Exception as e:
                        print(f"  구조 검증 실패: {e}")
            
            print(f"{copied_count}개 캐시 파일 복사 완료!")
            return copied_count > 0
            
        except Exception as e:
            print(f"캐시 복사 실패: {e}")
            return False
    
    def backup_cache(self, backup_dir: str) -> bool:
        """캐시 백업"""
        import shutil
        
        print(f"캐시 백업: {self.cache_dir} -> {backup_dir}")
        
        try:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            
            shutil.copytree(self.cache_dir, backup_dir)
            print("캐시 백업 완료!")
            return True
            
        except Exception as e:
            print(f"캐시 백업 실패: {e}")
            return False
    
    def restore_cache(self, backup_dir: str) -> bool:
        """캐시 복원"""
        import shutil
        
        print(f"캐시 복원: {backup_dir} -> {self.cache_dir}")
        
        if not os.path.exists(backup_dir):
            print(f"백업 디렉토리 없음: {backup_dir}")
            return False
        
        try:
            # 기존 캐시 삭제
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
            
            # 백업에서 복원
            shutil.copytree(backup_dir, self.cache_dir)
            print("캐시 복원 완료!")
            return True
            
        except Exception as e:
            print(f"캐시 복원 실패: {e}")
            return False
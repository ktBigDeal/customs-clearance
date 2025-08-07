#!/usr/bin/env python3
"""
벡터 DB 데이터 타입 분포 및 구조 분석 스크립트
전체 데이터베이스의 data_type, data_source 분포와 품질 분석
"""

import sys
from pathlib import Path
from collections import defaultdict, Counter

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.rag.vector_store import ChromaVectorStore
from src.rag.embeddings import OpenAIEmbedder
from src.utils.config import get_trade_agent_config, load_config

def analyze_data_distribution():
    """벡터 DB 데이터 분포 및 구조 분석"""
    print("📊 벡터 DB 데이터 분포 분석 시작...")
    
    try:
        # 환경 설정 로드
        config = load_config()
        trade_config = get_trade_agent_config()
        
        # 벡터 저장소 초기화
        vector_store = ChromaVectorStore(
            collection_name=trade_config["collection_name"],
            db_path="data/chroma_db"
        )
        
        print("✅ 벡터 DB 연결 완료")
        
        # === 1. 전체 컬렉션 통계 ===
        print(f"\n📈 전체 컬렉션 통계...")
        stats = vector_store.get_collection_stats()
        print(f"  총 문서 수: {stats.get('total_documents', 0)}개")
        print(f"  컬렉션 이름: {stats.get('collection_name', 'N/A')}")
        
        # === 2. 모든 문서 메타데이터 분석을 위한 샘플링 ===
        print(f"\n🔍 전체 문서 메타데이터 샘플링...")
        
        # 임베딩 모델 초기화 (샘플 검색용)
        embedder = OpenAIEmbedder()
        
        # 다양한 키워드로 샘플링하여 전체 데이터 구조 파악
        sample_queries = [
            "무역 규제 수입 수출",
            "동식물 검역 허용 국가", 
            "민원 상담 사례 통관",
            "HS코드 품목 분류",
            "관세 면세 감면"
        ]
        
        all_samples = []
        for query in sample_queries:
            query_embedding = embedder.embed_text(query)
            samples = vector_store.search_similar(
                query_embedding=query_embedding,
                top_k=100  # 각 쿼리당 100개씩 샘플링
            )
            all_samples.extend(samples)
        
        print(f"  샘플링된 문서 수: {len(all_samples)}개")
        
        # === 3. 메타데이터 필드 분석 ===
        print(f"\n📋 메타데이터 필드 분석...")
        
        all_metadata_keys = set()
        data_type_counter = Counter()
        data_source_counter = Counter()
        regulation_type_counter = Counter()
        product_name_counter = Counter()
        category_counter = Counter()
        
        for sample in all_samples:
            metadata = sample.get('metadata', {})
            all_metadata_keys.update(metadata.keys())
            
            # data_type 분포
            data_type = metadata.get('data_type', 'unknown')
            data_type_counter[data_type] += 1
            
            # data_source 분포
            data_source = metadata.get('data_source', 'unknown')
            data_source_counter[data_source] += 1
            
            # regulation_type 분포 (있는 경우)
            regulation_type = metadata.get('regulation_type', '')
            if regulation_type:
                regulation_type_counter[regulation_type] += 1
            
            # product_name 분포 (동식물 데이터)
            product_name = metadata.get('product_name', '')
            if product_name and '딸기' in product_name:
                product_name_counter[product_name] += 1
            
            # category 분포 (상담사례 데이터)
            category = metadata.get('category', '')
            if category:
                category_counter[category] += 1
        
        print(f"  발견된 메타데이터 필드: {len(all_metadata_keys)}개")
        print(f"  필드 목록: {sorted(all_metadata_keys)}")
        
        # === 4. data_type 분포 상세 분석 ===
        print(f"\n📊 data_type 분포 (샘플 기준):")
        total_samples = len(all_samples)
        for data_type, count in data_type_counter.most_common():
            percentage = (count / total_samples) * 100
            print(f"  {data_type}: {count}개 ({percentage:.1f}%)")
        
        # === 5. data_source 분포 상세 분석 ===
        print(f"\n📋 data_source 분포 (상위 10개):")
        for data_source, count in data_source_counter.most_common(10):
            percentage = (count / total_samples) * 100
            print(f"  {data_source}: {count}개 ({percentage:.1f}%)")
        
        # === 6. regulation_type 분포 ===
        if regulation_type_counter:
            print(f"\n⚖️ regulation_type 분포:")
            for reg_type, count in regulation_type_counter.most_common():
                print(f"  {reg_type}: {count}개")
        
        # === 7. 딸기 관련 product_name 분석 ===
        if product_name_counter:
            print(f"\n🍓 딸기 관련 제품명 분포:")
            for product, count in product_name_counter.most_common():
                print(f"  {product}: {count}개")
        
        # === 8. 상담사례 category 분포 ===
        if category_counter:
            print(f"\n📞 상담사례 카테고리 분포 (상위 10개):")
            for category, count in category_counter.most_common(10):
                print(f"  {category}: {count}개")
        
        # === 9. 특정 data_type별 상세 분석 ===
        print(f"\n🔍 data_type별 상세 분석...")
        
        # trade_regulation 데이터 분석
        trade_reg_samples = [s for s in all_samples if s.get('metadata', {}).get('data_type') == 'trade_regulation']
        if trade_reg_samples:
            print(f"\n📋 trade_regulation 데이터 ({len(trade_reg_samples)}개):")
            
            # data_source 분포
            trade_reg_sources = Counter(s.get('metadata', {}).get('data_source', 'unknown') for s in trade_reg_samples)
            for source, count in trade_reg_sources.most_common():
                print(f"  {source}: {count}개")
            
            # 동식물허용금지지역 데이터의 제품명 분석
            animal_plant_samples = [s for s in trade_reg_samples 
                                  if s.get('metadata', {}).get('data_source') == '동식물허용금지지역']
            if animal_plant_samples:
                print(f"\n🐕🌱 동식물허용금지지역 제품 분석 (상위 20개):")
                animal_products = Counter(s.get('metadata', {}).get('product_name', 'unknown') 
                                        for s in animal_plant_samples)
                for product, count in animal_products.most_common(20):
                    print(f"    {product}: {count}개")
        
        # consultation_case 데이터 분석
        consultation_samples = [s for s in all_samples if s.get('metadata', {}).get('data_type') == 'consultation_case']
        if consultation_samples:
            print(f"\n📞 consultation_case 데이터 ({len(consultation_samples)}개):")
            
            # data_source 분포
            consult_sources = Counter(s.get('metadata', {}).get('data_source', 'unknown') for s in consultation_samples)
            for source, count in consult_sources.most_common():
                print(f"  {source}: {count}개")
        
        # === 10. 데이터 품질 분석 ===
        print(f"\n✅ 데이터 품질 분석...")
        
        # 필수 필드 누락 분석
        missing_data_type = sum(1 for s in all_samples if not s.get('metadata', {}).get('data_type'))
        missing_data_source = sum(1 for s in all_samples if not s.get('metadata', {}).get('data_source'))
        
        print(f"  data_type 누락: {missing_data_type}개 ({(missing_data_type/total_samples)*100:.1f}%)")
        print(f"  data_source 누락: {missing_data_source}개 ({(missing_data_source/total_samples)*100:.1f}%)")
        
        # content 길이 분석
        content_lengths = [len(s.get('content', '')) for s in all_samples]
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        
        print(f"  평균 content 길이: {avg_content_length:.0f}자")
        print(f"  최소 content 길이: {min(content_lengths) if content_lengths else 0}자")
        print(f"  최대 content 길이: {max(content_lengths) if content_lengths else 0}자")
        
        # === 11. 권장사항 출력 ===
        print(f"\n{'='*60}")
        print(f"📋 분석 결과 요약 및 권장사항")
        print(f"{'='*60}")
        
        if 'trade_regulation' in data_type_counter and 'consultation_case' in data_type_counter:
            print("✅ data_type 분리가 잘 되어 있음 - 듀얼 에이전트 아키텍처 적합")
        else:
            print("⚠️ data_type 분리 확인 필요")
        
        if '동식물허용금지지역' in data_source_counter:
            print("✅ 동식물 규제 데이터 존재 - 전용 검색 로직 필요")
        else:
            print("❌ 동식물 규제 데이터 누락")
        
        trade_reg_ratio = data_type_counter.get('trade_regulation', 0) / total_samples
        consultation_ratio = data_type_counter.get('consultation_case', 0) / total_samples
        
        print(f"📊 데이터 비율: trade_regulation {trade_reg_ratio:.1%}, consultation_case {consultation_ratio:.1%}")
        
        if trade_reg_ratio > 0.3 and consultation_ratio > 0.3:
            print("✅ 균형잡힌 데이터 분포 - 듀얼 에이전트 권장")
        elif trade_reg_ratio > consultation_ratio * 2:
            print("⚠️ trade_regulation 데이터 과다 - 필터링 강화 필요")
        elif consultation_ratio > trade_reg_ratio * 2:
            print("⚠️ consultation_case 데이터 과다 - 규제 데이터 보강 필요")
        
        print("✅ 데이터 분포 분석 완료")
        
    except Exception as e:
        print(f"❌ 분석 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_data_distribution()
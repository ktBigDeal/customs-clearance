#!/usr/bin/env python3
"""
Document Processing Script

관세법 문서 처리 워크플로우를 실행하는 메인 스크립트입니다.
Chunking+Loader.ipynb 노트북의 기능을 명령행에서 실행할 수 있도록 구현했습니다.

Usage:
    python scripts/process_documents.py --all
    python scripts/process_documents.py --law 관세법
    python scripts/process_documents.py --law 관세법 --output custom_output.json
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import (
    load_config, get_law_data_paths, get_output_paths, get_pdf_data_paths, get_pdf_output_paths, 
    get_csv_data_paths, get_csv_output_paths, get_consultation_case_paths, validate_environment
)
from src.utils.file_utils import load_json_data, save_processed_documents
from src.data_processing.law_document_loader import CustomsLawLoader
from src.data_processing.trade_info_csv_loader import CSVDocumentLoader
from src.data_processing.pdf_processor import PDFDocumentProcessor
from src.data_processing.law_chunking_utils import analyze_chunking_results, print_sample_chunks, validate_chunk_integrity
from src.data_processing.pdf_chunking_utils import validate_pdf_chunks, analyze_pdf_processing_results, get_pdf_chunk_statistics

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_single_law(law_name: str, law_data: Dict[str, Any], output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """단일 법령 문서 처리
    
    Args:
        law_name (str): 법령명
        law_data (Dict[str, Any]): 법령 JSON 데이터
        output_path (Optional[Path]): 출력 파일 경로
    
    Returns:
        List[Dict[str, Any]]: 처리된 문서 청크들
    """
    print(f"\n📄 {law_name} 처리 시작...")
    
    # CustomsLawLoader로 문서 처리
    loader = CustomsLawLoader(law_data)
    processed_documents = loader.load()
    
    # 결과 분석
    print(f"\n📊 {law_name} 청킹 결과 분석:")
    analyze_chunking_results(processed_documents)
    
    # 데이터 무결성 검증
    integrity_issues = validate_chunk_integrity(processed_documents)
    if integrity_issues:
        print(f"\n⚠️ 데이터 무결성 문제 발견:")
        for issue in integrity_issues[:5]:  # 최대 5개만 출력
            print(f"  - {issue}")
        if len(integrity_issues) > 5:
            print(f"  ... 총 {len(integrity_issues)}개 문제 발견")
    else:
        print("✅ 데이터 무결성 검증 통과")
    
    # 결과 저장
    if output_path:
        success = save_processed_documents(processed_documents, str(output_path))
        if not success:
            logger.error(f"Failed to save {law_name} processed documents")
            return []
    
    print(f"✅ {law_name} 처리 완료: {len(processed_documents)}개 청크 생성")
    return processed_documents


def process_all_laws(show_samples: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """모든 법령 문서 처리
    
    Args:
        show_samples (bool): 샘플 청크 출력 여부
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: 법령별 처리된 문서들
    """
    print("🚀 전체 관세법 문서 처리 시작...")
    
    # 데이터 파일 경로 및 출력 경로 가져오기
    data_paths = get_law_data_paths()
    output_paths = get_output_paths()
    
    all_results = {}
    total_chunks = 0
    
    for law_name, data_path in data_paths.items():
        if not data_path.exists():
            print(f"⚠️ {law_name} 데이터 파일이 없습니다: {data_path}")
            continue
        
        # JSON 데이터 로드
        law_data = load_json_data(str(data_path))
        if law_data is None:
            print(f"❌ {law_name} 데이터 로드 실패")
            continue
        
        # 문서 처리
        output_path = output_paths.get(law_name)
        processed_docs = process_single_law(law_name, law_data, output_path)
        
        if processed_docs:
            all_results[law_name] = processed_docs
            total_chunks += len(processed_docs)
            
            # 샘플 출력 (요청시)
            if show_samples:
                print(f"\n📋 {law_name} 샘플 청크:")
                print_sample_chunks(processed_docs, num_samples=1)
    
    # 전체 결과 요약
    print(f"\n🎉 전체 처리 완료!")
    print(f"처리된 법령 수: {len(all_results)}")
    print(f"총 생성된 청크 수: {total_chunks}")
    
    # 법령별 청크 수 출력
    for law_name, docs in all_results.items():
        print(f"  - {law_name}: {len(docs)}개 청크")
    
    return all_results


def process_single_pdf(pdf_name: str, pdf_path: Path, output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """단일 PDF 문서 처리 (JSONL 방식)
    
    Args:
        pdf_name (str): PDF 문서명
        pdf_path (Path): PDF 파일 경로
        output_path (Optional[Path]): 출력 파일 경로 (.jsonl)
    
    Returns:
        List[Dict[str, Any]]: 처리된 문서 청크들
    """
    print(f"\n📄 {pdf_name} PDF 처리 시작...")
    
    # PDFDocumentProcessor로 문서 처리 및 JSONL 저장
    processor = PDFDocumentProcessor(pdf_path, pdf_name)
    
    if output_path:
        # 처리 후 바로 JSONL로 저장
        processed_documents, save_success = processor.process_and_save_jsonl(output_path)
        if not save_success:
            logger.error(f"Failed to save {pdf_name} processed documents to JSONL")
            return []
    else:
        # 저장 없이 처리만
        processed_documents = processor.process()
    
    if not processed_documents:
        print(f"❌ {pdf_name} PDF 처리 실패")
        return []
    
    # 결과 분석
    print(f"\n📊 {pdf_name} PDF 청킹 결과 분석:")
    analysis = analyze_pdf_processing_results(processed_documents)
    
    # 분석 결과 출력
    overview = analysis.get("overview", {})
    print(f"  총 청크 수: {overview.get('total_chunks', 0)}")
    print(f"  평균 청크 크기: {overview.get('average_chunk_size', 0)} 문자")
    print(f"  소스 문서 수: {len(overview.get('source_documents', []))}")
    
    # 문서 유형별 통계
    doc_types = analysis.get("document_types", {})
    if doc_types:
        print("  문서 유형별 청크 수:")
        for doc_type, stats in doc_types.items():
            print(f"    - {doc_type}: {stats.get('count', 0)}개")
    
    # PDF 청킹 검증
    validation_result = validate_pdf_chunks(processed_documents)
    if validation_result["is_valid"]:
        print("✅ PDF 청킹 검증 통과")
    else:
        print("⚠️ PDF 청킹 검증 문제 발견:")
        for issue in validation_result["issues"][:3]:  # 최대 3개만 출력
            print(f"  - {issue}")
        if len(validation_result["issues"]) > 3:
            print(f"  ... 총 {len(validation_result['issues'])}개 문제 발견")
    
    # 처리 요약 출력
    summary = processor.get_processing_summary()
    print(f"\n📋 {pdf_name} 처리 요약:")
    print(f"  문서 유형: {summary.get('document_type', '알 수 없음')}")
    print(f"  추출 방법: {list(summary.get('extraction_methods', {}).keys())}")
    print(f"  HS코드 발견: {summary.get('hs_codes_found', 0)}개")
    print(f"  법령 참조 발견: {summary.get('law_references_found', 0)}개")
    
    if output_path:
        print(f"💾 JSONL 파일 저장 완료: {output_path}")
    
    print(f"✅ {pdf_name} PDF 처리 완료: {len(processed_documents)}개 청크 생성")
    return processed_documents


def process_all_pdfs(show_samples: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """모든 PDF 문서 처리
    
    Args:
        show_samples (bool): 샘플 청크 출력 여부
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: PDF별 처리된 문서들
    """
    print("🚀 전체 PDF 문서 처리 시작...")
    
    # PDF 파일 경로 및 출력 경로 가져오기
    pdf_paths = get_pdf_data_paths()
    output_paths = get_pdf_output_paths()
    
    all_results = {}
    total_chunks = 0
    
    for pdf_name, pdf_path in pdf_paths.items():
        if not pdf_path.exists():
            print(f"⚠️ {pdf_name} PDF 파일이 없습니다: {pdf_path}")
            continue
        
        # PDF 문서 처리
        output_path = output_paths.get(pdf_name)
        processed_docs = process_single_pdf(pdf_name, pdf_path, output_path)
        
        if processed_docs:
            all_results[pdf_name] = processed_docs
            total_chunks += len(processed_docs)
            
            # 샘플 출력 (요청시)
            if show_samples:
                print(f"\n📋 {pdf_name} 샘플 청크:")
                # PDF 청크는 구조가 다르므로 간단히 출력
                for i, chunk in enumerate(processed_docs[:2]):  # 최대 2개
                    print(f"  청크 {i+1}:")
                    print(f"    인덱스: {chunk.get('index', 'N/A')}")
                    print(f"    제목: {chunk.get('title', 'N/A')}")
                    content = chunk.get('content', '')
                    print(f"    내용: {content[:100]}{'...' if len(content) > 100 else ''}")
                    print()
    
    # 전체 결과 요약
    print(f"\n🎉 전체 PDF 처리 완료!")
    print(f"처리된 PDF 수: {len(all_results)}")
    print(f"총 생성된 청크 수: {total_chunks}")
    
    # PDF별 청크 수 출력
    for pdf_name, docs in all_results.items():
        print(f"  - {pdf_name}: {len(docs)}개 청크")
    
    return all_results


def process_single_csv(csv_name: str, csv_path: Path, output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """단일 CSV 파일 처리 (일반 정보용)
    
    Args:
        csv_name (str): CSV 파일명
        csv_path (Path): CSV 파일 경로
        output_path (Optional[Path]): 출력 파일 경로
    
    Returns:
        List[Dict[str, Any]]: 처리된 문서 청크들
    """
    print(f"\n📄 {csv_name} CSV 처리 시작...")
    
    # CSVDocumentLoader로 문서 처리
    try:
        loader = CSVDocumentLoader(str(csv_path))
        processed_documents = loader.load()
    except Exception as e:
        print(f"❌ {csv_name} CSV 로딩 실패: {e}")
        return []
    
    if not processed_documents:
        print(f"❌ {csv_name} CSV 처리 결과가 없습니다.")
        return []
    
    # 결과 분석
    print(f"\n📊 {csv_name} CSV 청킹 결과 분석:")
    stats = loader.get_statistics()
    print(f"  총 청크 수: {stats.get('total_documents', 0)}")
    print(f"  평균 내용 길이: {stats.get('average_content_length', 0):.1f} 문자")
    print(f"  CSV 유형: {stats.get('csv_type', 'Unknown')}")
    
    # 카테고리 분포
    category_dist = stats.get('category_distribution', {})
    if category_dist:
        print("  카테고리 분포:")
        for category, count in category_dist.items():
            print(f"    - {category}: {count}개")
    
    # 결과 저장
    if output_path:
        success = save_processed_documents(processed_documents, str(output_path))
        if not success:
            logger.error(f"Failed to save {csv_name} processed documents")
            return []
    
    print(f"✅ {csv_name} CSV 처리 완료: {len(processed_documents)}개 청크 생성")
    return processed_documents


def process_all_csvs(show_samples: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """모든 CSV 파일 처리 (일반 정보용)
    
    Args:
        show_samples (bool): 샘플 청크 출력 여부
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: CSV별 처리된 문서들
    """
    print("🚀 전체 무역 정보 CSV 처리 시작...")
    
    # CSV 파일 경로 및 출력 경로 가져오기
    csv_paths = get_csv_data_paths()
    output_paths = get_csv_output_paths()
    
    all_results = {}
    total_chunks = 0
    
    for csv_name, csv_path in csv_paths.items():
        if not csv_path.exists():
            print(f"⚠️ {csv_name} CSV 파일이 없습니다: {csv_path}")
            continue
        
        # CSV 문서 처리
        output_path = output_paths.get(csv_name)
        processed_docs = process_single_csv(csv_name, csv_path, output_path)
        
        if processed_docs:
            all_results[csv_name] = processed_docs
            total_chunks += len(processed_docs)
            
            # 샘플 출력 (요청시)
            if show_samples:
                print(f"\n📋 {csv_name} 샘플 청크:")
                for i, chunk in enumerate(processed_docs[:2]):  # 최대 2개
                    print(f"  청크 {i+1}:")
                    print(f"    인덱스: {chunk.get('index', 'N/A')}")
                    print(f"    제목: {chunk.get('title', 'N/A')}")
                    content = chunk.get('content', '')
                    print(f"    내용: {content[:150]}{'...' if len(content) > 150 else ''}")
                    
                    # 메타데이터 정보
                    metadata = chunk.get('metadata', {})
                    if metadata.get('hs_code'):
                        print(f"    HS코드: {metadata.get('hs_code')}")
                    if metadata.get('country'):
                        print(f"    국가: {metadata.get('country')}")
                    if metadata.get('regulation_type'):
                        print(f"    규제유형: {metadata.get('regulation_type')}")
                    print()
    
    # 전체 결과 요약
    print(f"\n🎉 전체 CSV 처리 완료!")
    print(f"처리된 CSV 수: {len(all_results)}")
    print(f"총 생성된 청크 수: {total_chunks}")
    
    # CSV별 청크 수 출력
    for csv_name, docs in all_results.items():
        print(f"  - {csv_name}: {len(docs)}개 청크")
    
    return all_results


def process_consultation_cases(output_path: Optional[Path] = None, show_samples: bool = False) -> List[Dict[str, Any]]:
    """민원상담 사례집 PDF 처리 (JSON 형식, RAG 호환)
    
    Args:
        output_path (Optional[Path]): 출력 파일 경로
        show_samples (bool): 샘플 청크 출력 여부
    
    Returns:
        List[Dict[str, Any]]: 처리된 상담 사례 청크들
    """
    print("\n📄 민원상담 사례집 PDF 처리 시작...")
    
    # 상담 사례 파일 경로 가져오기
    consultation_paths = get_consultation_case_paths()
    input_pdf = consultation_paths["input_pdf"]
    
    if not input_pdf.exists():
        print(f"⚠️ 민원상담 사례집 PDF 파일이 없습니다: {input_pdf}")
        return []
    
    # 출력 경로 설정
    if not output_path:
        output_path = consultation_paths["output_json"]
    
    # PDFDocumentProcessor로 문서 처리 (JSON 방식 사용)
    processor = PDFDocumentProcessor(input_pdf, "관세행정_민원상담_사례집")
    
    # 처리 후 바로 JSON으로 저장 (RAG 호환)
    processed_documents, save_success = processor.process_and_save_json(output_path)
    
    if not processed_documents:
        print("❌ 민원상담 사례집 처리 실패")
        return []
    
    if not save_success:
        print("⚠️ JSON 파일 저장 실패")
    
    # 결과 분석
    print(f"\n📊 민원상담 사례집 청킹 결과 분석:")
    summary = processor.get_processing_summary()
    
    # 기본 통계
    print(f"  총 사례 수: {summary.get('total_chunks', 0)}")
    print(f"  평균 사례 크기: {summary.get('average_chunk_size', 0)} 문자")
    print(f"  문서 유형: {summary.get('document_type', '알 수 없음')}")
    
    # 카테고리별 통계
    categories = summary.get('categories', {})
    if categories:
        print("  카테고리별 사례 수:")
        for category, count in categories.items():
            print(f"    - {category}: {count}개")
    
    # 상담 유형별 통계
    consultation_types = summary.get('consultation_types', {})
    if consultation_types:
        print("  상담 유형별 사례 수:")
        for c_type, count in consultation_types.items():
            print(f"    - {c_type}: {count}개")
    
    # 내용 완성도
    completeness = summary.get('content_completeness', {})
    if completeness:
        print(f"  내용 완성도:")
        print(f"    - 질문 포함: {completeness.get('cases_with_questions', 0)}개")
        print(f"    - 답변 포함: {completeness.get('cases_with_answers', 0)}개")
        print(f"    - 법령 참조 포함: {completeness.get('cases_with_law_references', 0)}개")
        print(f"    - 완성도 비율: {completeness.get('completeness_rate', 0):.1%}")
    
    # 샘플 출력
    if show_samples and processed_documents:
        print(f"\n📋 민원상담 사례집 샘플 청크:")
        for i, chunk in enumerate(processed_documents[:2]):  # 최대 2개
            print(f"  사례 {i+1}:")
            print(f"    인덱스: {chunk.get('index', 'N/A')}")
            print(f"    제목: {chunk.get('title', 'N/A')}")
            content = chunk.get('content', '')
            print(f"    내용: {content[:200]}{'...' if len(content) > 200 else ''}")
            
            # 메타데이터 정보
            metadata = chunk.get('metadata', {})
            if metadata.get('category'):
                print(f"    카테고리: {metadata.get('category')}")
            if metadata.get('consultation_type'):
                print(f"    상담 유형: {metadata.get('consultation_type')}")
            if metadata.get('keywords'):
                keywords = metadata.get('keywords', [])[:5]  # 최대 5개
                print(f"    키워드: {', '.join(keywords)}")
            print()
    
    if save_success:
        print(f"💾 JSON 파일 저장 완료: {output_path}")
    
    print(f"✅ 민원상담 사례집 처리 완료: {len(processed_documents)}개 사례 생성")
    return processed_documents


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="관세법 문서, PDF, CSV 처리 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 법령 처리
  python scripts/process_documents.py --all                    # 모든 법령 처리
  python scripts/process_documents.py --law 관세법              # 특정 법령만 처리
  python scripts/process_documents.py --all --samples         # 샘플 출력 포함
  python scripts/process_documents.py --law 관세법 --output custom.json  # 커스텀 출력 파일
  
  # PDF 처리 (JSONL 형식)
  python scripts/process_documents.py --pdf-all               # 모든 PDF 처리
  python scripts/process_documents.py --pdf 수입제한품목       # 특정 PDF만 처리
  python scripts/process_documents.py --pdf-all --samples     # PDF 샘플 출력 포함
  python scripts/process_documents.py --pdf 수입제한품목 --output custom.jsonl  # 커스텀 JSONL 출력 파일
  
  # 민원상담 사례집 처리 (JSON 형식, RAG 호환)
  python scripts/process_documents.py --consultation          # 민원상담 사례집 처리
  python scripts/process_documents.py --consultation --samples # 상담사례 샘플 출력 포함
  python scripts/process_documents.py --consultation --output consultation_cases.json  # 커스텀 JSON 출력
  
  # CSV 처리 (일반 정보용)
  python scripts/process_documents.py --csv-all               # 모든 CSV 처리
  python scripts/process_documents.py --csv 수입규제DB_전체    # 특정 CSV만 처리
  python scripts/process_documents.py --csv-all --samples     # CSV 샘플 출력 포함
  python scripts/process_documents.py --csv 수출제한품목 --output custom.json  # 커스텀 JSON 출력 파일
        """
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="모든 관세법 문서 처리"
    )
    
    parser.add_argument(
        "--law",
        type=str,
        choices=["관세법", "관세법시행령", "관세법시행규칙"],
        help="처리할 특정 법령 선택"
    )
    
    parser.add_argument(
        "--pdf-all",
        action="store_true",
        help="모든 PDF 문서 처리"
    )
    
    parser.add_argument(
        "--pdf",
        type=str,
        choices=["수입제한품목", "수출제한품목", "수출금지품목", "무역통계부호", "수입신고서작성요령", "수출신고서작성요령"],
        help="처리할 특정 PDF 문서 선택"
    )
    
    parser.add_argument(
        "--consultation",
        action="store_true",
        help="민원상담 사례집 PDF 처리 (JSON 형식으로 저장, RAG 시스템 호환)"
    )
    
    parser.add_argument(
        "--csv-all",
        action="store_true",
        help="모든 CSV 파일 처리 (일반 정보용)"
    )
    
    parser.add_argument(
        "--csv",
        type=str,
        choices=["수입규제DB_전체", "수출제한품목", "수입제한품목", "수출금지품목", "동식물허용금지지역"],
        help="처리할 특정 CSV 파일 선택"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="출력 파일 경로 (특정 법령/PDF/CSV 처리시만 사용, PDF는 .jsonl, CSV는 .json 확장자 권장)"
    )
    
    parser.add_argument(
        "--samples",
        action="store_true",
        help="처리 결과 샘플 출력"
    )
    
    parser.add_argument(
        "--validate-env",
        action="store_true",
        help="환경 설정만 검증하고 종료"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        print("🔧 환경 설정 확인...")
        
        # 환경 변수 로드
        config = load_config()
        
        # 환경 검증
        if not validate_environment():
            print("❌ 환경 설정 검증 실패. 설정을 확인해주세요.")
            return 1
        
        # 환경 검증만 하고 종료
        if args.validate_env:
            print("✅ 환경 설정 검증 완료")
            return 0
        
        # 처리 옵션 확인
        if not any([args.all, args.law, args.pdf_all, args.pdf, args.consultation, args.csv_all, args.csv]):
            print("❌ 처리 옵션 중 하나를 선택해주세요: --all, --law, --pdf-all, --pdf, --consultation, --csv-all, --csv")
            parser.print_help()
            return 1
        
        # 동시 처리 방지
        law_options = args.all or args.law
        pdf_options = args.pdf_all or args.pdf
        consultation_options = args.consultation
        csv_options = args.csv_all or args.csv
        
        active_options = sum([bool(law_options), bool(pdf_options), bool(consultation_options), bool(csv_options)])
        if active_options > 1:
            print("❌ 법령, PDF, 민원상담, CSV 처리는 동시에 실행할 수 없습니다. 하나씩 처리해주세요.")
            return 1
        
        # 모든 법령 처리
        if args.all:
            results = process_all_laws(show_samples=args.samples)
            if not results:
                print("❌ 처리된 문서가 없습니다.")
                return 1
        
        # 특정 법령 처리
        elif args.law:
            data_paths = get_law_data_paths()
            output_paths = get_output_paths()
            
            data_path = data_paths[args.law]
            if not data_path.exists():
                print(f"❌ {args.law} 데이터 파일이 없습니다: {data_path}")
                return 1
            
            # 출력 경로 설정
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = output_paths[args.law]
            
            # JSON 데이터 로드
            law_data = load_json_data(str(data_path))
            if law_data is None:
                print(f"❌ {args.law} 데이터 로드 실패")
                return 1
            
            # 문서 처리
            processed_docs = process_single_law(args.law, law_data, output_path)
            if not processed_docs:
                print(f"❌ {args.law} 처리 실패")
                return 1
            
            # 샘플 출력
            if args.samples:
                print(f"\n📋 {args.law} 샘플 청크:")
                print_sample_chunks(processed_docs, num_samples=2)
        
        # 모든 PDF 처리
        elif args.pdf_all:
            results = process_all_pdfs(show_samples=args.samples)
            if not results:
                print("❌ 처리된 PDF 문서가 없습니다.")
                return 1
        
        # 특정 PDF 처리
        elif args.pdf:
            pdf_paths = get_pdf_data_paths()
            output_paths = get_pdf_output_paths()
            
            pdf_path = pdf_paths[args.pdf]
            if not pdf_path.exists():
                print(f"❌ {args.pdf} PDF 파일이 없습니다: {pdf_path}")
                return 1
            
            # 출력 경로 설정
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = output_paths[args.pdf]
            
            # PDF 문서 처리
            processed_docs = process_single_pdf(args.pdf, pdf_path, output_path)
            if not processed_docs:
                print(f"❌ {args.pdf} PDF 처리 실패")
                return 1
            
            # 샘플 출력
            if args.samples:
                print(f"\n📋 {args.pdf} 샘플 청크:")
                for i, chunk in enumerate(processed_docs[:2]):  # 최대 2개
                    print(f"  청크 {i+1}:")
                    print(f"    인덱스: {chunk.get('index', 'N/A')}")
                    print(f"    제목: {chunk.get('title', 'N/A')}")
                    content = chunk.get('content', '')
                    print(f"    내용: {content[:200]}{'...' if len(content) > 200 else ''}")
                    print()
        
        # 민원상담 사례집 처리
        elif args.consultation:
            # 출력 경로 설정
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = None  # 기본 경로 사용
            
            # 민원상담 사례집 처리
            processed_docs = process_consultation_cases(output_path, show_samples=args.samples)
            if not processed_docs:
                print("❌ 민원상담 사례집 처리 실패")
                return 1
        
        # 모든 CSV 처리
        elif args.csv_all:
            results = process_all_csvs(show_samples=args.samples)
            if not results:
                print("❌ 처리된 CSV 파일이 없습니다.")
                return 1
        
        # 특정 CSV 처리
        elif args.csv:
            csv_paths = get_csv_data_paths()
            output_paths = get_csv_output_paths()
            
            csv_path = csv_paths[args.csv]
            if not csv_path.exists():
                print(f"❌ {args.csv} CSV 파일이 없습니다: {csv_path}")
                return 1
            
            # 출력 경로 설정
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = output_paths[args.csv]
            
            # CSV 문서 처리
            processed_docs = process_single_csv(args.csv, csv_path, output_path)
            if not processed_docs:
                print(f"❌ {args.csv} CSV 처리 실패")
                return 1
            
            # 샘플 출력
            if args.samples:
                print(f"\n📋 {args.csv} 샘플 청크:")
                for i, chunk in enumerate(processed_docs[:2]):  # 최대 2개
                    print(f"  청크 {i+1}:")
                    print(f"    인덱스: {chunk.get('index', 'N/A')}")
                    print(f"    제목: {chunk.get('title', 'N/A')}")
                    content = chunk.get('content', '')
                    print(f"    내용: {content[:200]}{'...' if len(content) > 200 else ''}")
                    
                    # 메타데이터 정보
                    metadata = chunk.get('metadata', {})
                    if metadata.get('hs_code'):
                        print(f"    HS코드: {metadata.get('hs_code')}")
                    if metadata.get('country'):
                        print(f"    국가: {metadata.get('country')}")
                    if metadata.get('regulation_type'):
                        print(f"    규제유형: {metadata.get('regulation_type')}")
                    print()
        
        print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        return 1
    except Exception as e:
        logger.error(f"처리 중 오류 발생: {e}")
        print(f"❌ 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
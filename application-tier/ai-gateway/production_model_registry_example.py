"""
프로덕션 환경용 모델 레지스트리 구현 예시

현재 models.py의 인메모리 레지스트리를 데이터베이스 기반으로 
변경할 때 참고할 수 있는 구현 예시입니다.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from datetime import datetime
import json

from ..core.database import get_db_session  # 가상의 DB 연결
from ..schemas.models import ModelInfo, ModelType, ModelStatus

Base = declarative_base()

class ModelEntity(Base):
    """
    모델 정보 데이터베이스 엔티티
    
    프로덕션 환경에서 모델 서비스 정보를 저장하는 테이블입니다.
    각 모델의 메타데이터, 상태, 서비스 URL 등을 관리합니다.
    """
    __tablename__ = "model_registry"
    
    id: Mapped[str] = mapped_column(primary_key=True)  # model-ocr, model-report 등
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)  # ModelType enum value
    version: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)  # ModelStatus enum value
    description: Mapped[Optional[str]] = mapped_column()
    service_url: Mapped[str] = mapped_column(nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column()  # JSON string
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class DatabaseModelRegistry:
    """
    데이터베이스 기반 모델 레지스트리
    
    프로덕션 환경에서 사용할 모델 레지스트리 클래스입니다.
    데이터베이스에서 모델 정보를 동적으로 조회하고 관리합니다.
    """
    
    @staticmethod
    async def get_all_models() -> Dict[str, ModelInfo]:
        """
        모든 활성 모델 조회
        
        데이터베이스에서 READY 상태인 모든 모델을 조회하여
        모델 레지스트리 딕셔너리로 반환합니다.
        
        Returns:
            Dict[str, ModelInfo]: 모델 ID를 키로 하는 모델 정보 딕셔너리
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(ModelEntity).where(ModelEntity.status == ModelStatus.READY)
            )
            models = result.scalars().all()
            
            model_registry = {}
            for model_entity in models:
                # 메타데이터 JSON 파싱
                metadata = {}
                if model_entity.metadata_json:
                    try:
                        metadata = json.loads(model_entity.metadata_json)
                    except json.JSONDecodeError:
                        metadata = {}
                
                # ModelInfo 객체 생성
                model_info = ModelInfo(
                    id=model_entity.id,
                    name=model_entity.name,
                    type=ModelType(model_entity.type),
                    version=model_entity.version,
                    status=ModelStatus(model_entity.status),
                    description=model_entity.description,
                    created_at=model_entity.created_at,
                    updated_at=model_entity.updated_at,
                    metadata=metadata
                )
                
                model_registry[model_entity.id] = model_info
            
            return model_registry
    
    @staticmethod
    async def get_model_by_id(model_id: str) -> Optional[ModelInfo]:
        """
        특정 모델 조회
        
        Args:
            model_id: 조회할 모델 ID
            
        Returns:
            Optional[ModelInfo]: 모델 정보 또는 None
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(ModelEntity).where(ModelEntity.id == model_id)
            )
            model_entity = result.scalar_one_or_none()
            
            if not model_entity:
                return None
            
            metadata = {}
            if model_entity.metadata_json:
                try:
                    metadata = json.loads(model_entity.metadata_json)
                except json.JSONDecodeError:
                    metadata = {}
            
            return ModelInfo(
                id=model_entity.id,
                name=model_entity.name,
                type=ModelType(model_entity.type),
                version=model_entity.version,
                status=ModelStatus(model_entity.status),
                description=model_entity.description,
                created_at=model_entity.created_at,
                updated_at=model_entity.updated_at,
                metadata=metadata
            )
    
    @staticmethod
    async def register_model(model_info: ModelInfo) -> bool:
        """
        새 모델 등록
        
        Args:
            model_info: 등록할 모델 정보
            
        Returns:
            bool: 등록 성공 여부
        """
        async with get_db_session() as session:
            try:
                # 메타데이터를 JSON 문자열로 변환
                metadata_json = json.dumps(model_info.metadata) if model_info.metadata else None
                
                # 새 모델 엔티티 생성
                new_model = ModelEntity(
                    id=model_info.id,
                    name=model_info.name,
                    type=model_info.type.value,
                    version=model_info.version,
                    status=model_info.status.value,
                    description=model_info.description,
                    service_url=model_info.metadata.get("service_url", ""),
                    metadata_json=metadata_json
                )
                
                session.add(new_model)
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                print(f"모델 등록 실패: {e}")
                return False
    
    @staticmethod
    async def update_model_status(model_id: str, status: ModelStatus) -> bool:
        """
        모델 상태 업데이트
        
        Health check 결과에 따라 모델 상태를 업데이트합니다.
        
        Args:
            model_id: 모델 ID
            status: 새로운 상태
            
        Returns:
            bool: 업데이트 성공 여부
        """
        async with get_db_session() as session:
            try:
                await session.execute(
                    update(ModelEntity)
                    .where(ModelEntity.id == model_id)
                    .values(
                        status=status.value,
                        updated_at=datetime.now()
                    )
                )
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                print(f"모델 상태 업데이트 실패: {e}")
                return False


# models.py에서 사용할 수 있도록 함수로 래핑
async def get_model_registry() -> Dict[str, ModelInfo]:
    """
    프로덕션용 모델 레지스트리 조회
    
    현재 models.py의 인메모리 딕셔너리를 이 함수로 대체하면
    데이터베이스 기반 동적 모델 관리가 가능합니다.
    """
    return await DatabaseModelRegistry.get_all_models()


async def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """
    프로덕션용 개별 모델 조회
    
    현재 models.py의 딕셔너리 접근을 이 함수로 대체하면
    데이터베이스에서 실시간 모델 정보를 조회할 수 있습니다.
    """
    return await DatabaseModelRegistry.get_model_by_id(model_id)


# 초기 데이터 마이그레이션 예시
INITIAL_MODELS = [
    {
        "id": "model-ocr",
        "name": "Azure Document Intelligence OCR",
        "type": "text_extractor",
        "version": "1.0.0",
        "status": "ready",
        "description": "Azure Document Intelligence를 사용한 관세 문서 OCR 처리",
        "service_url": "http://localhost:8001",
        "metadata": {
            "endpoint": "/ocr/",
            "supported_documents": ["invoice", "packing_list", "bill_of_lading"],
            "supported_formats": ["pdf", "jpg", "png", "tiff"],
            "max_file_size": "50MB",
            "processing_time": "2-5 seconds",
            "accuracy": 0.95
        }
    },
    {
        "id": "model-report", 
        "name": "LangChain 관세신고서 생성",
        "type": "text_generator",
        "version": "1.0.0", 
        "status": "ready",
        "description": "LangChain과 OpenAI GPT를 사용한 한국 관세청 규정 기반 수입/수출 신고서 자동 생성",
        "service_url": "http://localhost:8002",
        "metadata": {
            "endpoints": {
                "import": "/generate-customs-declaration/import",
                "export": "/generate-customs-declaration/export"
            },
            "supported_types": ["import_declaration", "export_declaration"],
            "llm_model": "gpt-4o-mini",
            "temperature": 0.3,
            "processing_time": "3-8 seconds",
            "language": "Korean"
        }
    }
]

async def migrate_initial_data():
    """
    초기 모델 데이터 마이그레이션
    
    현재 하드코딩된 모델 정보를 데이터베이스로 이관합니다.
    """
    for model_data in INITIAL_MODELS:
        model_info = ModelInfo(
            id=model_data["id"],
            name=model_data["name"], 
            type=ModelType(model_data["type"]),
            version=model_data["version"],
            status=ModelStatus(model_data["status"]),
            description=model_data["description"],
            metadata=model_data["metadata"]
        )
        
        success = await DatabaseModelRegistry.register_model(model_info)
        print(f"모델 {model_data['id']} 마이그레이션: {'성공' if success else '실패'}")
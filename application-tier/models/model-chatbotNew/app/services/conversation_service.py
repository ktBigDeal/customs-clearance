"""
대화 관리 서비스

PostgreSQL 데이터베이스를 사용하여 대화방과 메시지를 관리하는 서비스입니다.
사용자별 대화 이력 저장, 조회, 삭제 및 검색 기능을 제공합니다.

주요 기능:
- 대화방 생성 및 관리
- 메시지 저장 및 조회
- 대화 이력 검색
- 사용자별 대화 목록 관리
- 대화 컨텍스트 캐싱
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.redis_client import redis_manager
from app.core.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
    DatabaseError,
    handle_exceptions
)
from app.models.conversation import Conversation, Message
from app.models.user_session import UserSession

logger = logging.getLogger(__name__)


class ConversationService:
    """대화 관리 서비스 클래스
    
    대화방과 메시지의 CRUD 작업을 처리하고,
    Redis 캐싱을 통해 성능을 최적화합니다.
    """
    
    @handle_exceptions("대화방 생성")
    async def create_conversation(
        self, 
        user_id: int, 
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """새 대화방 생성
        
        Args:
            user_id (int): 사용자 ID
            title (Optional[str]): 대화방 제목 (None이면 자동 생성)
            metadata (Optional[Dict[str, Any]]): 추가 메타데이터
            
        Returns:
            Conversation: 생성된 대화방
        """
        async with get_db_session() as session:
            conversation = Conversation(
                user_id=user_id,
                title=title or "새 대화",
                metadata=metadata or {}
            )
            
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            
            logger.info(f"✅ 대화방 생성 완료 - ID: {conversation.id}, 사용자: {user_id}")
            return conversation
    
    @handle_exceptions("사용자 대화방 목록 조회")
    async def get_user_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        include_inactive: bool = False
    ) -> Tuple[List[Conversation], int]:
        """사용자의 대화방 목록 조회
        
        Args:
            user_id (int): 사용자 ID
            limit (int): 조회할 대화방 수
            offset (int): 시작 위치
            include_inactive (bool): 비활성 대화방 포함 여부
            
        Returns:
            Tuple[List[Conversation], int]: (대화방 목록, 총 개수)
        """
        async with get_db_session() as session:
            # 조건 구성
            conditions = [Conversation.user_id == user_id]
            if not include_inactive:
                conditions.append(Conversation.is_active == True)
            
            # 총 개수 조회
            count_stmt = select(func.count(Conversation.id)).where(and_(*conditions))
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # 대화방 목록 조회 (최신순)
            stmt = (
                select(Conversation)
                .where(and_(*conditions))
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(stmt)
            conversations = result.scalars().all()
            
            logger.info(f"✅ 사용자 대화방 목록 조회 - 사용자: {user_id}, 개수: {len(conversations)}/{total_count}")
            return list(conversations), total_count
    
    @handle_exceptions("대화방 조회")
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[int] = None,
        include_messages: bool = True
    ) -> Conversation:
        """대화방 조회
        
        Args:
            conversation_id (str): 대화방 ID
            user_id (Optional[int]): 사용자 ID (권한 확인용)
            include_messages (bool): 메시지 포함 여부
            
        Returns:
            Conversation: 대화방 정보
            
        Raises:
            ConversationNotFoundError: 대화방을 찾을 수 없는 경우
        """
        async with get_db_session() as session:
            # 쿼리 구성
            stmt = select(Conversation).where(Conversation.id == conversation_id)
            
            if user_id is not None:
                stmt = stmt.where(Conversation.user_id == user_id)
            
            if include_messages:
                stmt = stmt.options(selectinload(Conversation.messages))
            
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise ConversationNotFoundError(conversation_id)
            
            logger.info(f"✅ 대화방 조회 완료 - ID: {conversation_id}")
            return conversation
    
    @handle_exceptions("대화방 업데이트")
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: int,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """대화방 정보 업데이트
        
        Args:
            conversation_id (str): 대화방 ID
            user_id (int): 사용자 ID
            title (Optional[str]): 새 제목
            metadata (Optional[Dict[str, Any]]): 새 메타데이터
            
        Returns:
            Conversation: 업데이트된 대화방
        """
        conversation = await self.get_conversation(conversation_id, user_id, include_messages=False)
        
        async with get_db_session() as session:
            # 변경사항 적용
            update_data = {}
            if title is not None:
                update_data[Conversation.title] = title
            if metadata is not None:
                update_data[Conversation.metadata] = metadata
            
            if update_data:
                stmt = (
                    update(Conversation)
                    .where(and_(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    ))
                    .values(**update_data)
                )
                await session.execute(stmt)
                await session.commit()
            
            # 업데이트된 대화방 반환
            updated_conversation = await self.get_conversation(conversation_id, user_id, include_messages=False)
            logger.info(f"✅ 대화방 업데이트 완료 - ID: {conversation_id}")
            return updated_conversation
    
    @handle_exceptions("대화방 삭제")
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: int,
        soft_delete: bool = True
    ) -> bool:
        """대화방 삭제 (소프트 삭제 또는 하드 삭제)
        
        Args:
            conversation_id (str): 대화방 ID
            user_id (int): 사용자 ID
            soft_delete (bool): 소프트 삭제 여부
            
        Returns:
            bool: 삭제 성공 여부
        """
        # 권한 확인
        await self.get_conversation(conversation_id, user_id, include_messages=False)
        
        async with get_db_session() as session:
            if soft_delete:
                # 소프트 삭제 (is_active = False)
                stmt = (
                    update(Conversation)
                    .where(and_(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    ))
                    .values(is_active=False)
                )
                await session.execute(stmt)
            else:
                # 하드 삭제 (실제 레코드 삭제)
                stmt = delete(Conversation).where(and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                ))
                await session.execute(stmt)
            
            await session.commit()
            
            # 캐시에서도 삭제
            await redis_manager.delete_conversation_context(conversation_id)
            
            delete_type = "소프트" if soft_delete else "하드"
            logger.info(f"✅ 대화방 {delete_type} 삭제 완료 - ID: {conversation_id}")
            return True
    
    @handle_exceptions("메시지 추가")
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_type: Optional[str] = None,
        processing_time: Optional[float] = None,
        token_usage: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """대화방에 메시지 추가
        
        Args:
            conversation_id (str): 대화방 ID
            role (str): 메시지 역할 (user/assistant/system)
            content (str): 메시지 내용
            agent_type (Optional[str]): 에이전트 유형
            processing_time (Optional[float]): 처리 시간
            token_usage (Optional[Dict[str, Any]]): 토큰 사용량
            metadata (Optional[Dict[str, Any]]): 메타데이터
            
        Returns:
            Message: 생성된 메시지
        """
        async with get_db_session() as session:
            # 메시지 생성
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                agent_type=agent_type,
                processing_time=processing_time,
                token_usage=token_usage,
                metadata=metadata
            )
            
            session.add(message)
            
            # 대화방 통계 업데이트
            conversation_stmt = select(Conversation).where(Conversation.id == conversation_id)
            conversation_result = await session.execute(conversation_stmt)
            conversation = conversation_result.scalar_one_or_none()
            
            if conversation:
                conversation.message_count += 1
                conversation.last_message_at = message.created_at
                
                # 첫 번째 사용자 메시지인 경우 제목 자동 생성
                if role == "user" and conversation.message_count == 1 and conversation.title == "새 대화":
                    conversation.title = Conversation.generate_title(content)
            
            await session.commit()
            await session.refresh(message)
            
            # 대화 컨텍스트 캐시 무효화
            await redis_manager.delete(conversation_id, prefix="context")
            
            logger.info(f"✅ 메시지 추가 완료 - 대화: {conversation_id}, 역할: {role}")
            return message
    
    @handle_exceptions("대화 이력 조회")
    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """대화 이력 조회
        
        Args:
            conversation_id (str): 대화방 ID
            user_id (Optional[int]): 사용자 ID (권한 확인용)
            limit (Optional[int]): 조회할 메시지 수
            offset (int): 시작 위치
            
        Returns:
            List[Message]: 메시지 목록
        """
        # 권한 확인
        if user_id is not None:
            await self.get_conversation(conversation_id, user_id, include_messages=False)
        
        # 캐시에서 확인
        cache_key = f"{conversation_id}:messages:{limit}:{offset}"
        cached_messages = await redis_manager.get_conversation_context(cache_key)
        if cached_messages:
            logger.info(f"✅ 캐시된 메시지 반환 - 대화: {conversation_id}")
            return [Message(**msg) for msg in cached_messages]
        
        async with get_db_session() as session:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
            
            if limit is not None:
                stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            # 캐시에 저장
            message_dicts = [msg.to_dict() for msg in messages]
            await redis_manager.set_conversation_context(cache_key, message_dicts, ttl=1800)
            
            logger.info(f"✅ 대화 이력 조회 완료 - 대화: {conversation_id}, 메시지: {len(messages)}개")
            return list(messages)
    
    @handle_exceptions("대화 검색")
    async def search_conversations(
        self,
        user_id: int,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """대화 검색 (제목 및 메시지 내용 검색)
        
        Args:
            user_id (int): 사용자 ID
            query (str): 검색 쿼리
            limit (int): 결과 수 제한
            offset (int): 시작 위치
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: (검색 결과, 총 개수)
        """
        async with get_db_session() as session:
            search_term = f"%{query}%"
            
            # 대화방 제목 검색 + 메시지 내용 검색
            conversation_search = (
                select(Conversation)
                .where(and_(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True,
                    Conversation.title.ilike(search_term)
                ))
            )
            
            message_search = (
                select(Conversation)
                .join(Message)
                .where(and_(
                    Conversation.user_id == user_id,
                    Conversation.is_active == True,
                    Message.content.ilike(search_term)
                ))
                .distinct()
            )
            
            # 두 검색 결과 통합
            union_stmt = conversation_search.union(message_search)
            
            # 총 개수 조회
            count_stmt = select(func.count()).select_from(union_stmt.subquery())
            count_result = await session.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # 결과 조회 (최신순)
            final_stmt = (
                union_stmt
                .order_by(desc(Conversation.updated_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(final_stmt)
            conversations = result.scalars().all()
            
            # 검색 결과 포맷팅
            search_results = []
            for conv in conversations:
                search_results.append({
                    **conv.to_dict(),
                    "match_type": "title" if query.lower() in conv.title.lower() else "content"
                })
            
            logger.info(f"✅ 대화 검색 완료 - 사용자: {user_id}, 쿼리: '{query}', 결과: {len(search_results)}개")
            return search_results, total_count
    
    @handle_exceptions("대화 통계 조회")
    async def get_user_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """사용자 대화 통계 조회
        
        Args:
            user_id (int): 사용자 ID
            
        Returns:
            Dict[str, Any]: 대화 통계 정보
        """
        async with get_db_session() as session:
            # 기본 통계
            stats_stmt = (
                select(
                    func.count(Conversation.id).label("total_conversations"),
                    func.count(Conversation.id).filter(Conversation.is_active == True).label("active_conversations"),
                    func.sum(Conversation.message_count).label("total_messages"),
                    func.max(Conversation.created_at).label("latest_conversation"),
                    func.min(Conversation.created_at).label("first_conversation")
                )
                .where(Conversation.user_id == user_id)
            )
            
            stats_result = await session.execute(stats_stmt)
            stats = stats_result.first()
            
            # 최근 30일 통계
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_stmt = (
                select(func.count(Conversation.id))
                .where(and_(
                    Conversation.user_id == user_id,
                    Conversation.created_at >= thirty_days_ago
                ))
            )
            
            recent_result = await session.execute(recent_stmt)
            recent_count = recent_result.scalar() or 0
            
            return {
                "total_conversations": stats.total_conversations or 0,
                "active_conversations": stats.active_conversations or 0,
                "total_messages": stats.total_messages or 0,
                "recent_conversations_30d": recent_count,
                "first_conversation_date": stats.first_conversation.isoformat() if stats.first_conversation else None,
                "latest_conversation_date": stats.latest_conversation.isoformat() if stats.latest_conversation else None
            }
    
    @handle_exceptions("대화 내보내기")
    async def export_conversation(
        self,
        conversation_id: str,
        user_id: int,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """대화 내보내기
        
        Args:
            conversation_id (str): 대화방 ID
            user_id (int): 사용자 ID
            format_type (str): 내보내기 형식 (json/text)
            
        Returns:
            Dict[str, Any]: 내보내기 데이터
        """
        conversation = await self.get_conversation(conversation_id, user_id, include_messages=True)
        
        export_data = {
            "conversation": conversation.to_dict(),
            "messages": [msg.to_dict() for msg in conversation.messages],
            "exported_at": datetime.now().isoformat(),
            "format": format_type,
            "total_messages": len(conversation.messages)
        }
        
        if format_type == "text":
            # 텍스트 형식으로 변환
            text_content = f"대화방: {conversation.title}\n"
            text_content += f"생성일: {conversation.created_at}\n"
            text_content += f"메시지 수: {len(conversation.messages)}\n\n"
            
            for msg in conversation.messages:
                sender = "사용자" if msg.role == "user" else "AI"
                text_content += f"[{msg.created_at}] {sender}: {msg.content}\n\n"
            
            export_data["text_content"] = text_content
        
        logger.info(f"✅ 대화 내보내기 완료 - ID: {conversation_id}, 형식: {format_type}")
        return export_data


# 전역 대화 서비스 인스턴스
conversation_service = ConversationService()
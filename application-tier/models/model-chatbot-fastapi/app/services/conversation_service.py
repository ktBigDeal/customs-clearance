"""
대화기록 연속성 서비스 구현
기존 LangGraph 오케스트레이터와 PostgreSQL 기반 대화기록의 통합
"""

import json
import asyncio
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.orm import selectinload
import redis.asyncio as redis

from ..models.conversation import (
    ConversationORM, MessageORM, MessageRole, AgentType,
    ConversationCreate, ConversationDetail, ConversationSummary,
    MessageCreate, MessageResponse, ConversationListResponse,
    ConversationSearchRequest, ConversationSearchResponse,
    RoutingInfo, MessageReference, ConversationUtils, ConversationValidator
)
from ..core.database import DatabaseManager, get_database_manager


logger = logging.getLogger(__name__)


class ConversationService:
    """
    대화기록 연속성 관리 서비스
    기존 LangGraph 오케스트레이터와 완전 통합
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.redis = None
        
        # 캐시 설정
        self.cache_ttl = 3600 * 24  # 24시간
        self.session_cache_ttl = 3600 * 2  # 2시간 (활성 세션)
        
        # 성능 설정
        self.max_context_messages = 20  # 컨텍스트로 사용할 최대 메시지 수
        self.context_cache_ttl = 3600  # 컨텍스트 캐시 1시간
    
    async def initialize(self):
        """서비스 초기화"""
        self.redis = await self.db_manager.get_redis()
        logger.info("ConversationService initialized")
    
    async def create_conversation(self, user_id: int, initial_message: Optional[str] = None) -> ConversationDetail:
        """
        새 대화 세션 생성
        
        Args:
            user_id: 사용자 ID (presentation-tier/backend에서 관리)
            initial_message: 첫 메시지 (선택적)
            
        Returns:
            ConversationDetail: 생성된 대화 세션 정보
        """
        conversation_id = ConversationUtils.generate_conversation_id()
        
        # 제목 생성
        if initial_message:
            title = ConversationUtils.generate_conversation_title(initial_message)
        else:
            title = f"새 대화 - {datetime.now().strftime('%m/%d %H:%M')}"
        
        # 데이터베이스에 저장
        async with self.db_manager.get_db_session() as session:
            conversation = ConversationORM(
                id=conversation_id,
                user_id=user_id,
                title=title,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_count=0,
                is_active=True,
                extra_metadata={}
            )
            
            session.add(conversation)
            await session.commit()
            
            # 관계 로드
            await session.refresh(conversation, ['messages'])
            
            logger.info(f"✅ Created conversation {conversation_id} for user {user_id}")
            
            # 캐시에 저장
            await self._cache_conversation(conversation)
            
            return ConversationDetail(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                message_count=conversation.message_count,
                last_agent_used=conversation.last_agent_used,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                is_active=conversation.is_active,
                extra_metadata=conversation.extra_metadata,
                recent_messages=[]
            )
    
    async def add_message_with_langgraph_integration(
        self,
        conversation_id: str,
        user_message: str,
        user_id: int,
        langgraph_orchestrator,
        include_history: bool = True
    ) -> Tuple[MessageResponse, MessageResponse]:
        """
        LangGraph 오케스트레이터와 통합된 메시지 처리
        
        Args:
            conversation_id: 대화 세션 ID
            user_message: 사용자 메시지
            user_id: 사용자 ID
            langgraph_orchestrator: LangGraph 오케스트레이터 인스턴스
            include_history: 이전 대화 컨텍스트 포함 여부
            
        Returns:
            Tuple[MessageResponse, MessageResponse]: (사용자 메시지, AI 응답)
        """
        try:
            # 1. 대화 세션 검증 및 로드
            conversation = await self._get_conversation_with_validation(conversation_id, user_id)
            
            # 2. 사용자 메시지 저장
            user_msg = await self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=user_message,
                user_id=user_id
            )
            
            # 3. 대화 컨텍스트 구성 (이전 메시지 포함)
            context_messages = []
            if include_history:
                context_messages = await self.get_conversation_context(conversation_id, limit=self.max_context_messages)
            
            # 4. LangGraph 오케스트레이터 실행
            try:
                # 컨텍스트가 있으면 포함해서 전달
                enhanced_input = self._prepare_langgraph_input(user_message, context_messages)
                
                logger.info(f"🧠 Executing LangGraph for conversation {conversation_id}")
                result = langgraph_orchestrator.invoke(enhanced_input)
                
                # 5. LangGraph 결과 파싱
                ai_response, routing_info, references = self._parse_langgraph_result(result)
                
                # 6. AI 응답 메시지 저장
                assistant_msg = await self.add_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=ai_response,
                    user_id=user_id,
                    agent_used=routing_info.get('selected_agent') if routing_info else None,
                    routing_info=routing_info,
                    references=references
                )
                
                # 7. 대화 세션 통계 업데이트
                await self._update_conversation_stats(conversation_id, routing_info)
                
                logger.info(f"✅ LangGraph integration completed for conversation {conversation_id}")
                
                return user_msg, assistant_msg
                
            except Exception as e:
                logger.error(f"❌ LangGraph execution failed: {e}")
                
                # 오류 응답 저장
                error_msg = await self.add_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                    user_id=user_id,
                    extra_metadata={"error": True, "error_message": str(e)}
                )
                
                return user_msg, error_msg
                
        except Exception as e:
            logger.error(f"❌ Message processing failed for conversation {conversation_id}: {e}")
            raise
    
    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        user_id: int,
        agent_used: Optional[str] = None,
        routing_info: Optional[Dict] = None,
        references: Optional[List[Dict]] = None,
        extra_metadata: Optional[Dict] = None
    ) -> MessageResponse:
        """개별 메시지 추가"""
        
        # 입력 검증
        if not ConversationValidator.validate_message_content(content):
            raise ValueError("Invalid message content")
        
        message_id = ConversationUtils.generate_message_id()
        
        async with self.db_manager.get_db_session() as session:
            # 대화 세션 검증
            conversation = await session.get(ConversationORM, conversation_id)
            if not conversation or not ConversationValidator.validate_user_permission(user_id, conversation):
                raise ValueError("Invalid conversation or permission denied")
            
            # 메시지 생성
            message = MessageORM(
                id=message_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                agent_used=agent_used,
                routing_info=routing_info or {},
                references=references or [],
                timestamp=datetime.now(),
                extra_metadata=extra_metadata or {}
            )
            
            session.add(message)
            
            # 대화 세션 통계 업데이트
            conversation.message_count += 1
            conversation.updated_at = datetime.now()
            if agent_used:
                conversation.last_agent_used = agent_used
            
            await session.commit()
            
            # 캐시 업데이트
            await self._cache_message(message)
            await self._invalidate_conversation_cache(conversation_id)
            
            return MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                agent_used=message.agent_used,
                routing_info=RoutingInfo(**message.routing_info) if message.routing_info else None,
                references=[MessageReference(**ref) for ref in message.references],
                timestamp=message.timestamp,
                extra_metadata=message.extra_metadata
            )
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[MessageResponse]:
        """대화 기록 조회 (캐싱 적용)"""
        
        # 캐시에서 조회 시도
        cache_key = f"history:{conversation_id}:{limit}:{offset}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            try:
                messages_data = json.loads(cached)
                return [MessageResponse(**msg) for msg in messages_data]
            except Exception as e:
                logger.warning(f"Cache parse error: {e}")
        
        # 데이터베이스에서 조회
        async with self.db_manager.get_db_session() as session:
            # 권한 검증
            conversation = await session.get(ConversationORM, conversation_id)
            if not conversation or not ConversationValidator.validate_user_permission(user_id, conversation):
                raise ValueError("Invalid conversation or permission denied")
            
            # 메시지 조회 (시간순 정렬 - 오래된 것부터)
            query = (
                select(MessageORM)
                .where(MessageORM.conversation_id == conversation_id)
                .order_by(MessageORM.timestamp.asc())  # 시간순 정렬로 변경
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            # 응답 구성
            response_messages = []
            for message in messages:
                msg_response = MessageResponse(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    role=message.role,
                    content=message.content,
                    agent_used=message.agent_used,
                    routing_info=RoutingInfo(**message.routing_info) if message.routing_info else None,
                    references=[MessageReference(**ref) for ref in message.references],
                    timestamp=message.timestamp,
                    extra_metadata=message.extra_metadata
                )
                response_messages.append(msg_response)
            
            # 캐시에 저장
            cache_data = [msg.dict() for msg in response_messages]
            await self.redis.setex(cache_key, self.cache_ttl, json.dumps(cache_data, default=str))
            
            return response_messages
    
    async def get_conversation_context(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        LangGraph용 대화 컨텍스트 구성
        최근 메시지를 LangGraph가 이해할 수 있는 형태로 변환
        """
        cache_key = f"context:{conversation_id}:{limit}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                pass
        
        # 최근 메시지 조회 (시간순 정렬)
        async with self.db_manager.get_db_session() as session:
            query = (
                select(MessageORM)
                .where(MessageORM.conversation_id == conversation_id)
                .order_by(MessageORM.timestamp.asc())  # 시간순 (오래된 것부터)
                .limit(limit)
            )
            
            result = await session.execute(query)
            messages = result.scalars().all()
            
            # LangGraph 호환 형태로 변환
            context = []
            for message in messages:
                context.append({
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "agent_used": message.agent_used
                })
            
            # 캐시 저장
            await self.redis.setex(cache_key, self.context_cache_ttl, json.dumps(context, default=str))
            
            return context
    
    async def get_user_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> ConversationListResponse:
        """사용자 대화 목록 조회"""
        
        async with self.db_manager.get_db_session() as session:
            # 전체 개수 조회
            count_query = select(func.count(ConversationORM.id)).where(
                and_(ConversationORM.user_id == user_id, ConversationORM.is_active == True)
            )
            total_result = await session.execute(count_query)
            total_count = total_result.scalar()
            
            # 대화 목록 조회
            query = (
                select(ConversationORM)
                .where(and_(ConversationORM.user_id == user_id, ConversationORM.is_active == True))
                .order_by(desc(ConversationORM.updated_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await session.execute(query)
            conversations = result.scalars().all()
            
            # 응답 구성
            conversation_summaries = [
                ConversationSummary(
                    id=conv.id,
                    title=conv.title,
                    message_count=conv.message_count,
                    last_agent_used=conv.last_agent_used,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    is_active=conv.is_active
                )
                for conv in conversations
            ]
            
            return ConversationListResponse(
                conversations=conversation_summaries,
                total_count=total_count,
                page=offset // limit + 1,
                page_size=limit,
                has_next=offset + limit < total_count
            )
    
    async def search_conversations(self, request: ConversationSearchRequest) -> ConversationSearchResponse:
        """대화 전문검색 (PostgreSQL GIN 인덱스 활용)"""
        
        async with self.db_manager.get_pg_connection() as conn:
            # PostgreSQL 전문검색 쿼리
            search_query = """
            SELECT DISTINCT c.id, c.title, c.message_count, c.last_agent_used, 
                   c.created_at, c.updated_at, c.is_active,
                   ts_rank(to_tsvector('korean', m.content), plainto_tsquery('korean', $1)) as rank
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE to_tsvector('korean', m.content) @@ plainto_tsquery('korean', $1)
            """
            
            params = [request.query]
            param_count = 1
            
            # 필터 조건 추가
            if request.user_id:
                param_count += 1
                search_query += f" AND c.user_id = ${param_count}"
                params.append(request.user_id)
            
            if request.agent_type:
                param_count += 1
                search_query += f" AND m.agent_used = ${param_count}"
                params.append(request.agent_type.value)
            
            if request.start_date:
                param_count += 1
                search_query += f" AND m.timestamp >= ${param_count}"
                params.append(request.start_date)
            
            if request.end_date:
                param_count += 1
                search_query += f" AND m.timestamp <= ${param_count}"
                params.append(request.end_date)
            
            search_query += f" ORDER BY rank DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([request.limit, request.offset])
            
            rows = await conn.fetch(search_query, *params)
            
            conversations = [
                ConversationSummary(
                    id=row['id'],
                    title=row['title'],
                    message_count=row['message_count'],
                    last_agent_used=row['last_agent_used'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    is_active=row['is_active']
                )
                for row in rows
            ]
            
            return ConversationSearchResponse(
                conversations=conversations,
                messages=[],  # 필요시 메시지도 포함 가능
                total_count=len(conversations),
                search_query=request.query
            )
    
    # 내부 유틸리티 메서드들
    async def _get_conversation_with_validation(self, conversation_id: str, user_id: int) -> ConversationORM:
        """대화 세션 로드 및 권한 검증"""
        async with self.db_manager.get_db_session() as session:
            conversation = await session.get(ConversationORM, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            if not ConversationValidator.validate_user_permission(user_id, conversation):
                raise ValueError("Permission denied")
            
            return conversation
    
    def _prepare_langgraph_input(self, current_message: str, context_messages: List[Dict]) -> str:
        """LangGraph 입력 준비 (컨텍스트 포함)"""
        if not context_messages:
            return current_message
        
        # 간단한 컨텍스트 형식
        context_str = ""
        for msg in context_messages[-5:]:  # 최근 5개 메시지만
            role = "사용자" if msg["role"] == "user" else "AI"
            context_str += f"{role}: {msg['content'][:100]}...\n"
        
        return f"[이전 대화]\n{context_str}\n[현재 질문]\n{current_message}"
    
    def _parse_langgraph_result(self, result: Dict[str, Any]) -> Tuple[str, Optional[Dict], List[Dict]]:
        """LangGraph 결과 파싱"""
        
        # 메시지 추출
        messages = result.get("messages", [])
        ai_response = ""
        if messages:
            last_message = messages[-1]
            ai_response = getattr(last_message, 'content', str(last_message))
        
        # 라우팅 정보 추출
        routing_info = None
        routing_history = result.get("routing_history", [])
        if routing_history:
            latest_routing = routing_history[-1]
            routing_info = {
                "selected_agent": latest_routing.get("selected_agent"),
                "complexity": latest_routing.get("complexity", 0.0),
                "reasoning": latest_routing.get("reasoning", ""),
                "requires_multiple_agents": latest_routing.get("requires_multiple", False),
                "routing_history": routing_history
            }
        
        # 참조 문서 추출
        references = []
        agent_responses = result.get("agent_responses", {})
        for agent_name, agent_data in agent_responses.items():
            docs = agent_data.get("docs", [])
            for doc in docs[:3]:  # 최대 3개
                references.append({
                    "source": agent_name,
                    "title": doc.get("title", ""),
                    "similarity": doc.get("similarity", 0.0),
                    "metadata": doc.get("metadata", {})
                })
        
        return ai_response, routing_info, references
    
    async def _update_conversation_stats(self, conversation_id: str, routing_info: Optional[Dict]):
        """대화 세션 통계 업데이트"""
        if not routing_info:
            return
        
        stats_key = f"stats:{conversation_id}"
        await self.redis.hincrby(stats_key, "total_messages", 1)
        
        agent = routing_info.get("selected_agent")
        if agent:
            await self.redis.hincrby(stats_key, f"agent_{agent}", 1)
        
        await self.redis.expire(stats_key, 3600 * 24 * 7)  # 7일
    
    async def _cache_conversation(self, conversation: ConversationORM):
        """대화 세션 캐싱"""
        cache_key = f"conversation:{conversation.id}"
        data = {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "message_count": conversation.message_count,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "is_active": conversation.is_active
        }
        
        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(data, default=str))
    
    async def _cache_message(self, message: MessageORM):
        """메시지 캐싱"""
        cache_key = f"message:{message.id}"
        data = {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        }
        
        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(data, default=str))
    
    async def _invalidate_conversation_cache(self, conversation_id: str):
        """대화 관련 캐시 무효화"""
        patterns = [
            f"conversation:{conversation_id}",
            f"history:{conversation_id}:*",
            f"context:{conversation_id}:*"
        ]
        
        for pattern in patterns:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
    
    async def add_user_message(
        self, 
        conversation_id: str, 
        message: str, 
        user_id: int
    ) -> MessageResponse:
        """사용자 메시지 추가"""
        return await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=message,
            user_id=user_id
        )
    
    async def add_assistant_message(
        self,
        conversation_id: str,
        message: str,
        agent_used: str = "unknown",
        extra_metadata: Optional[Dict] = None
    ) -> MessageResponse:
        """어시스턴트 메시지 추가"""
        # 대화의 실제 소유자 ID를 찾아서 사용
        async with self.db_manager.get_db_session() as session:
            conversation = await session.get(ConversationORM, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            actual_user_id = conversation.user_id
        
        return await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=message,
            user_id=actual_user_id,  # 실제 대화 소유자 ID 사용
            agent_used=agent_used,
            extra_metadata=extra_metadata
        )
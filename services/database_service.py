from sqlalchemy.orm import Session
from models.chat_models import ChatSession, UserQuery, Response, get_db
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid

class DatabaseService:
    def __init__(self):
        pass

    def create_session(self, db: Session, user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> ChatSession:
        """
        Create a new chat session
        """
        session = ChatSession(
            user_id=user_id,
            session_metadata=metadata or {}
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(self, db: Session, session_id: UUID) -> Optional[ChatSession]:
        """
        Retrieve a chat session by ID
        """
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    def create_user_query(self, db: Session, session_id: UUID, content: str, selected_text: Optional[str] = None, context_chunks: Optional[List[str]] = None) -> UserQuery:
        """
        Create a new user query in the database
        """
        query = UserQuery(
            session_id=session_id,
            content=content,
            selected_text=selected_text,
            context_chunks=context_chunks or []
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        return query

    def create_response(self, db: Session, query_id: UUID, content: str, source_chunks: Optional[List[str]] = None, confidence_score: Optional[int] = None, token_count: Optional[int] = None, validation_result: Optional[Dict[str, Any]] = None) -> Response:
        """
        Create a new response in the database
        """
        response = Response(
            query_id=query_id,
            content=content,
            source_chunks=source_chunks or [],
            confidence_score=confidence_score,
            token_count=token_count,
            validation_result=validation_result
        )
        db.add(response)
        db.commit()
        db.refresh(response)
        return response

    def get_session_queries(self, db: Session, session_id: UUID, limit: int = 50) -> List[UserQuery]:
        """
        Get all queries for a specific session
        """
        return db.query(UserQuery).filter(
            UserQuery.session_id == session_id
        ).order_by(UserQuery.timestamp.desc()).limit(limit).all()

    def get_query_with_response(self, db: Session, query_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a query with its corresponding response
        """
        query = db.query(UserQuery).filter(UserQuery.query_id == query_id).first()
        if not query:
            return None

        response = db.query(Response).filter(Response.query_id == query_id).first()

        return {
            'query': query,
            'response': response
        }

    def get_recent_sessions(self, db: Session, user_id: str, limit: int = 10) -> List[ChatSession]:
        """
        Get recent sessions for a specific user
        """
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()

    def update_session_metadata(self, db: Session, session_id: UUID, metadata: Dict) -> ChatSession:
        """
        Update session metadata
        """
        session = self.get_session(db, session_id)
        if session:
            session.session_metadata = metadata
            db.commit()
            db.refresh(session)
        return session

# Global instance
database_service = DatabaseService()
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import asyncio
import json
import logging

from backend.models import Notification, User
from backend.database import get_db
from backend.schemas import NotificationCreate, NotificationResponse, NotificationUpdate
from backend.auth.dependencies import get_current_user
from backend.auth.security import decode_token

logger = logging.getLogger(__name__)

# APIRouter without prefix to keep exactly the /notifications routes
router = APIRouter(tags=["Notifications"])


class NotificationPublisher:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, user_id: int) -> asyncio.Queue:
        if user_id not in self._listeners:
            self._listeners[user_id] = set()
        queue = asyncio.Queue()
        self._listeners[user_id].add(queue)
        return queue

    def unsubscribe(self, user_id: int, queue: asyncio.Queue):
        if user_id in self._listeners:
            self._listeners[user_id].discard(queue)
            if not self._listeners[user_id]:
                del self._listeners[user_id]

    async def publish(self, user_id: int, notification_data: dict):
        if user_id in self._listeners:
            for queue in self._listeners[user_id]:
                await queue.put(notification_data)


notification_publisher = NotificationPublisher()


def get_current_user_sse(
    token: str = Query(None),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token type invalid")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id, User.ativo == True).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@router.post("/notifications", response_model=NotificationResponse, status_code=201)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_notification = Notification(
        id_user=current_user.id,
        title=notification.title,
        message=notification.message,
        type=notification.type,
        link=notification.link,
    )
    try:
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        
        notification_payload = {
            "id": db_notification.id,
            "id_user": db_notification.id_user,
            "title": db_notification.title,
            "message": db_notification.message,
            "type": db_notification.type,
            "is_read": db_notification.is_read,
            "link": db_notification.link,
            "created_at": db_notification.created_at.isoformat() if db_notification.created_at else None
        }
        await notification_publisher.publish(current_user.id, notification_payload)
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        db.rollback()
    return db_notification


@router.get("/notifications/sse")
async def notifications_sse(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_sse),
):
    async def event_generator():
        queue = notification_publisher.subscribe(current_user.id)
        try:
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(notification)}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"ping\"}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            notification_publisher.unsubscribe(current_user.id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/notifications", response_model=List[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.id_user == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).limit(50).all()


@router.get("/notifications/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = db.query(Notification).filter(
        Notification.id_user == current_user.id,
        Notification.is_read == False,
    ).count()
    return {"count": count}


@router.put("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.id_user == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


@router.put("/notifications/{notification_id}", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.id_user == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if update.is_read is not None:
        notification.is_read = update.is_read
    
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/notifications/clear-read", status_code=200)
def clear_read_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.id_user == current_user.id,
        Notification.is_read == True,
    ).delete(synchronize_session=False)
    db.commit()
    return {"message": "All read notifications cleared"}


@router.delete("/notifications/{notification_id}", status_code=200)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.id_user == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted successfully"}

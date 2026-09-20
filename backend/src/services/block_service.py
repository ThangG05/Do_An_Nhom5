import uuid
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.db.models.user import User

def is_blocked(db:Session,a:uuid.UUID,b:uuid.UUID)->bool:
 return bool(db.scalar(text("SELECT EXISTS(SELECT 1 FROM user_blocks WHERE (blocker_id=:a AND blocked_id=:b) OR (blocker_id=:b AND blocked_id=:a))"),{"a":a,"b":b}))
def set_block(db:Session,actor:User,target:User,value:bool)->bool:
 if actor.id==target.id:raise HTTPException(400,"Không thể tự chặn chính mình.")
 low,high=sorted((actor.id,target.id))
 if value:
  db.execute(text("INSERT INTO user_blocks(blocker_id,blocked_id) VALUES(:a,:b) ON CONFLICT DO NOTHING"),{"a":actor.id,"b":target.id});db.execute(text("DELETE FROM friendships WHERE user_low_id=:low AND user_high_id=:high"),{"low":low,"high":high});db.execute(text("UPDATE friend_requests SET status='CANCELLED',responded_at=now() WHERE status='PENDING' AND ((sender_id=:a AND receiver_id=:b) OR (sender_id=:b AND receiver_id=:a))"),{"a":actor.id,"b":target.id})
 else:db.execute(text("DELETE FROM user_blocks WHERE blocker_id=:a AND blocked_id=:b"),{"a":actor.id,"b":target.id})
 db.commit();return value

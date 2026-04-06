from fastapi import Request, HTTPException, status
from app.models.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request):
    username = request.cookies.get("username")
    role = request.cookies.get("user_role")
    if not username or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return {"username": username, "role": role}
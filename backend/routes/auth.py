from fastapi import APIRouter, Depends, HTTPException, status

from sqlmodel import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas import UserCreate, UserOut, Token, LoginCred
from auth import authenticate_user, create_access_token, get_session, get_current_user
from jose import jwt
from datetime import datetime
from crud import create_user
from datetime import timedelta

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_session)):
    return create_user(db, user)



@router.post("/login", response_model=Token)
def login(cred: LoginCred, db: Session = Depends(get_session)):
    user = authenticate_user(db, cred.username, cred.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    refresh_token = create_access_token(data={"sub": user.username, "type": "refresh"}, expires_delta=timedelta(days=7))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user

# app/routes/auth.py
from fastapi import APIRouter
from app.services import auth as auth_service

router = APIRouter(tags=["Authentication"])

router.include_router(auth_service.router, prefix="/auth")
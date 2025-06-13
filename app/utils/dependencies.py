# app/utils/dependencies.py
from fastapi import Depends
from app.utils.security import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    oauth2_scheme
)
from app.models.user import User

# Dependencies to use in routes
def get_db():
    # We'll implement this when we add database sessions
    pass

def get_redis():
    # We'll implement this when we need Redis dependencies
    pass

# Auth dependencies
get_current_user_dep = Depends(get_current_user)
get_current_active_user_dep = Depends(get_current_active_user)
get_admin_user_dep = Depends(get_admin_user)
oauth2_scheme_dep = Depends(oauth2_scheme)
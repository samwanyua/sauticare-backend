# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import requests
import os
from fastapi import Body, Form

from api.schemas.auth import UserCreate
from api.db.database import SessionLocal
from api.db.models import User
from api.utils.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------
# SIGNUP
# ------------------------
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(data.password)
    new_user = User(name=data.name, email=data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

# ------------------------
# LOGIN
# ------------------------
@router.post("/login")
def login(
    db: Session = Depends(get_db),
    email: str = Body(None),           # JSON body
    password: str = Body(None),
    form_data: OAuth2PasswordRequestForm = Depends()  # form-data
):
    # Determine which method is used
    user_email = email or form_data.username
    user_password = password or form_data.password

    user = db.query(User).filter(User.email == user_email).first()
    if not user or not verify_password(user_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer", "email": user.email, "name": user.name}

# ------------------------
# CURRENT USER
# ------------------------
@router.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"id": user.id, "name": user.name, "email": user.email}

# ------------------------
# LOGOUT
# ------------------------
@router.post("/logout")
def logout():
    return {"message": "Logout successful. Please remove the token client-side."}

# ------------------------
# RESET PASSWORD
# ------------------------
@router.post("/reset-password")
def reset_password(
    db: Session = Depends(get_db),
    email: str = Body(None),        # JSON body
    email_query: str = None          # optional query param
):
    user_email = email or email_query
    if not user_email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Normally send reset email — placeholder
    return {"message": f"Password reset link sent to {user_email}"}



# ------------------------
# OAUTH LOGIN
# ------------------------
OAUTH_CONFIG = {
    "google": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "user_info_uri": "https://www.googleapis.com/oauth2/v2/userinfo",
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI"),  # e.g. https://yourfrontend.com/auth/callback/google
        "scope": "openid email profile"
    },
    "github": {
        "client_id": os.environ.get("GITHUB_CLIENT_ID"),
        "client_secret": os.environ.get("GITHUB_CLIENT_SECRET"),
        "auth_uri": "https://github.com/login/oauth/authorize",
        "token_uri": "https://github.com/login/oauth/access_token",
        "user_info_uri": "https://api.github.com/user",
        "redirect_uri": os.environ.get("GITHUB_REDIRECT_URI"),
        "scope": "read:user user:email"
    },
    "facebook": {
        "client_id": os.environ.get("FACEBOOK_CLIENT_ID"),
        "client_secret": os.environ.get("FACEBOOK_CLIENT_SECRET"),
        "auth_uri": "https://www.facebook.com/v10.0/dialog/oauth",
        "token_uri": "https://graph.facebook.com/v10.0/oauth/access_token",
        "user_info_uri": "https://graph.facebook.com/me",
        "redirect_uri": os.environ.get("FACEBOOK_REDIRECT_URI"),
        "scope": "email public_profile"
    },
}

@router.get("/oauth/{provider}")
def oauth_redirect(provider: str):
    if provider not in OAUTH_CONFIG:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    conf = OAUTH_CONFIG[provider]
    params = {
        "client_id": conf["client_id"],
        "redirect_uri": conf["redirect_uri"],
        "response_type": "code",
        "scope": conf["scope"]
    }
    url = f"{conf['auth_uri']}?{urlencode(params)}"
    return RedirectResponse(url)

@router.get("/oauth/{provider}/callback")
def oauth_callback(provider: str, code: str, db: Session = Depends(get_db)):
    if provider not in OAUTH_CONFIG:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    
    conf = OAUTH_CONFIG[provider]

    # Exchange code for access token
    data = {
        "client_id": conf["client_id"],
        "client_secret": conf["client_secret"],
        "code": code,
        "redirect_uri": conf["redirect_uri"],
        "grant_type": "authorization_code"
    }

    headers = {"Accept": "application/json"}
    token_resp = requests.post(conf["token_uri"], data=data, headers=headers).json()
    access_token = token_resp.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    # Get user info
    if provider == "google":
        user_info = requests.get(conf["user_info_uri"], headers={"Authorization": f"Bearer {access_token}"}).json()
        email = user_info.get("email")
        name = user_info.get("name")
    elif provider == "github":
        user_info = requests.get(conf["user_info_uri"], headers={"Authorization": f"token {access_token}"}).json()
        email = user_info.get("email")
        if not email:
            # Fallback: get emails separately
            emails = requests.get(f"https://api.github.com/user/emails", headers={"Authorization": f"token {access_token}"}).json()
            primary = next((e for e in emails if e.get("primary")), emails[0])
            email = primary.get("email")
        name = user_info.get("name") or user_info.get("login")
    elif provider == "facebook":
        user_info = requests.get(conf["user_info_uri"], params={"access_token": access_token, "fields": "id,name,email"}).json()
        email = user_info.get("email")
        name = user_info.get("name")
    
    if not email:
        raise HTTPException(status_code=400, detail="Failed to get user email")

    # Check if user exists, else create
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email, hashed_password=hash_password(os.urandom(16).hex()))
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue JWT
    token = create_access_token({"sub": user.email})

   # Redirect to frontend with token (localhost for development)
    redirect_url = f"http://localhost:3000/auth/oauth-success?token={token}&email={email}&name={name}"
    return RedirectResponse(redirect_url)


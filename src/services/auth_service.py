"""
Authentication Service - Handles user authentication and token management
"""
from config.supabase_config import supabase, supabase_admin
from src.models.auth_models import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    FyersTokenStore, FyersTokenResponse
)
from fastapi import HTTPException
from datetime import datetime
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)


class AuthService:
    """Handle authentication operations"""

    def __init__(self):
        self.supabase = supabase
        # Use admin client for operations that need to bypass RLS (like token storage)
        self.supabase_admin = supabase_admin
    
    async def register_user(self, user_data: UserRegister) -> TokenResponse:
        """Register a new user"""
        try:
            # Sign up with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
            })
            
            if not response.user:
                raise HTTPException(status_code=400, detail="Registration failed")
            
            # Try to create user profile in public.users table
            # This might fail due to RLS - if so, it will be created on first login
            try:
                user_profile = {
                    "id": response.user.id,
                    "email": user_data.email,
                    "full_name": user_data.full_name
                }
                self.supabase.table("users").insert(user_profile).execute()
            except Exception as profile_error:
                # Log but don't fail - profile will be created on login
                logger.warning(f"Could not create user profile (will be created on login): {profile_error}")
            
            # Create response
            created_at = datetime.now()
            if response.user.created_at:
                try:
                    created_at = datetime.fromisoformat(str(response.user.created_at).replace('Z', '+00:00'))
                except:
                    pass
            
            user_response = UserResponse(
                id=response.user.id,
                email=response.user.email,
                full_name=user_data.full_name,
                created_at=created_at
            )
            
            # Check if email confirmation is required (no session returned)
            if response.session:
                return TokenResponse(
                    access_token=response.session.access_token,
                    user=user_response,
                    expires_at=datetime.fromtimestamp(response.session.expires_at) if response.session.expires_at else None
                )
            else:
                # Email confirmation required
                return TokenResponse(
                    access_token=None,
                    user=user_response,
                    message="Please check your email to confirm your account before logging in."
                )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Registration error: {error_msg}")
            
            # Provide more helpful error messages
            if "rate limit" in error_msg.lower():
                raise HTTPException(
                    status_code=429,
                    detail="Too many signup attempts. Please wait a few minutes and try again."
                )
            elif "invalid" in error_msg.lower() and "email" in error_msg.lower():
                raise HTTPException(
                    status_code=400, 
                    detail="Please use a valid email address. Test domains like 'example.com' may not be accepted."
                )
            elif "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail="This email is already registered. Please login or use a different email."
                )
            raise HTTPException(status_code=400, detail=f"Registration failed: {error_msg}")
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        """Login existing user"""
        try:
            # Sign in with Supabase Auth
            response = self.supabase.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not response.user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Get user profile
            user_profile = self.supabase.table("users").select("*").eq("id", response.user.id).execute()
            
            profile = user_profile.data[0] if user_profile.data else {}
            
            # Parse created_at safely
            created_at = datetime.now()
            if response.user.created_at:
                try:
                    if isinstance(response.user.created_at, str):
                        created_at = datetime.fromisoformat(response.user.created_at.replace('Z', '+00:00'))
                    elif hasattr(response.user.created_at, 'isoformat'):
                        # It's already a datetime object
                        created_at = response.user.created_at
                except Exception as e:
                    logger.warning(f"Could not parse created_at: {e}")
            
            user_response = UserResponse(
                id=response.user.id,
                email=response.user.email,
                full_name=profile.get("full_name"),
                created_at=created_at
            )
            
            return TokenResponse(
                access_token=response.session.access_token,
                user=user_response,
                expires_at=datetime.fromtimestamp(response.session.expires_at) if response.session.expires_at else None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Login error: {str(e)}")
            
            # Provide helpful error messages
            if "email not confirmed" in error_msg:
                raise HTTPException(
                    status_code=401, 
                    detail="Please confirm your email before logging in. Check your inbox for the confirmation link."
                )
            elif "invalid login credentials" in error_msg or "invalid" in error_msg:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid email or password. Please check your credentials and try again."
                )
            
            raise HTTPException(status_code=401, detail="Login failed. Please check your credentials.")
    
    async def logout_user(self, access_token: str):
        """Logout user and invalidate token"""
        try:
            self.supabase.auth.sign_out()
            return {"message": "Logged out successfully"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise HTTPException(status_code=400, detail="Logout failed")
    
    async def get_current_user(self, access_token: str) -> UserResponse:
        """Get current user from access token"""
        try:
            # Set the session
            self.supabase.auth.set_session(access_token, refresh_token="")
            
            # Get user
            user = self.supabase.auth.get_user(access_token)
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Get user profile
            user_profile = self.supabase.table("users").select("*").eq("id", user.user.id).execute()
            profile = user_profile.data[0] if user_profile.data else {}
            
            # Handle created_at properly - it might be a string or datetime object
            created_at = user.user.created_at
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif hasattr(created_at, 'isoformat'):
                # It's already a datetime object
                pass
            else:
                # Fallback to current time if we can't parse it
                created_at = datetime.now()
            
            return UserResponse(
                id=user.user.id,
                email=user.user.email,
                full_name=profile.get("full_name"),
                created_at=created_at
            )
            
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def store_fyers_token(self, user_id: str, token_data: FyersTokenStore) -> FyersTokenResponse:
        """Store or update Fyers authentication token"""
        try:
            # Use admin client to bypass RLS for token storage
            # Check if token exists
            existing = self.supabase_admin.table("fyers_tokens").select("*").eq("user_id", user_id).execute()

            token_record = {
                "user_id": user_id,
                "access_token": token_data.access_token,
                "refresh_token": token_data.refresh_token,
                "token_type": token_data.token_type,
                "expires_at": token_data.expires_at.isoformat() if token_data.expires_at else None,
                "updated_at": datetime.now().isoformat()
            }

            logger.info(f"📝 Storing Fyers token for user {user_id}")

            if existing.data:
                # Update existing token
                logger.info(f"🔄 Updating existing token for user {user_id}")
                response = self.supabase_admin.table("fyers_tokens").update(token_record).eq("user_id", user_id).execute()
            else:
                # Insert new token
                logger.info(f"➕ Inserting new token for user {user_id}")
                token_record["id"] = str(uuid.uuid4())
                token_record["created_at"] = datetime.now().isoformat()
                response = self.supabase_admin.table("fyers_tokens").insert(token_record).execute()
            
            data = response.data[0]
            
            return FyersTokenResponse(
                id=data["id"],
                user_id=data["user_id"],
                access_token=data["access_token"],
                expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
            
        except Exception as e:
            logger.error(f"Store Fyers token error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to store token: {str(e)}")
    
    async def get_fyers_token(self, user_id: str) -> Optional[FyersTokenResponse]:
        """Get Fyers token for user"""
        try:
            # Use admin client to bypass RLS
            response = self.supabase_admin.table("fyers_tokens").select("*").eq("user_id", user_id).execute()

            if not response.data:
                logger.info(f"🔍 No Fyers token found for user {user_id}")
                return None

            data = response.data[0]
            logger.info(f"✅ Found Fyers token for user {user_id}")

            return FyersTokenResponse(
                id=data["id"],
                user_id=data["user_id"],
                access_token=data["access_token"],
                expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )

        except Exception as e:
            logger.error(f"Get Fyers token error: {str(e)}")
            return None

    async def delete_fyers_token(self, user_id: str):
        """Delete Fyers token for user"""
        try:
            # Use admin client to bypass RLS
            self.supabase_admin.table("fyers_tokens").delete().eq("user_id", user_id).execute()
            logger.info(f"🗑️ Deleted Fyers token for user {user_id}")
            return {"message": "Token deleted successfully"}
        except Exception as e:
            logger.error(f"Delete Fyers token error: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to delete token")


# Create auth service instance
auth_service = AuthService()

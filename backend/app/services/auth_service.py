from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
from backend.app.models import User
from backend.extensions import db

class AuthService:
    @staticmethod
    def authenticate_user(email: str, password: str):
        """Verify credentials and return user if valid."""
        user = User.query.filter_by(email=email).first()
        if not user:
            return None, "Invalid email or password"
        
        if not check_password_hash(user.hashed_password, password):
            return None, "Invalid email or password"
        
        return user, None

    @staticmethod
    def create_token(user: User, expires_in: int = 3600):
        """Create access token with user ID as identity (string) and role as additional claim."""
        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=str(user.id),  
            additional_claims=additional_claims,
            expires_delta=timedelta(seconds=expires_in)
        )
        return access_token

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using werkzeug (pbkdf2:sha256 — avoids scrypt/OpenSSL portability issues)."""
        return generate_password_hash(password, method='pbkdf2:sha256')

    @staticmethod
    def verify_password(hashed_password: str, password: str) -> bool:
        """Verify a password against its hash."""
        return check_password_hash(hashed_password, password)
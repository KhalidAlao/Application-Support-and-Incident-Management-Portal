from .health import health_bp
from .auth import auth_bp
from .incidents import incidents_bp

__all__ = ['health_bp', 'auth_bp', 'incidents_bp']
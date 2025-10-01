from enum import IntEnum
import firebase_admin
from firebase_admin import credentials, auth
from app.config import settings

class AuthType(IntEnum):
    GOOGLE = 0

class AuthInitException(Exception):
    pass

class AuthFailedException(Exception):
    pass

class GoogleAuthBackend:
    _instance = None

    def __init__(self, config):
        self.type = AuthType.GOOGLE
        self.cred = credentials.Certificate(config['SA_KEY_FILE'])
        try:
            firebase_admin.initialize_app(credential=self.cred)
        except ValueError:
            # already initialized
            pass
        except Exception as e:
            raise AuthInitException("Firebase init failed") from e

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GoogleAuthBackend({"SA_KEY_FILE": settings.FIREBASE_SA_FILE})
        return cls._instance

    def verify_token(self, token):
        try:
            decoded = auth.verify_id_token(token)
            if not decoded.get('email_verified'):
                raise AuthFailedException("Email not verified")
        except Exception as e:
            # more specific catches are possible: auth.InvalidIdTokenError, auth.ExpiredIdTokenError, etc.
            raise AuthFailedException("Token verification failed") from e

        return {
            'name': decoded.get('name', 'Anonymous'),
            'email': decoded.get('email'),
            'uid': decoded.get('uid'),
        }

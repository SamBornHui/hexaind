import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException
import time
import os
import logging
from typing import Optional
from datetime import datetime, timezone
from prometheus_client import Counter

JWT_SECRET = os.getenv('JWT_SECRET', '1768b8debb403a6b838f')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_VALIDITY = int(os.getenv('ACCESS_TOKEN_VALIDITY', '80000'))
REFRESH_TOKEN_VALIDITY_IN_DAYS = int(os.getenv('REFRESH_TOKEN_VALIDITY_IN_DAYS', '30'))
EMAIL_TOKEN_VALIDITY_IN_DAYS = int(os.getenv('EMAIL_TOKEN_VALIDITY_IN_DAYS', '3'))
token_validation_counter = Counter('token_validation','Number of token validation events',['user_email', 'time_window'])
logger = logging.getLogger(__package__)
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail={"code": "403", "message": "Invalid authentication scheme.", "data": None})
            if not self.verify_accessToken(credentials.credentials):
                raise HTTPException(status_code=403, detail={"code": "403", "message": "Invalid token or expired token.", "data": None})
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail={"code": "403", "message": "Invalid authorization code.", "data": None})

    def verify_accessToken(self, jwtoken: str) -> bool:
        return isValidAccessToken(jwtoken)

def isValidAccessToken(token: str):
    is_token_valid: bool = False
    try:
        payload = decodeJWT(token)
    except:
        payload = None
    if payload and payload["type"] == "access_token":
        is_token_valid = True
    return is_token_valid

def decodeJWT(token: str) -> Optional[dict]:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        time_now = time.time()
        current_time_window = datetime.now().strftime('%Y-%m-%d %H:%M')
        if decoded_token["expires"] >= time_now:
            user_email = decoded_token.get("email", "unknown")
            token_validation_counter.labels(user_email=user_email, time_window=current_time_window)
            return decoded_token
        else:
            return None
    except Exception as e:
        logging.exception('Failed to decode token at decodeJWT')
        return None

def decode_jwt_ignore_expiry(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except Exception:
        logging.exception('Failed to decode token at decode_jwt_ignore_expiry')
        return None

def getJwtToken(payload):
    try:
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    except Exception as e:
        token = None
    return token

def getAccessToken(email: str, server_role_value: int, user_id: str) -> Optional[str]:
    payload = {
        "email": email,
        "server_role_value": server_role_value,
        "type": "access_token",
        "user_id": user_id,
        "expires": time.time() + ACCESS_TOKEN_VALIDITY
    }
    token = getJwtToken(payload)
    return token

def get_fresh_access_token(enc_token):
    decoded_token = decode_jwt_ignore_expiry(enc_token)
    token = getAccessToken(decoded_token['email'], decoded_token['server_role_value'], decoded_token['user_id'])
    return token

def getRefreshToken(email):
    payload = {
        "email": email,
        "type": "refresh_token",
        "expires": time.time() + (REFRESH_TOKEN_VALIDITY_IN_DAYS * 24 * 60 * 60)
    }
    token = getJwtToken(payload)
    return token

def getMailVerificationToken(email):
    payload = {
        "email": email,
        "type": "mail_verification",
        "expires": time.time() + (EMAIL_TOKEN_VALIDITY_IN_DAYS * 24 * 60 * 60)
    }
    token = getJwtToken(payload)
    return token

def is_email_token_time_expired(token_sent_time: float) -> bool:
    cur_time = int(time.time())
    token_exp_time = (token_sent_time + (EMAIL_TOKEN_VALIDITY_IN_DAYS * 24 * 60 * 60))
    return cur_time >  token_exp_time

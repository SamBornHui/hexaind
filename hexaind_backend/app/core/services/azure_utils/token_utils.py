import jwt
import json
from urllib.request import urlopen
import base64
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import logging
from pydantic import BaseModel
from app.core.services.cloud_utils.azure_secrets import AzureEnvironment
from app.core.services.cloud_utils.azure_secrets import AzureSecretManager

logger = logging.getLogger(__package__)

class RSAModulusExponents(BaseModel):
    modulus: str
    exponent: str

def encode_str_to_utf8(key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    return key

def find_rsa_modulus_exponent(jwks, unverified_header) -> RSAModulusExponents:
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            return RSAModulusExponents(modulus=key['n'], exponent=key['e'])

def get_rsa_pem_from_mod_expos(rsa_mod_exps: RSAModulusExponents):
    return RSAPublicNumbers(
        n=decode_value(rsa_mod_exps.modulus),
        e=decode_value(rsa_mod_exps.exponent)
    ).public_key(default_backend()).public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def decode_value(val):
    decoded = base64.urlsafe_b64decode(encode_str_to_utf8(val) + b'==')
    return int.from_bytes(decoded, 'big')

class AzureTokenUtilsService:
    # Get environment and secret manager instances
    __env = AzureEnvironment()
    __secret_manager = AzureSecretManager()
    
    # Hexaind3 App Client ID used from FE Single page App
    __client_id = __secret_manager.get_secret('hexaind3app-client-id')
    __tenant_id = __env.azure_tenant_id
    __json_web_keyset_url = f'https://login.microsoftonline.com/{__tenant_id}/discovery/keys'
    __access_token_issuer_url = f'https://sts.windows.net/{__tenant_id}/'

    #To Decode ID Token 
    __id_token_issuer_url = f'https://login.microsoftonline.com/{__tenant_id}/v2.0'

    __audience = f'{__client_id}'

    @classmethod
    def decode_azure_token(cls, token, issuer_url):
        json_web_keyset = json.loads(urlopen(cls.__json_web_keyset_url).read())
        """
        Note on Signature Verification Without kid:
        Why Using kid is Important: JWTs' headers specify a kid that helps consumers identify which key in a JWKS to use for verifying the token's signature. 
        Without this, you must either try all keys (INEFFICIENT AND POTENTIALLY INSECURE) or have other means to ensure key correspondence.
        Security Concerns:
        Skipping kid matching or trying to verify a JWT without confirming the kid matches the key used poses a risk of 
        using an outdated or incorrect key, POTENTIALLY LEADING TO ACCEPTING INVALID TOKENS.
        """
        unverified_header = jwt.get_unverified_header(token)
        rsa_mod_exps: RSAModulusExponents = find_rsa_modulus_exponent(json_web_keyset, unverified_header)
        public_key = get_rsa_pem_from_mod_expos(rsa_mod_exps)

        return jwt.decode(
        token,
        public_key,
        verify=True,
        algorithms=['RS256'],
        audience=cls.__audience,
        issuer=issuer_url
        )

    @classmethod
    def decode_azure_id_token(cls, token):
        try:
            return cls.decode_azure_token(token, cls.__id_token_issuer_url)
        except Exception:
            logger.exception("Failed to decode azure raw token")
            return None

    @classmethod
    def decode_azure_access_token(cls, token):
        try:
            return cls.decode_azure_token(token, cls.__access_token_issuer_url)
        except Exception:
            logger.exception("Failed to decode azure access token")
            return None

import json, os
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))

def encrypt_json(obj: dict, password: str) -> str:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    ct = aes.encrypt(nonce, data, None)
    return b64encode(salt + nonce + ct).decode("ascii")

def decrypt_json(token_b64: str, password: str) -> dict:
    raw = b64decode(token_b64.encode("ascii"))
    salt, nonce, ct = raw[:16], raw[16:28], raw[28:]
    key = derive_key(password, salt)
    aes = AESGCM(key)
    data = aes.decrypt(nonce, ct, None)
    return json.loads(data.decode("utf-8"))
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

KEYS_DIR = Path(__file__).resolve().parents[2] / "config" / "keys"
KEYS_DIR.mkdir(parents=True, exist_ok=True)
PRIV = KEYS_DIR / "audit_ed25519_private.pem"
PUB  = KEYS_DIR / "audit_ed25519_public.pem"

def ensure_keys():
    if not PRIV.exists() or not PUB.exists():
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        PRIV.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        PUB.write_bytes(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

def load_keys():
    ensure_keys()
    private_key = serialization.load_pem_private_key(PRIV.read_bytes(), password=None)
    public_key  = serialization.load_pem_public_key(PUB.read_bytes())
    return private_key, public_key
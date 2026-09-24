import os
from cryptography.fernet import Fernet

key = os.environ.get("TOKEN_ENCRYPTION_KEY")
if not key:
    raise RuntimeError("TOKEN_ENCRYPTION_KEY environment variable is required")

fernet = Fernet(key.encode())

def encrypt_secret(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_secret(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()

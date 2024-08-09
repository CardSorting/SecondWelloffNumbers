from cryptography.fernet import Fernet
import base64

class EncryptionUtil:
    def __init__(self, key):
        if not key:
            raise ValueError("Encryption key is not set. Please set the ENCRYPTION_KEY environment variable.")
        try:
            # Ensure the key is 32 bytes long and properly encoded
            key_bytes = key.encode() if isinstance(key, str) else key
            if len(key_bytes) != 32:
                raise ValueError("Encryption key must be 32 bytes long")
            self.key = base64.urlsafe_b64encode(key_bytes)
            self.fernet = Fernet(self.key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {str(e)}")

    def encrypt(self, data):
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data):
        return self.fernet.decrypt(encrypted_data.encode()).decode()
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from app.Database.DatabaseOperations import DatabaseOperations
from app.utils.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class KeyHandler:
    def __init__(self, databaseops: DatabaseOperations):
        self.databaseops = databaseops
        
        master_key_b64 = os.environ.get("MASTER_KEY")
        if not master_key_b64:
            raise ValueError("MASTER_ENCRYPTION_KEY environment variable not set")
        self.master_cipher = Fernet(master_key_b64.encode())

    def _encrypt_key(self, key_bytes: bytes) -> str:
        encrypted = self.master_cipher.encrypt(key_bytes)
        return base64.b64encode(encrypted).decode('utf-8')

    def _decrypt_key(self, encrypted_b64: str) -> bytes:
        encrypted = base64.b64decode(encrypted_b64.encode('utf-8'))
        return self.master_cipher.decrypt(encrypted)

    async def addKeyToDatabase(self, key_hex: str, db: AsyncSession, user_id: str) -> bool:
        """Store the key (hex) after encrypting it."""
        # convert hex to bytes, then encrypt
        key_bytes = bytes.fromhex(key_hex)
        encrypted_b64 = self._encrypt_key(key_bytes)

        user = await self.databaseops.GetUserByID(db, user_id)
        if not user:
            logger.error("Failed to find user while storing encryption key: %s", user_id)
            return False

        updated = await self.databaseops.AddUserKey(db, user_id, encrypted_b64)  # store encrypted
        if updated == 0:
            logger.error("Failed to update encryption key for user %s", user_id)
            return False

        logger.info("Encryption key stored successfully (encrypted) for user %s", user_id)
        return True

    async def createKey(self, user_id: str, db: AsyncSession) -> str:
        """Generate a new 256-bit key, store encrypted, return plain hex (for the caller)."""
        key_bytes = AESGCM.generate_key(bit_length=256)
        key_hex = key_bytes.hex()

        logger.info("Generated new encryption key for user %s", user_id)

        success = await self.addKeyToDatabase(key_hex, db, user_id)
        if not success:
            raise Exception("Failed to store newly generated encryption key in database")

        return key_hex   

    async def getKey(self, db: AsyncSession, user_id: str) -> bytes | None:
        """Retrieve the key, decrypt it, and return raw bytes."""
        user = await self.databaseops.GetUserByID(db, user_id)
        if not user:
            logger.error("User %s not found when retrieving encryption key", user_id)
            return None

        stored = getattr(user, "encryption_key", None)

        # If no key exists yet, create one
        if not stored:
            key_hex = await self.createKey(user_id, db)
            return bytes.fromhex(key_hex)

        # stored is now the encrypted base64 string
        # We'll try to decrypt; if it fails, assume it's plain hex (migration scenario)
        try:
            return self._decrypt_key(stored)
        except Exception as e:
            # If decryption fails, it might be a legacy plain hex key.
            # You can either migrate it or raise an error.
            logger.warning("Failed to decrypt key for user %s, treating as plain hex (legacy).", user_id)
            try:
                return bytes.fromhex(stored)
            except (TypeError, ValueError):
                logger.error("Invalid encryption_key format in DB for user %s", user_id)
                raise
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.Encryption.keyGenerator import KeyHandler
from app.utils.logger import SingletonLogger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.FileManager.fileOperations import fileOperations

logger = SingletonLogger().get_logger()


class EncryptionService:
    def __init__(self, keyhandler: KeyHandler, fileoperations: "fileOperations"):
        
        self.keyhandler = keyhandler
        self.fileoperations = fileoperations

    async def encrypt(self, user_id: str, plaintext: bytes, db: AsyncSession) -> tuple[bytes, bytes]:
        key = await self.keyhandler.getKey(db=db, user_id=user_id)
        if not key:
            raise ValueError("No encryption key available for user")
        if not isinstance(key, (bytes, bytearray)):
            raise ValueError("Encryption key must be bytes")
        if len(key) != 32:
            raise ValueError("Invalid key length (must be 32 bytes for AES-256)")

        aesgcm = AESGCM(bytes(key))
        nonce = os.urandom(12)
        aad = str(user_id).encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
        return nonce, ciphertext

    async def decrypt(self, user_id: str, ciphertext: bytes, nonce: bytes, db: AsyncSession) -> bytes:
        key = await self.keyhandler.getKey(db=db, user_id=user_id)
        if not key:
            raise ValueError("No encryption key available for user")
        if not isinstance(key, (bytes, bytearray)):
            raise ValueError("Encryption key must be bytes")
        if len(key) != 32:
            raise ValueError("Invalid key length (must be 32 bytes for AES-256)")

        aesgcm = AESGCM(bytes(key))
        aad = str(user_id).encode("utf-8")
        return aesgcm.decrypt(nonce, ciphertext, aad)
import os
from typing import TYPE_CHECKING
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from app.Database.DatabaseOperations import DatabaseOperations
from app.Encryption_Services.keyGenerator import KeyHandler

if TYPE_CHECKING:
    from app.FileManager.fileOperations import fileOperations


class EncryptionService:
    def __init__(self, keyhandler: KeyHandler, fileoperations: "fileOperations"):
        self.keyhandler = keyhandler(DatabaseOperations)
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

    async def decrypt(self, file_path: str, user_id: str, db: AsyncSession) -> bytes:
        key = await self.keyhandler.getKey(db=db, user_id=user_id)
        if not key or not isinstance(key, (bytes, bytearray)):
            raise ValueError("No encryption key available for user")
        if len(key) != 32:
            raise ValueError("Invalid key length (must be 32 bytes for AES-256)")

        blob = await self.fileoperations.read_file(file_path)
        if len(blob) < 12:
            raise ValueError("Encrypted file too short to contain nonce")

        nonce = blob[:12]
        ciphertext = blob[12:]

        aesgcm = AESGCM(bytes(key))
        aad = str(user_id).encode("utf-8")

        return aesgcm.decrypt(nonce, ciphertext, aad)
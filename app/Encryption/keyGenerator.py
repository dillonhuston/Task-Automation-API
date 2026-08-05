from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.ext.asyncio import AsyncSession

from app.Database.DatabaseOperations import DatabaseOperations
from app.utils.logger import SingletonLogger

logger = SingletonLogger().get_logger()


class KeyHandler:
    def __init__(self, databaseops: DatabaseOperations):
        self.databaseops = databaseops

    async def addKeyToDatabase(self, key_hex: str, db: AsyncSession, user_id: str) -> bool:
        user = await self.databaseops.GetUserByID(db, user_id)
        if not user:
            logger.error("Failed to find user while storing encryption key: %s", user_id)
            return False

        updated = await self.databaseops.AddUserKey(db, user_id, key_hex)
        if updated == 0:
            logger.error("Failed to update encryption key for user %s", user_id)
            return False

        logger.info("Encryption key stored successfully for user %s", user_id)
        return True

    async def createKey(self, user_id: str, db: AsyncSession) -> str:
        """Generate a new 256-bit key and store it as hex string in DB. Returns the hex string."""
        key_bytes = AESGCM.generate_key(bit_length=256)
        key_hex = key_bytes.hex()

        logger.info("Generated new encryption key for user %s", user_id)

        success = await self.addKeyToDatabase(key_hex, db, user_id)
        if not success:
            raise Exception("Failed to store newly generated encryption key in database")

        return key_hex

    async def getKey(self, db: AsyncSession, user_id: str) -> bytes | None:
        user = await self.databaseops.GetUserByID(db, user_id)
        if not user:
            logger.error("User %s not found when retrieving encryption key", user_id)
            return None

        if not getattr(user, "encryption_key", None):
            key_hex = await self.createKey(user_id, db)
            return bytes.fromhex(key_hex)

        stored = user.encryption_key

        if isinstance(stored, bytes):
            return stored

        try:
            return bytes.fromhex(stored)
        except (TypeError, ValueError) as e:
            logger.error("Invalid encryption_key format in DB for user %s: %s", user_id, e)
            raise

from sqlalchemy.orm import Session
from app.models.user import UserModel
from app.utils.logger import SingletonLogger
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = SingletonLogger().get_logger()

#TODO remove all db operations into one file instead of doing so within this function. Also add any encrpytion key operations into a service that handles this alone. Also add pydantic
#TODO add dependency injections 
class KeyHandler:

    @staticmethod
    def addKeyToDatabase(key_hex: str, db: Session, user_id: int) -> bool:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            logger.error("Failed to find user %s while storing encryption key", user_id)
            return False
        
        user.encryption_key = key_hex
        db.commit()
        logger.info("Encryption key stored successfully for user %s", user_id)
        return True

    @staticmethod
    def createKey(user_id: int, db: Session) -> str:
        """Generate a new 256-bit key and store it as hex string in DB. Returns the hex string."""
        key_bytes = AESGCM.generate_key(bit_length=256)
        key_hex = key_bytes.hex()

        logger.info("Generated new encryption key for user %s", user_id)
        
        success = KeyHandler.addKeyToDatabase(key_hex, db, user_id)
        if not success:
            raise Exception("Failed to store newly generated encryption key in database")
        
        return key_hex

    @staticmethod
    def getKey(user_id: int, db: Session) -> bytes:
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            logger.error("User %s not found when retrieving encryption key", user_id)
            return None

        if not user.encryption_key:
            key_hex = KeyHandler.createKey(user_id, db)
            return bytes.fromhex(key_hex)

        if isinstance(user.encryption_key, bytes):
            logger.warning(" raw bytes key detected for user %s - using directly", user_id)
            return user.encryption_key
        else:
            try:
                return bytes.fromhex(user.encryption_key)
            except (TypeError, ValueError) as e:
                logger.error("Invalid encryption_key format in DB for user %s: %s", user_id, e)
                raise
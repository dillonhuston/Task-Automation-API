import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.Encryption_Services.keyGenerator import KeyHandler
from app.utils.logger import SingletonLogger

logger = SingletonLogger().get_logger()


"""
    This whole file need to be changed to a celery task.

    Why: Having any function that restricts the api from being used for anything else is bad. This is why we use celery to execute tasks while keeping the server functional and accessible.

    If task encrpytion fails or the file is not required, the app would just crash. Thats why we seperate all concerns into its own module.

    Security: We cant just put our encryption and decryption in with our api route, youd be hakced in the first hour, with passwint raw bytes over network. Big NONO 

"""

#TODO clean OOP these should not be a static method and also start adding pydantic. remove all useless excption and replace with global handler deriving from custom exceptions
class EncryptionService():
    @staticmethod
    def encrypt(file_path: str, user_id: str, db: Session):
        key = KeyHandler.getKey(user_id, db)
        if not key:
            raise Exception("No encryption key available for user")

        if not isinstance(key, bytes):
            raise Exception("Encryption key is not in bytes format")
        
        if len(key) != 32:
            raise Exception("Invalid key length (must be 32 bytes for AES-256)")
        #TODO remove these actions into a service of its own. We should not be opening files and encrypting in the same file
        # Read plaintext
        with open(file_path, 'rb') as f:
            data = f.read()

        # Encrypt
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        aad = str(user_id).encode()
        
        encrypted_bytes = aesgcm.encrypt(nonce, data, aad)

        # Overwrite file 
        with open(file_path, 'wb') as f:
            f.write(encrypted_bytes)
        return nonce

    @staticmethod
    def decrypt(file_path: str, user_id: str, db: Session, nonce)-> bytes:
        """Again need to add some error handlers here"""
        #TODO Same here, remove all file handling operations and encryption from this function 
        key = KeyHandler.getKey(user_id, db)
        try:
            with open(file_path,'rb')as f:
                encrypted_data = f.read() 
        except Exception as e:
            raise HTTPException(status_code=500, detail={e})
        
        # get data prepared 
        aesgcm = AESGCM(key)
        aad = user_id.encode('utf-8')

        # try to derypted
        try:
            plaintext = aesgcm.decrypt(
                nonce,
                encrypted_data,
                aad
                )
            return plaintext
        except Exception as e:
            logger.exception("Decryption failed for file %s (user %s): %s", file_path, user_id,e)
       
       




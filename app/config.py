
"""CONFIG FOR APP """
import os
from dotenv import load_dotenv



load_dotenv()

class Config:
    #TODO this also should not be os, as some people might deploy to different systems. ALso to impot BaseSettings for FastAPI use

    SECRET_KEY = os.getenv("SECRET_KEY", "ef69d3115c60d774e98a08a8665e251f213d39a8cd76c1b99f5ad111469b3368")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    TOKEN_FILE = os.getenv("TOKEN_FILE", "")
    POLL_INTERVAL = os.getenv("POLL_INTERVAL", "10") # In seconds 
    HOST = os.getenv("HOST")


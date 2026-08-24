from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    
    #CREDENCIALES PARA LA DB
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME") 
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    SCHEMA = 'obras'
    
    #CREDENCIALES CONFIGURACION APP
    SECRET_KEY = os.getenv("SECRET_KEY", "obratec_secret_key_123456")
    TOKEN_KEY = os.getenv("TOKEN_KEY", "obratec_token_key_1234567890abcdef")
    DEBUG = os.getenv("DEBUG", "True")



    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "OBRATEC")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", 10))
    RECOVERY_CODE_SECRET = os.getenv("RECOVERY_CODE_SECRET")
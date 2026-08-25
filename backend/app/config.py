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


    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
    BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "OBRATEC")
    BREVO_TIMEOUT_SECONDS = int(os.getenv("BREVO_TIMEOUT_SECONDS", 10))

    RECOVERY_CODE_SECRET = os.getenv("RECOVERY_CODE_SECRET")

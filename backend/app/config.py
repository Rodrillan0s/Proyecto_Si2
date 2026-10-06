from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv(), override=True)

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

    # CREDENCIALES GEMINI IA
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'deepseek' if os.getenv('DEEPSEEK_API_KEY') else 'gemini')
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    AI_TIMEOUT_SECONDS = int(os.getenv('AI_TIMEOUT_SECONDS', '30'))
    SPEECH_PROVIDER = os.getenv('SPEECH_PROVIDER', 'disabled')
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'small')

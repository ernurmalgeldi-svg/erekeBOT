import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Жобаның негізгі папкасына жол табу
BASE_DIR = Path(__file__).resolve().parent.parent
env_file_path = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Тек үлкен әріппен жазамыз, Pydantic-ке осы жеткілікті
    TELEGRAM_BOT_TOKEN: str = ""
    GROQ_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()

# Егер .env-ді автоматты оқи алмаса, күштеп os.getenv арқылы толтырамыз
if not config.TELEGRAM_BOT_TOKEN:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_file_path)
    config.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    config.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Задача 2: Человекочитаемая ошибка (Адам түсінетін қате шығару)
if not config.TELEGRAM_BOT_TOKEN or not config.GROQ_API_KEY:
    print("\n" + "="*60)
    print("❌ ҚАТЕ: .env файлынан қажетті токендер табылмады!")
    print(f"Файл мына жерде тұруы керек: {env_file_path}")
    print("Ішінде мына жолдар болуын тексеріңіз:")
    print("TELEGRAM_BOT_TOKEN=сіздің_токен")
    print("GROQ_API_KEY=сіздің_groq_кілт")
    print("="*60 + "\n")
    sys.exit(1)
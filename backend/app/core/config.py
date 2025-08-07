import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_V1_STR: str = "/api/v1"
    # Gere uma chave segura com: openssl rand -hex 32
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "a_super_secret_key_that_must_be_changed")
    ALGORITHM = "HS256"
    # 60 minutos * 24 horas * 7 dias = 7 dias
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
    # A chave de serviço (service_role) é necessária para operações de admin no backend
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

    # Validação básica no início
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY precisam ser definidos no ambiente.")

ssettings = Settings()

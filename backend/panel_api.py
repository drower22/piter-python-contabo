import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

# Cria a instância da aplicação para o painel
app = FastAPI(
    title="Agency Panel API",
    description="API para o painel de agências parceiras.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configuração de CORS (Cross-Origin Resource Sharing)
# Permite que o frontend React (em outro domínio/porta) se comunique com esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja para o domínio do seu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui o roteador da API v1
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Status"])
def read_root():
    """Endpoint raiz para verificar a saúde da API do painel."""
    return {"status": "ok", "message": "Bem-vindo à API do Painel de Agências!"}

# Permite a execução direta para desenvolvimento
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

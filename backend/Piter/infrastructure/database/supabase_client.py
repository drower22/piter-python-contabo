"""
Cliente de Conexão com o Supabase.

Este módulo fornece uma função para instanciar e retornar um cliente Supabase,
configurado com as credenciais de serviço para operações de backend.
"""

from functools import lru_cache
from supabase import create_client, Client
from ...core.settings import get_settings

# Export SupabaseClient para type hinting em outros módulos
SupabaseClient = Client

@lru_cache()
def get_supabase() -> SupabaseClient:
    """
    Cria e retorna uma instância do cliente Supabase.

    Utiliza as configurações de URL e a chave de serviço (service role key) para
    inicializar o cliente, permitindo operações com privilégios de administrador.
    O resultado é cacheado para reutilizar a mesma instância do cliente.

    Returns:
        Uma instância do cliente Supabase.
    """
    settings = get_settings()
    
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return client

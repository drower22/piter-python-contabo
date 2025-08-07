from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.api import deps
from app.db.supabase import supabase_client
from app.schemas.account import Account
from app.schemas.user import User as UserSchema

router = APIRouter()

@router.get("/accounts", response_model=List[Account])
def read_accounts(
    current_user: UserSchema = Depends(deps.get_current_user)
):
    """
    Recupera a lista de contas. 
    - Super admins veem todas as contas.
    - Usuários de agência veem apenas as contas da sua agência.
    """
    query = supabase_client.table("accounts").select("*")

    if current_user.role != 'super_admin':
        if not current_user.agency_id:
            raise HTTPException(status_code=403, detail="Usuário de agência não tem um ID de agência associado.")
        query = query.eq('agency_id', str(current_user.agency_id))

    try:
        response = query.execute()
        accounts_data = response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contas: {str(e)}")

    return accounts_data

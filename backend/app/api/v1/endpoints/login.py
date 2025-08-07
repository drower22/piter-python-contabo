from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, UUID4

from app.api.deps import get_db, get_supabase_client
from app.core.security import create_access_token
from app.schemas.token import Token
from app.crud.crud_user import user as crud_user
from supabase import Client

router = APIRouter()

class UserProfileCompletion(BaseModel):
    user_id: UUID4
    email: EmailStr

@router.post("/complete-profile")
def complete_user_profile(
    *, 
    db: Session = Depends(get_db),
    supabase: Client = Depends(get_supabase_client),
    profile_data: UserProfileCompletion
):
    """
    Creates the user profile in public.agency_users after password setup.
    This is called by the frontend right after a successful password update.
    """
    # Verifica se o perfil já não existe para evitar duplicatas
    existing_profile = db.query(crud_user.model).filter(crud_user.model.id == profile_data.user_id).first()
    if existing_profile:
        # O perfil já existe, não há nada a fazer.
        return {"message": "Profile already exists."}

    # Cria o perfil na tabela agency_users
    # O valor 'role' usará o DEFAULT da tabela ('admin')
    # O valor 'agency_id' será NULL, pois o usuário ainda não está associado a uma agência
    try:
        # Usando o cliente supabase para inserir diretamente, pois o CRUD pode não estar configurado para isso
        # Isso também garante que estamos usando a mesma lógica que o gatilho tentava usar
        data, count = supabase.table('agency_users').insert({
            'id': str(profile_data.user_id),
            'email': profile_data.email
            # 'role' e 'agency_id' usarão os padrões do banco de dados
        }).execute()

    except Exception as e:
        # Se algo der errado, levanta um erro HTTP
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user profile: {str(e)}"
        )

    return {"message": "User profile completed successfully."}


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    try:
        # Supabase Auth para validar o usuário
        user_session = supabase_client.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        user_id = user_session.user.id

        # Buscar role e agency_id da nossa tabela 'users'
        response = supabase_client.table('users').select('role', 'agency_id').eq('id', user_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User metadata not found in public.users table.")

        user_metadata = response.data
        role = user_metadata.get('role', 'agency_viewer')
        agency_id = user_metadata.get('agency_id')

        # Criar o token JWT com os dados
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            subject=str(user_id),
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    except Exception as e:
        # Captura erros de autenticação do Supabase ou outros
        raise HTTPException(
            status_code=400,
            detail=f"Incorrect email or password: {str(e)}",
        )

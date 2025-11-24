from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.token import Token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Enregistrer un nouvel utilisateur"""
    try:
        # 1. Vérifier l'unicité du téléphone
        result = await db.execute(select(User).where(User.phone == user_in.phone))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Ce numéro est déjà utilisé")

        # 2. Hasher le password
        hashed_password = get_password_hash(user_in.password)
        print(f"✅ Password hashé: {hashed_password[:20]}...")

        # 3. Créer l'utilisateur
        new_user = User(
            phone=user_in.phone,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role
        )
        db.add(new_user)
        await db.flush()

        # 4. Créer le wallet
        new_wallet = Wallet(user_id=new_user.id)
        db.add(new_wallet)

        # 5. Commit
        await db.commit()
        await db.refresh(new_user)

        print(f"✅ Utilisateur créé: {new_user.phone}")
        return new_user

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur registration: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """Connexion utilisateur"""
    try:
        # 1. Trouver l'utilisateur
        result = await db.execute(select(User).where(User.phone == user_in.phone))
        user = result.scalars().first()

        if not user:
            print(f"❌ Utilisateur non trouvé: {user_in.phone}")
            raise HTTPException(status_code=401, detail="Identifiants incorrects")

        # 2. Vérifier le password
        is_valid = verify_password(user_in.password, user.hashed_password)
        print(f"Vérification password pour {user_in.phone}: {is_valid}")
        print(f"  Hash DB: {user.hashed_password[:30]}...")
        print(f"  Password: {user_in.password}")

        if not is_valid:
            print(f"❌ Password invalide pour {user_in.phone}")
            raise HTTPException(status_code=401, detail="Identifiants incorrects")

        # 3. Vérifier que le compte est actif
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Compte inactif")

        # 4. Créer le token
        access_token = create_access_token(subject=user.id)
        print(f"✅ Login réussi pour {user_in.phone}, token créé")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur login: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
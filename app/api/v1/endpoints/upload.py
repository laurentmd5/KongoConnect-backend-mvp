import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter()

# Assurez-vous que le répertoire de stockage existe au démarrage
Path(settings.STATIC_DIR).mkdir(parents=True, exist_ok=True)

@router.post("/", summary="Upload de Fichier (Photo de Preuve ou de Profil)")
async def upload_file(
    file: UploadFile = File(...),
    # On force l'utilisateur à être connecté pour l'upload
    current_user: User = Depends(get_current_user)
):
    """
    Accepte un fichier (idéalement compressé par le client), le sauve
    localement et retourne l'URL d'accès.
    """
    
    # 1. Validation de base
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Seuls les formats JPEG, PNG et WebP sont acceptés.")

    # 2. Création d'un nom de fichier unique et sécurisé (UUID)
    # L'extension est extraite du nom original pour la compatibilité.
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # 3. Chemin complet du fichier
    file_path = Path(settings.STATIC_DIR) / unique_filename
    
    try:
        # 4. Écriture du fichier sur le disque
        with open(file_path, "wb") as buffer:
            # Note: read() charge tout en mémoire, ce qui est acceptable pour des fichiers pré-compressés (150-500 KB)
            data = await file.read() 
            buffer.write(data)
            
        # 5. Construction de l'URL de retour
        # L'URL est relative au préfixe /static que nous allons ajouter dans main.py
        file_url = f"{settings.STATIC_URL}/{unique_filename}"
        
        return JSONResponse(content={
            "filename": unique_filename,
            "url": file_url,
            "user_id": current_user.id
        })

    except Exception as e:
        # En cas d'erreur de disque ou autre
        raise HTTPException(status_code=500, detail=f"Échec de l'upload: {e}")
import asyncio
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.order import Order
from app.models.base_class import Base # Nécessaire pour l'initialisation DB

logger = logging.getLogger(__name__)

# --- Configuration Gemini (Synchrone) ---

# Configuration unique au démarrage de l'app (main.py)
try:
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("🧠 Gemini configuré.")
    else:
        logger.warning("⚠️ GEMINI_API_KEY non définie. Le service IA est désactivé.")
except Exception as e:
    logger.error(f"❌ Erreur de configuration Gemini: {e}")

# ThreadPool pour les appels Gemini (qui sont synchrones)
executor = ThreadPoolExecutor(max_workers=2)

class AISimplifierService:

    @staticmethod
    def _call_gemini(description: str) -> dict:
        """
        Appel SYNCHRONE à Gemini.
        S'exécute dans un thread séparé (via run_in_executor) pour ne pas bloquer FastAPI.
        """
        print(f"🧠 DEBUG IA: Appel Gemini avec description: '{description}'")  
        
        if not settings.GEMINI_API_KEY:
            print("🧠 DEBUG IA: API Key manquante")  
            return {"success": False, "error": "API Key manquante"}
             
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""Tu es un assistant pour artisans. Analyse ce problème du client : "{description}"
Retourne UNIQUEMENT un JSON brut (pas de markdown) :
{{
    "title": "Titre technique court (max 5 mots, ex: Fuite d'eau WC)",
    "category": "PLOMBERIE|ELECTRICITE|FROID|MACONNERIE|DIVERS",
    "tags": "mot1,mot2,mot3,mot4"
}}"""
            
            print("🧠 DEBUG IA: Envoi requête à Gemini...")  
            
            # Appel SYNC
            response = model.generate_content(prompt)

            
            text = response.text
            print(f"🧠 DEBUG IA: Réponse Gemini brute: {text}")  
            
            # Le modèle avec response_mime_type doit retourner du JSON propre, 
            # mais on garde la logique de nettoyage pour plus de robustesse.
            clean_json = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            print(f"🧠 DEBUG IA: JSON parsé: {data}")  
            
            return {
                "success": True,
                "title": data.get("title", "Analyse en cours"),
                "category": data.get("category", "DIVERS"),
                "tags": data.get("tags", "")
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON Parse Error: {e}. Response: {text}")
            print(f"🧠 DEBUG IA: Erreur JSON: {e}") 
            return {"success": False, "error": "JSON_PARSE_ERROR"}
            
        except Exception as e:
            logger.error(f"❌ Gemini Error: {e}")
            print(f"🧠 DEBUG IA: Erreur Gemini: {e}") 
            return {"success": False, "error": str(e)}

    @staticmethod
    async def analyze_order(order_id: int, description: str):
        """
        Analyse asynchrone via ThreadPool. Ouvre sa propre session DB.
        """
        print(f"🧠 DEBUG IA: Début analyse pour order #{order_id}")  
        
        if not description:
            print(f"🧠 DEBUG IA: Description vide pour order #{order_id}") 
            return
            
        if len(description) < 5:
            print(f"🧠 DEBUG IA: Description trop courte pour order #{order_id}") 
            return
            
        if not settings.GEMINI_API_KEY:
            print(f"🧠 DEBUG IA: API Key manquante pour order #{order_id}")  
            return

        from app.db.session import AsyncSessionLocal
        
        logger.info(f"🧠 IA: Analyse commande #{order_id} EN COURS...")
        print(f"🧠 DEBUG IA: Analyse commande #{order_id} EN COURS...")  
        
        # 1. Exécuter l'appel Gemini dans un thread séparé
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            AISimplifierService._call_gemini,
            description
        )
        
        print(f"🧠 DEBUG IA: Résultat Gemini pour order #{order_id}: {result}")  
        
        if not result.get("success"):
            logger.warning(f"⚠️ IA Analysis failed for #{order_id}: {result.get('error')}")
            print(f"🧠 DEBUG IA: Échec analyse pour order #{order_id}: {result.get('error')}")  
            return

        # 2. Ouvrir une session DB dédiée pour la mise à jour (Critique #3: SAFE DB)
        async with AsyncSessionLocal() as db:
            try:
                order = await db.get(Order, order_id)
                if order:
                    order.ai_title = result["title"]
                    # Ajout des nouveaux champs
                    order.ai_category = result["category"] 
                    order.ai_tags = result["tags"] 
                    order.ai_summary = description # Utiliser description comme summary pour MVP
                    
                    await db.commit()
                    logger.info(f"✅ IA: Order #{order_id} enrichie -> {result['title']}")
                    print(f"🧠 DEBUG IA: Order #{order_id} mis à jour avec succès -> {result['title']}")  
                else:
                    logger.warning(f"Commande {order_id} non trouvée pour mise à jour IA.")
                    print(f"🧠 DEBUG IA: Commande {order_id} non trouvée en DB")  
            except Exception as e:
                await db.rollback()
                logger.error(f"❌ Erreur de mise à jour DB après IA: {e}")
                print(f"🧠 DEBUG IA: Erreur DB pour order #{order_id}: {e}")  
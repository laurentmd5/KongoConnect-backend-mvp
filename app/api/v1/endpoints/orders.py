from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderResponse
from app.services.escrow_service import EscrowService
from app.services.ai_simplifier import AISimplifierService   # ⬅️ IMPORT IA

router = APIRouter()


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate,
    background_tasks: BackgroundTasks,     # ⬅️ Permet d'appeler l'IA en tâche de fond
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer une nouvelle demande de service (Statut PENDING)."""

    # 1. Vérifier si le service/produit existe
    result = await db.execute(select(Listing).where(Listing.id == order_in.listing_id))
    listing = result.scalars().first()
    if not listing:
        raise HTTPException(status_code=404, detail="Service/Produit introuvable")

    # 2. Création de la commande
    # Note: Pour le MVP, le prix est fixe. En V2, on pourra négocier.
    new_order = Order(
        client_id=current_user.id,
        partner_id=listing.partner_id,
        listing_id=listing.id,
        total_amount=listing.price,
        delivery_needed=order_in.delivery_needed,
        delivery_address=order_in.delivery_address,
        problem_description=order_in.problem_description,
        status=OrderStatus.PENDING
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    # ------------- 🔥 INTÉGRATION IA (SAFE ASYNC BACKGROUND TASK) -------------
    if order_in.problem_description:
        background_tasks.add_task(
            AISimplifierService.analyze_order,
            new_order.id,
            order_in.problem_description
        )
        print(f"🧠 IA: Tâche lancée pour order #{new_order.id}")  # ⬅️ LOG DE CONFIRMATION
    # -------------------------------------------------------------------------

    return new_order


@router.get("/", response_model=List[OrderResponse])
async def my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère l'historique des commandes (Client ou Partenaire)."""

    query = select(Order).where(
        (Order.client_id == current_user.id) | (Order.partner_id == current_user.id)
    ).order_by(Order.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


# --- ACTIONS ESCROW & WORKFLOW (MVP "Cafard") ---


@router.post("/{order_id}/pay")
async def pay_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Le client paie et bloque les fonds (Escrow)."""
    return await EscrowService.lock_funds(db, order_id, current_user.id)


@router.post("/{order_id}/finish")
async def finish_work(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """L'artisan déclare avoir fini. Démarre le timer 48h."""
    return await EscrowService.declare_job_finished(db, order_id, current_user.id)


@router.post("/{order_id}/validate")
async def validate_work(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Le client valide manuellement. Libération immédiate."""
    return await EscrowService.release_funds(db, order_id, trigger_source="CLIENT")

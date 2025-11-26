import asyncio
import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(__file__))

from app.db.session import AsyncSessionLocal
from app.models.order import Order, OrderStatus

async def create_test_order():
    async with AsyncSessionLocal() as db:
        order = Order(
            client_id=1,
            partner_id=2, 
            listing_id=1,
            total_amount=15000.0,
            status=OrderStatus.PENDING,
            problem_description="Mon √©vier fuit depuis ce matin, eau partout dans la cuisine"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        print('‚úÖ Commande cr√©√©e avec ID:', order.id)
        print('Ì≥ù Description:', order.problem_description)
        return order.id

if __name__ == "__main__":
    order_id = asyncio.run(create_test_order())
    print(f'Order ID: {order_id}')

# -*- coding: utf-8 -*-
import asyncio
import sys
import os

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
            problem_description="Mon evier fuit depuis ce matin, eau partout dans la cuisine"
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        print('SUCCESS: Commande creee avec ID:', order.id)
        return order.id

if __name__ == "__main__":
    order_id = asyncio.run(create_test_order())
    print('Order ID:', order_id)

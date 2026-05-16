from pydantic import BaseModel

from app.models.order import  OrderStatus

class OrderResponse(BaseModel):
    order_id: str
    status: OrderStatus
    total: float
    item_count: int

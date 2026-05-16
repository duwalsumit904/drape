import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy import ForeignKey, Enum, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum

class OrderStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    shipped   = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id            : Mapped[str]         = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id       : Mapped[str]         = mapped_column(String, ForeignKey("users.id"), nullable=False)
    status        : Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    total         : Mapped[float]       = mapped_column(Float, nullable=False)
    created_at    : Mapped[datetime]    = mapped_column(DateTime, default=datetime.utcnow)

    # relationships
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id                  : Mapped[str]   = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id            : Mapped[str]   = mapped_column(String, ForeignKey("orders.id"), nullable=False)
    variant_id          : Mapped[str]   = mapped_column(String, ForeignKey("product_variants.id"), nullable=False)
    quantity            : Mapped[int]   = mapped_column(Integer, nullable=False)
    unit_price_at_purchase: Mapped[float] = mapped_column(Float, nullable=False)

    # relationships
    order  : Mapped["Order"]          = relationship("Order", back_populates="items")
    variant: Mapped["ProductVariant"] = relationship("ProductVariant")
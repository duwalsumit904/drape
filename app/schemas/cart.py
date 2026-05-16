from pydantic import BaseModel, field_validator


class AddToCart(BaseModel):
    variant_id: str
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v

class UpdateCart(BaseModel):
    quantity: int
    field_validator("quantity")

    @classmethod
    def quantity_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Quantity must be at least 1")
        return v

    
from pydantic import BaseModel


class Product(BaseModel):
    id: int
    name: str
    description: str
    image: str
    price: float
    embedding: list[float] | None

    def __hash__(self):
        return hash(self.id)


class ProductWithSimilarity(Product):
    similarity: float

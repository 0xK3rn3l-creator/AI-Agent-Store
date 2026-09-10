import strawberry
from typing import List
from sqlalchemy.orm import Session
from api.models.database import SessionLocal, Supplier, Product

# Визначаємо типи GraphQL
@strawberry.type
class ProductType:
    id: int
    name: str
    sku: str
    price: float

@strawberry.type
class SupplierType:
    id: int
    name: str
    phone: str
    email: str
    
    @strawberry.field
    def products(self) -> List[ProductType]:
        with SessionLocal() as db:
            products = db.query(Product).filter(Product.supplier_id == self.id).all()
            return [ProductType(id=p.id, name=p.name, sku=p.sku, price=p.price) for p in products]

@strawberry.type
class Query:
    @strawberry.field
    def suppliers(self) -> List[SupplierType]:
        with SessionLocal() as db:
            suppliers = db.query(Supplier).all()
            return [SupplierType(id=s.id, name=s.name, phone=s.phone, email=s.email) for s in suppliers]

    @strawberry.field
    def products(self) -> List[ProductType]:
        with SessionLocal() as db:
            products = db.query(Product).all()
            return [ProductType(id=p.id, name=p.name, sku=p.sku, price=p.price) for p in products]

schema = strawberry.Schema(query=Query)

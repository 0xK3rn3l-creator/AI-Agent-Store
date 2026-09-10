from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from api.models.database import SessionLocal, Supplier, Product, PurchaseOrder, OrderItem
from api.routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(dependencies=[Depends(get_current_user)])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SupplierCreate(BaseModel): name: str; phone: str; email: str
class ProductCreate(BaseModel): supplier_id: int; name: str; sku: str; price: float
class OrderItemCreate(BaseModel): product_id: int; quantity: int; buy_price: float

@router.get("/suppliers/search")
def search_suppliers(query: str, db: Session = Depends(get_db)):
    return db.query(Supplier).filter(Supplier.name.ilike(f"%{query}%")).all()

@router.post("/suppliers")
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):
    db_obj = Supplier(**data.model_dump())
    db.add(db_obj); db.commit(); db.refresh(db_obj)
    return {"supplier_id": db_obj.id}

@router.post("/products")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    db_obj = Product(**data.model_dump())
    try:
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Продукт із артикулом (SKU) '{data.sku}' вже існує."
        )
    return {"product_id": db_obj.id}

@router.post("/orders")
def create_purchase_order(supplier_id: int, db: Session = Depends(get_db)):
    db_obj = PurchaseOrder(supplier_id=supplier_id)
    db.add(db_obj); db.commit(); db.refresh(db_obj)
    return {"order_id": db_obj.id}

@router.post("/orders/{order_id}/items")
def add_item_to_order(order_id: int, data: OrderItemCreate, db: Session = Depends(get_db)):
    db_obj = OrderItem(order_id=order_id, **data.model_dump())
    db.add(db_obj); db.commit()
    return {"status": "success"}

@router.get("/orders/{order_id}/summary")
def get_order_summary(order_id: int, db: Session = Depends(get_db)):
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    return {
        "order_id": order.id,
        "supplier": order.supplier.name,
        "items": [{"product": i.product.name, "qty": i.quantity, "price": i.buy_price} for i in order.items],
        "total": sum(i.quantity * i.buy_price for i in order.items)
    }

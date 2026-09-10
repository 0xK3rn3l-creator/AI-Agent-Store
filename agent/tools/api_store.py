import requests
from agent.tracing import log_step
from agent.guardrails import assert_tool_allowed

BASE_URL = "http://localhost:8000"
TOKEN = None

def _get_headers():
    global TOKEN
    if not TOKEN:
        resp = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin"})
        TOKEN = resp.json()["access_token"]
    return {"Authorization": f"Bearer {TOKEN}"}

def _wrap_tool(func):
    """Декоратор для логування та перевірки guardrails"""
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        assert_tool_allowed(tool_name)
        log_step(f"tool_call_{tool_name}", {"args": args, "kwargs": kwargs})
        try:
            result = func(*args, **kwargs)
            log_step(f"tool_result_{tool_name}", {"result": result})
            return result
        except Exception as e:
            log_step(f"tool_error_{tool_name}", {"error": str(e)})
            return {"error": str(e)}
    return wrapper

@_wrap_tool
def search_suppliers(query: str):
    return requests.get(f"{BASE_URL}/suppliers/search", params={"query": query}, headers=_get_headers()).json()

@_wrap_tool
def create_supplier(name: str, phone: str, email: str):
    return requests.post(f"{BASE_URL}/suppliers", json={"name": name, "phone": phone, "email": email}, headers=_get_headers()).json()

@_wrap_tool
def create_product(supplier_id: int, name: str, sku: str, price: float):
    return requests.post(f"{BASE_URL}/products", json={"supplier_id": supplier_id, "name": name, "sku": sku, "price": price}, headers=_get_headers()).json()

@_wrap_tool
def create_purchase_order(supplier_id: int):
    return requests.post(f"{BASE_URL}/orders", params={"supplier_id": supplier_id}, headers=_get_headers()).json()

@_wrap_tool
def add_item_to_order(order_id: int, product_id: int, quantity: int, buy_price: float):
    return requests.post(f"{BASE_URL}/orders/{order_id}/items", json={"product_id": product_id, "quantity": quantity, "buy_price": buy_price}, headers=_get_headers()).json()

@_wrap_tool
def get_order_summary(order_id: int):
    return requests.get(f"{BASE_URL}/orders/{order_id}/summary", headers=_get_headers()).json()

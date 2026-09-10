import os
import json
from agent.tools import api_store
from agent.guardrails import max_steps_instruction, MAX_STEPS
from agent.tracing import log_step

# Спільний мапінг інструментів
AVAILABLE_TOOLS = {
    "search_suppliers": api_store.search_suppliers,
    "create_supplier": api_store.create_supplier,
    "create_product": api_store.create_product,
    "create_purchase_order": api_store.create_purchase_order,
    "add_item_to_order": api_store.add_item_to_order,
    "get_order_summary": api_store.get_order_summary,
}

# ==========================================================
# ЛОГІКА ДЛЯ GEMINI
# ==========================================================
def search_suppliers_gemini(query: str = ""):  
    return api_store.search_suppliers(query=query)

def create_supplier_gemini(name: str, phone: str, email: str):  
    return api_store.create_supplier(name=name, phone=phone, email=email)

def create_product_gemini(supplier_id: int, name: str, sku: str, price: float):  
    return api_store.create_product(supplier_id=supplier_id, name=name, sku=sku, price=price)

def create_purchase_order_gemini(supplier_id: int):  
    return api_store.create_purchase_order(supplier_id=supplier_id)

def add_item_to_order_gemini(order_id: int, product_id: int, quantity: int, buy_price: float):  
    return api_store.add_item_to_order(order_id=order_id, product_id=product_id, quantity=quantity, buy_price=buy_price)

def get_order_summary_gemini(order_id: int):  
    return api_store.get_order_summary(order_id=order_id)

GEMINI_TOOLS = [
    search_suppliers_gemini,
    create_supplier_gemini,
    create_product_gemini,
    create_purchase_order_gemini,
    add_item_to_order_gemini,
    get_order_summary_gemini,
]

def run_gemini_turn(chat, initial_message):
    from google.genai import types
    from google.genai.errors import ClientError
    
    step_count = 0
    log_step("agent_start", {"prompt": initial_message, "provider": "gemini"})
    current_message = initial_message
    
    while step_count < MAX_STEPS:
        step_count += 1
        try:
            response = chat.send_message(current_message)
        except ClientError as e:
            if e.code == 429:
                print("\n❌ Ліміт запитів вичерпано (429 Resource Exhausted). Будь ласка, зачекайте хвилину.")
            else:
                print(f"\n❌ Помилка клієнта Gemini API: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Непередбачувана помилка при зверненні до моделі: {e}")
            return False
            
        if response.function_calls:
            function_responses = []
            for function_call in response.function_calls:
                func_name = function_call.name.replace("_gemini", "")
                args = function_call.args
                
                print(f"🛠 Виклик інструменту: {func_name}({args})")
                
                if func_name in AVAILABLE_TOOLS:
                    try:
                        result = AVAILABLE_TOOLS[func_name](**args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": "Unknown tool"}
                
                function_responses.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={"result": result}
                    )
                )
            current_message = function_responses
        else:
            final_text = response.text
            log_step("agent_finish", {"final_answer": final_text})
            print("\n🤖 Агент:", final_text)
            return True
            
    print("❌ Досягнуто ліміт кроків для цього запиту.")
    return True


# ==========================================================
# ЛОГІКА ДЛЯ OPENAI
# ==========================================================
OPENAI_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_suppliers",
            "description": "Search for suppliers by query string",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_supplier",
            "description": "Create a new supplier",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["name", "phone", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_product",
            "description": "Create a new product for a supplier",
            "parameters": {
                "type": "object",
                "properties": {
                    "supplier_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "sku": {"type": "string"},
                    "price": {"type": "number"},
                },
                "required": ["supplier_id", "name", "sku", "price"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_purchase_order",
            "description": "Create a new purchase order",
            "parameters": {
                "type": "object",
                "properties": {"supplier_id": {"type": "integer"}},
                "required": ["supplier_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_item_to_order",
            "description": "Add an item to a purchase order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"},
                    "product_id": {"type": "integer"},
                    "quantity": {"type": "integer"},
                    "buy_price": {"type": "number"},
                },
                "required": ["order_id", "product_id", "quantity", "buy_price"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_summary",
            "description": "Get order summary details",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
            },
        },
    },
]

def run_openai_turn(client, messages, initial_message):
    messages.append({"role": "user", "content": initial_message})
    step_count = 0
    log_step("agent_start", {"prompt": initial_message, "provider": "openai"})

    while step_count < MAX_STEPS:
        step_count += 1
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=OPENAI_TOOLS_SCHEMA,
                tool_choice="auto",
            )
        except Exception as e:
            print(f"\n❌ Помилка OpenAI API: {e}")
            return False

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                print(f"🛠 Виклик інструменту: {func_name}({args})")
                
                if func_name in AVAILABLE_TOOLS:
                    try:
                        result = AVAILABLE_TOOLS[func_name](**args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": "Unknown tool"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
        else:
            final_text = response_message.content
            log_step("agent_finish", {"final_answer": final_text})
            print("\n🤖 Агент:", final_text)
            return True

    print("❌ Досягнуто ліміт кроків для цього запиту.")
    return True


# ==========================================================
# ГОЛОВНИЙ ЗАПУСК
# ==========================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 СТАРТ АГЕНТА СКЛАДУ")
    print("=" * 60)

    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    provider = None
    client = None
    chat_or_messages = None

    system_instruction_text = (
        "Ти — інтелектуальний AI-асистент CRM системи управління складом. "
        "Твоє завдання — послідовно виконувати запити користувача, викликаючи відповідні інструменти. "
        f"{max_steps_instruction()}"
    )

    if openai_key:
        print("💡 Виявлено ключ OpenAI. Працюємо через OpenAI API (gpt-4o-mini).")
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        provider = "openai"
        chat_or_messages = [{"role": "system", "content": system_instruction_text}]
        
    elif gemini_key:
        print("💡 Виявлено ключ Google Gemini. Працюємо через Gemini API (gemini-2.5-flash).")
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gemini_key)
        provider = "gemini"
        chat_or_messages = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_text,
                tools=GEMINI_TOOLS,
                temperature=0.2,
            )
        )
    else:
        print("❌ Не знайдено жодного API-ключа! Встановіть OPENAI_API_KEY або GEMINI_API_KEY.")
        exit(1)

    # Вибір режиму: виконати тест чи одразу перейти до чату
    choice = input("\nБажаєш виконати стандартне тестове завдання перед запуском чату? (y/n, за замовчуванням y): ").strip().lower()
    
    if choice != 'n':
        test_prompt = (
            "Зареєструй нового постачальника 'Молочний Гай' (contact: moloko@example.com, phone: +380991112233). "
            "Додай до нього новий товар 'Сметану 20%' (SKU: SMT-20, ціна: 45 грн). "
            "Створи нову поставку від цього постачальника і додай туди 100 банок цієї сметани (ціна закупівлі 35 грн). "
            "Наприкінці покажи мені підсумок поставки."
        )
        print("\n📌 Виконую тестове завдання...")
        if provider == "openai":
            success = run_openai_turn(client, chat_or_messages, test_prompt)
        else:
            success = run_gemini_turn(chat_or_messages, test_prompt)
            
        if not success:
            exit(1)

    print("\n" + "=" * 60)
    print("💬 ІНТЕРАКТИВНИЙ РЕЖИМ УВІМКНЕНО")
    print("Напиши своє питання або команду. Для виходу введи 'exit', 'вихід' або 'quit'.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nТи: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Вихід...")
            break

        if user_input.lower() in ["exit", "вихід", "quit", "q"]:
            print("👋 До зустрічі!")
            break
            
        if not user_input:
            continue

        if provider == "openai":
            run_openai_turn(client, chat_or_messages, user_input)
        else:
            run_gemini_turn(chat_or_messages, user_input)

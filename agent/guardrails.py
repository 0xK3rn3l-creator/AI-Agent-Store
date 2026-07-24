from agent.tracing import log_step

MAX_STEPS = 20
ALLOWED_TOOLS = [
    "search_suppliers", "create_supplier", "create_product",
    "create_purchase_order", "add_item_to_order", "get_order_summary"
]

def max_steps_instruction() -> str:
    return f"У тебе є максимум {MAX_STEPS} кроків (tool calls) для виконання завдання. Плануй свої дії ефективно."

def assert_tool_allowed(tool_name: str):
    if tool_name not in ALLOWED_TOOLS:
        log_step("guardrail_block", {"attempted_tool": tool_name})
        raise ValueError(f"Tool {tool_name} is not allowed. Allowed tools: {ALLOWED_TOOLS}")

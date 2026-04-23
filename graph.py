from langgraph.graph import StateGraph, END
from state import AgentState

# Import Routers
from routers.router_main import classify_domain
from routers.router_medical import analyze_medical_intent
from routers.router_weather import analyze_weather_intent
from routers.router_search import analyze_search_intent
from routers.router_image import analyze_image_intent

# Import Tools
from tools.medical import (
    check_schedule,
    book_appointment,
    get_clinic_info,
    get_doctor_list,
    get_doctor_schedule_list
)
from tools.weather import execute_weather
from tools.search import execute_search
from tools.image import generate_image

workflow = StateGraph(AgentState)

# 1. Register Router Nodes
workflow.add_node("classifier", classify_domain)
workflow.add_node("router_medical", analyze_medical_intent)
workflow.add_node("router_weather", analyze_weather_intent)
workflow.add_node("router_search", analyze_search_intent)
workflow.add_node("router_image", analyze_image_intent)

# 2. Register Medical Tool Nodes
workflow.add_node("check_schedule", check_schedule)
workflow.add_node("book_appointment", book_appointment)
workflow.add_node("get_clinic_info", get_clinic_info)
workflow.add_node("get_doctor_list", get_doctor_list)
workflow.add_node("get_doctor_schedule_list", get_doctor_schedule_list)

# 3. Register General Tool Nodes
workflow.add_node("weather", execute_weather)
workflow.add_node("search", execute_search)
workflow.add_node("image", generate_image)

workflow.set_entry_point("classifier")

def route_domain(state: AgentState):
    domain = state.get("domain")

    if domain == "medical":
        return "router_medical"
    elif domain == "weather":
        return "router_weather"
    elif domain == "search":
        return "router_search"
    elif domain == "image":
        return "router_image"
    else:
        return END


def route_medical(state: AgentState):
    action = state.get("action")

    allowed_actions = [
        "check_schedule",
        "book_appointment",
        "get_clinic_info",
        "get_doctor_list",
        "get_doctor_schedule_list",
    ]
    if action in allowed_actions:
        return action
    return END


def route_weather(state: AgentState):
    if state.get("action") == "get_weather":
        return "weather"
    return END


def route_search(state: AgentState):
    if state.get("action") == "web_search":
        return "search"
    return END


def route_image(state: AgentState):
    if state.get("action") == "generate_image":
        return "image"
    return END

workflow.add_conditional_edges("classifier", route_domain)

workflow.add_conditional_edges("router_medical", route_medical)
workflow.add_conditional_edges("router_weather", route_weather)
workflow.add_conditional_edges("router_search", route_search)
workflow.add_conditional_edges("router_image", route_image)

tool_nodes = [
    "check_schedule",
    "book_appointment",
    "get_clinic_info",
    "get_doctor_list",
    "get_doctor_schedule_list",
    "weather",
    "search",
    "image",
]

for node in tool_nodes:
    workflow.add_edge(node, END)

app_graph = workflow.compile()
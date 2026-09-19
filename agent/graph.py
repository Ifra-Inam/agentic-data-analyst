from .agent_state import AgentState
from .nodes.retrieve_documentation import retrieve_documentation
from .nodes.get_schema import get_schema
from .nodes.generate_sql import generate_sql
from .nodes.validate_sql import validate_sql
from .nodes.execute_sql import execute_sql
from .nodes.check_result import check_result    
from .nodes.analyze_result import analyze_result
from .nodes.create_chart import create_chart

from langgraph.graph import StateGraph, START, END

graph = StateGraph(AgentState)

graph.add_node("rag", retrieve_documentation)
graph.add_node("schema", get_schema)
graph.add_node("sql", generate_sql)
graph.add_node("validate", validate_sql)
graph.add_node("execute", execute_sql)
graph.add_node("check", check_result)
graph.add_node("analyze", analyze_result)
graph.add_node("chart", create_chart)


graph.add_edge(START, "rag")

graph.add_conditional_edges("rag", 
                                lambda state: state["route_after_rag"],
                                {
                                    "END": END,
                                    "SCHEMA": "schema"
                                }
                            )
graph.add_edge("schema", "sql")
graph.add_edge("sql", "validate")
graph.add_conditional_edges("validate", 
                                lambda state: state["sql_valid"],
                                {
                                    True: "execute",
                                    False: "sql"
                                }
                            )
graph.add_edge("execute", "check")
graph.add_conditional_edges("check",
                                lambda state: state["result_valid"],
                                {
                                    True: "analyze",
                                    False: "sql"
                                }
                            )
graph.add_conditional_edges("analyze",
                            lambda state: state["chart_needed"],
                            {
                                "CHART": "chart",
                                "NO_CHART": END
                            })
graph.add_edge("chart", END)

def app():
    return graph
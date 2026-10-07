from typing import TypedDict, Any

class AgentState(TypedDict):
    user_query: str
    doc_info: str
    route_after_rag: str
    schema_info: dict[str, dict[str, str]]
    generated_sql: str
    sql_valid: bool
    result: list[dict[str, Any]]
    sql_error: str
    result_valid: bool
    chart_needed: bool
    chart_specs: dict[str, Any]
    chart: object
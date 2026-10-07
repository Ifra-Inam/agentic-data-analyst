from typing import TypedDict, Any

MAX_SQL_REVISIONS = 3

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
    revision_count: int
    retry_limit_reached: bool


def record_revision(state: AgentState) -> None:
    state["revision_count"] = state.get("revision_count", 0) + 1
    state["retry_limit_reached"] = state["revision_count"] >= MAX_SQL_REVISIONS
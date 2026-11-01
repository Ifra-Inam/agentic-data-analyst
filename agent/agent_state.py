from typing import TypedDict, Literal, Any
from pydantic import BaseModel, Field

MAX_SQL_ATTEMPTS = 3

class ChartSpecs(BaseModel):
    chart_type: Literal["scatter","line","bar","pie"]
    x: str
    y: str
    title: str

class SQLAttempt(TypedDict):
    sql: str
    stage: str
    reason: str

class SQLReview(BaseModel):
    valid: bool
    reason: str = Field(description="A concise, actionable explanation for the verdict.")

class AgentState(TypedDict):
    user_query: str
    doc_info: str
    conversation_history: str
    resolved_query: str
    route_after_rag: str
    schema_info: dict[str, dict[str, str]]
    generated_sql: str
    sql_attempts: int
    sql_attempt_history: list[SQLAttempt]
    sql_valid: bool
    result: list[dict[str, Any]]
    sql_error: str
    result_valid: bool
    chart_needed: bool
    chart_specs: dict[str, Any]
    chart: object

def record_sql_failure(state: AgentState, stage: str, reason: str) -> None:
    history = state.get("sql_attempt_history")
    if history is None:
        history = []
        state["sql_attempt_history"] = history

    history.append({
        "sql": state["generated_sql"],
        "stage": stage,
        "reason": reason,
    })
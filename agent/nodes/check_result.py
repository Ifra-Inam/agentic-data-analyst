from ..agent_state import AgentState, SQLReview, record_sql_failure
from ..llm import get_llm

def check_result(state:AgentState) -> AgentState:
    """This node checks whether the result answers the user's question"""

    if state.get("sql_error"):
        state["result_valid"] = False
        record_sql_failure(state, "execution", state["sql_error"])
        return state

    llm = get_llm()

    check_result_prompt = f'''
        Determine whether the SQL result contains the database facts or calculations needed to answer the data-queryable part of the user's request.

        User's Question:
        {state.get("resolved_query") or state["user_query"]}

        Business Context:
        {state["doc_info"]}

        Database Schema:
        {state["schema_info"]}

        Generated SQL:
        {state["generated_sql"]}

        SQL Error:
        {state.get("sql_error")}

        Query Result:
        {state["result"]}

        Check whether the result contains the requested values, facts, or calculation and is usable 
        as evidence for a later answer. Do not require the result itself to interpret or evaluate the 
        data (for example, decide whether revenue means the company is doing well). A partial preview 
        is acceptable only when it still contains the information needed for the requested data answer.
        
        Return a structured verdict with:
        - valid: whether the result contains the needed database information
        - reason: a concise, actionable explanation; empty when valid
    '''
    print("CHECK PROMPT CHARACTERS:", len(check_result_prompt))
    print("RESULT ROWS:", len(state["result"]))

    structured_llm = llm.with_structured_output(SQLReview, method="json_schema", strict=True)
    check_result = structured_llm.invoke(check_result_prompt)
    print(check_result.valid)
    print(check_result.reason)
    
    state["result_valid"] = check_result.valid
    if not check_result.valid:
        record_sql_failure(state, "result_check", check_result.reason)

    return state

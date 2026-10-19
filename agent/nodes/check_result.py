from ..agent_state import AgentState
from ..llm import get_llm

def check_result(state:AgentState) -> AgentState:
    """This node checks whether the result answers the user's question"""

    if state.get("sql_error"):
        state["result_valid"] = False
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
        
        Return exactly one:
            VALID: The result contains the needed database information.
            REDO: The query failed, returned an unusable result, or omitted the needed database information.
    '''
    print("CHECK PROMPT CHARACTERS:", len(check_result_prompt))
    print("RESULT ROWS:", len(state["result"]))

    check_result = llm.invoke(check_result_prompt).content.strip()

    print(check_result)
    if check_result == "VALID":
        state["result_valid"] = True
    else:
        state["result_valid"] = False

    return state

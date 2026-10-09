from ..agent_state import AgentState
from ..llm import get_llm

def check_result(state:AgentState) -> AgentState:
    """This node checks whether the result answers the user's question"""

    if state.get("sql_error"):
        state["result_valid"] = False
        return state

    if state.get("result_truncated"):
        state["result_valid"] = True
        return state

    llm = get_llm()

    check_result_prompt = f'''
        Determine whether the SQL query successfully answered the user's question.

        User's Question:
        {state["user_query"]}

        Generated SQL:
        {state["generated_sql"]}

        SQL Error:
        {state.get("sql_error")}

        Query Result:
        {state["result"]}

        Return exactly one:
            VALID: The result correctly answers the user's question.
            REDO: The query failed, returned an error, returned an unusable result, or does not answer the user's question.
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

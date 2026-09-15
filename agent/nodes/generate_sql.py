from ..agent_state import AgentState
from ..llm import get_llm

import re

def clean_sql(sql: str) -> str:
    sql = sql.strip()

    # Remove ```sql ... ``` or ``` ... ```
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*```$", "", sql)

    return sql.strip()

def generate_sql(state:AgentState) -> AgentState:
    """This node generates the appropriate SQL."""

    generate_sql_prompt=f'''
        Generate SQL provided these parameters. Return only the SQL query. Do not use Markdown code fences.
            User's Question: {state["user_query"]},
            Documentation: {state["doc_info"]},
            Database Schema: {state["schema_info"]}
    '''

    llm = get_llm()
    generated_sql = llm.invoke(generate_sql_prompt).content
    state["generated_sql"] = clean_sql(generated_sql)
    print(state["generated_sql"])
    return state

    
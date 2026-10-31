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
            User's Question: {state.get("resolved_query") or state["user_query"]},
            Documentation: {state["doc_info"]},
            Database Schema: {state["schema_info"]}

        Result-size and ordering rules:
        - Ranking or comparison questions with no stated count: return the top 10 rows, ordered so the best match comes first.
        - Singular wording ("which product has the highest...") returns 1 row; plural or "top"/"best" with no count returns 10.
        - If the user gives a number, return that many rows, up to a maximum of 200.
        - Use up to 200 rows only when the user explicitly asks for a broad or complete row-level listing. Never use 200 as the default.
        - Never limit aggregate calculations (totals, averages, counts). For grouped aggregates, apply the top-10 default only if the question is a ranking; otherwise return all groups needed to answer it.
    '''

    llm = get_llm()
    generated_sql = llm.invoke(generate_sql_prompt).content
    state["generated_sql"] = clean_sql(generated_sql)
    print(state["generated_sql"])
    return state

    
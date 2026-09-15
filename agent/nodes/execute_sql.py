from ..agent_state import AgentState
from database.connection import get_connection

def execute_sql(state:AgentState)->AgentState:
    """This node executes the generated SQL."""

    connection = get_connection()
    cursor = connection.cursor()

    query = state["generated_sql"]
    cursor.execute(query)
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    state["result"] = [
        dict(zip(columns, row))
        for row in rows
    ]

    cursor.close()
    connection.close()

    # state["result"] = result     

    return state
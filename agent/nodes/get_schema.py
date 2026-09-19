from ..agent_state import AgentState
from database.connection import get_connection 

def get_schema(state:AgentState) -> AgentState:
    """This node retrieves the database schema (tables, columns, data types)."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # limit schema to fit within token limit
        cursor.execute("""
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'hr', 'pe', 'pu', 'pr', 'sa') 
            ORDER BY table_schema, table_name, ordinal_position;
        """)

        rows = cursor.fetchall()

        schema = {}

        for table_schema, table_name, column_name in rows:
            table = f"{table_schema}.{table_name}"
            if table not in schema:
                schema[table] = []

            schema[table].append({"column": column_name})        

    finally: 
        cursor.close()
        connection.close()

    state["schema_info"] = schema

    print("Schema characters:", len(str(state["schema_info"])))
    print("Documentation characters:", len(state["doc_info"]))

    return state
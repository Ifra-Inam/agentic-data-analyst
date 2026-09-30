import json
from ..agent_state import AgentState
from database.connection import get_connection 
from ..llm import get_llm

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

    relevant_schema_prompt = f"""
        Retrieve only the database schema relevant to answering the user's question.

        User question:
        {state["user_query"]}

        Full database schema:
        {schema}

        Return ONLY the relevant tables and columns needed to answer the user's question.

        The output must use exactly the same structure as the full database schema:

        {{
            "table_schema.table_name": [
                {{"column": "column_name"}},
                {{"column": "column_name"}}
            ]
        }}

        Rules:
        - Each top-level key must be in the format "table_schema.table_name".
        - Each value must be a list of dictionaries.
        - Each dictionary must contain exactly one key, "column", whose value is the column name.
        - Include only tables and columns relevant to answering the user's question.
        - Include columns needed to join relevant tables.
        - Do not invent tables or columns.
        - Do not include unrelated tables or columns.
        - Return valid JSON only.
    """

    llm = get_llm()
    response = llm.invoke(relevant_schema_prompt).content.strip()
    relavent_schema = json.loads(response)
    print(response)

    state["schema_info"] = relavent_schema

    print("Schema characters:", len(str(state["schema_info"])))
    print("Documentation characters:", len(state["doc_info"]))

    return state
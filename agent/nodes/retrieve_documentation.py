import json
import re
from ..agent_state import AgentState
from ..llm import get_llm
from ..retrieval_initialization import retriever

def retrieve_documentation(state:AgentState) -> AgentState:
    """This node retrieves relavent business context from internal documentation to help answer the user's question."""

    llm = get_llm()

    original_question = state["user_query"]
    history = state["conversation_history"]

    retrieval_query = f'''
    Recent conversation:
    {history}
        
    Current question:
    {original_question}
    '''

    docs = retriever.invoke(retrieval_query)

    if not docs:
        state["doc_info"] = "No relavent information found."

    else:
        results = []

        for i, doc in enumerate(docs):
            results.append(f"Document {i+1}:\n{doc.page_content}")

        state["doc_info"] = "\n\n".join(results)
        print(state["doc_info"])

    route_prompt = f'''
        You are part of a conversational data analyst.

        Recent conversation:
        {history}

        Current user question:
        {original_question}

        Retrieved business documentation:
        {state["doc_info"]}

        Tasks:
        1. Rewrite the current question as a standalone question, using the conversation history when necessary.
        2. Decide whether the question requires querying the database.

        Rules:
        - Resolve follow-ups such as "How about 2025?" using the previous conversation.
        - Preserve the original metric, filters, and intent.
        - If the question is already standalone, preserve its meaning.
        - Do not invent missing details.
        - Return END if the question can be sufficiently answered using the business documentation alone.
        - Return SCHEMA if database records or calculations are needed.
        - If the question is ambiguous, do not invent an interpretation.

        Return valid JSON only, using this exact structure:
        {{
            "resolved_query": "<the current question rewritten as a standalone question>",
            "route": "END"
        }}

        The route must be exactly END or SCHEMA.
    '''

    response = llm.invoke(route_prompt).content.strip()

    if response.startswith("```"):
        response = re.sub(r"^```(?:json)?\s*", "", response, flags=re.IGNORECASE)
        response = re.sub(r"\s*```$", "", response)

    try:
        decision = json.loads(response)
        resolved_query = decision["resolved_query"]
        route = decision["route"]

        if not isinstance(resolved_query, str) or not resolved_query.strip():
            raise ValueError("Invalid resolved_query")

        if route not in {"END", "SCHEMA"}:
            raise ValueError("Invalid route")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid routing response from LLM: {response}"
        ) from exc

    state["resolved_query"] = decision["resolved_query"]
    state["route_after_rag"] = decision["route"]

    print(state["resolved_query"])
    print(state["route_after_rag"])
    
    if state["route_after_rag"] == "END":

            answer_prompt = f'''
                Answer the user's question using the documentation below.

                User's Question: {state.get("resolved_query") or state["user_query"]}
                Documentation: {state["doc_info"]}
            '''

            state["result"] = llm.invoke(answer_prompt).content

    return state
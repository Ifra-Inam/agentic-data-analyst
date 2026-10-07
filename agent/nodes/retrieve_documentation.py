from ..agent_state import AgentState
from ..llm import get_llm
from ..retrieval_initialization import retriever

def retrieve_documentation(state:AgentState) -> AgentState:
    """This node retrieves relavent business context from internal documentation to help answer the user's question."""

    docs = retriever.invoke(state["user_query"])

    if not docs:
        state["doc_info"] = "No relavent information found."

    else:
        results = []

        for i, doc in enumerate(docs):
            results.append(f"Document {i+1}:\n{doc.page_content}")

        state["doc_info"] = "\n\n".join(results)
        print(state["doc_info"])

    route_prompt = f'''
        Determine whether the user's question requires querying the database to answer.
        
        User's Question: {state["user_query"]}
        Business Context: {state["doc_info"]}

        Your response MUST be exactly ONE of these two words:
        END
        SCHEMA
        
        Rules:
        - END if the question can sufficiently be answered using the business context. 
        - SCHEMA if the question reqiures database information.
    '''

    llm = get_llm()

    state["route_after_rag"] = llm.invoke(route_prompt).content.strip()

    print(state["route_after_rag"])
    if state["route_after_rag"] == "END":

            answer_prompt = f'''
                Answer the user's question using the documentation below.

                User's Question: {state["user_query"]}
                Documentation: {state["doc_info"]}
            '''

            state["result"] = llm.invoke(answer_prompt).content

    return state
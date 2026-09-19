from ..agent_state import AgentState
from ..llm import get_llm

# 1. load documentation pages into a list of Document objects 

from langchain_core.documents import Document
from pathlib import Path

DOC_PATHS = [
    "business_definitions.md",
    "company_policies.md",
    "database_documentation.md",
    "metric_definitions.md",
]

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"

def load_docs(doc_paths: list[str] | None = None) -> list[Document]:
    """Fetch documentation pages as Documents."""
    paths = doc_paths or DOC_PATHS
    docs: list[Document] = []
    for path in paths:
        file_path = KNOWLEDGE_DIR / path
        try:
            content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError: 
            print(f"File not found: {file_path}")
            continue
        docs.append(
            Document(page_content=content, metadata={"source": str(file_path)})
        )
    return docs

docs = load_docs(DOC_PATHS)
print(f"Loaded {len(docs)} documentation pages.")

# 2. split the Document objects into chunks

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)
print(f"Split documentation into {len(all_splits)} chunks.")

# 3. select an embedding model, then embed and store the chunks into a vector store

from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="adeventure_works_collection",
    embedding_function=embeddings,
)

vector_store.add_documents(documents=all_splits)
print(f"Indexed {len(all_splits)} chunks.")

# 4. from the vector store, retrieve the k most similar chunks to the user's question

retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})

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

    route_prompt = f'''
        Determine whether the user's question requires querying the database to answer.
        
        User's Question: {state["user_query"]}
        Business Context: {state["doc_info"]}

        Return exactly one:
            END: The question can sufficiently be answered using the business context. 
            SCHEMA: The question reqiures database information.
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
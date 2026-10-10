import streamlit as st # to show the retrieval initialization progress on the ui
import os

# 1. load documentation pages into a list of Document objects 

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pathlib import Path

DOC_PATHS = [
    "business_definitions.md",
    "company_policies.md",
    "database_documentation.md",
    "metric_definitions.md",
]

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"

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

status = st.status("Loading documentation...", expanded=True)
docs = load_docs(DOC_PATHS)
print(f"Loaded {len(docs)} documentation pages.")
status.write(f"Loaded {len(docs)} documentation pages.")

# 2. split the Document objects into chunks

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
status.update(label="Chunking documentation...")
all_splits = text_splitter.split_documents(docs)
print(f"Split documentation into {len(all_splits)} chunks.")
status.write(f"Split documentation into {len(all_splits)} chunks.")

# 3. select an embedding model, then embed and store the chunks into a vector store

class FastEmbedAdapter(Embeddings):
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [embedding.tolist() for embedding in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self.model.query_embed(text)).tolist()


embedding_provider = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower()
if embedding_provider == "ollama":
    from langchain_ollama import OllamaEmbeddings
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
elif embedding_provider == "fastembed":
    embeddings = FastEmbedAdapter(
        model_name=os.getenv("FASTEMBED_MODEL", "BAAI/bge-small-en-v1.5")
    )
else:
    raise ValueError(
        "EMBEDDING_PROVIDER must be either 'ollama' or 'fastembed'."
    )

from langchain_chroma import Chroma

vector_store = Chroma(
    collection_name="adeventure_works_collection",
    embedding_function=embeddings,
)

status.update(label="Indexing documentation chunks...")
vector_store.add_documents(documents=all_splits)
print(f"Indexed {len(all_splits)} chunks.")
status.write(f"Indexed {len(all_splits)} chunks.")

# 4. from the vector store, retrieve the k most similar chunks to the user's question

retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 2})
status.update(label="Documentation search is ready.", state="complete", expanded=False)
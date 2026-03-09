from langchain.tools import tool
from pydantic import BaseModel, Field
import chromadb
from pathlib import Path
from dotenv import load_dotenv
import os

from langchain_openai import OpenAIEmbeddings

# --- load secrets robustly (05_src/.secrets) bcoz i was running into too many relative path issues 
ROOT_05_SRC = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_05_SRC / ".secrets")

CHROMA_DIR = ROOT_05_SRC / "assignment_chat" / "data" / "chroma"
COLLECTION_NAME = "parenting_corpus"

_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _client.get_collection(name=COLLECTION_NAME)

# --- IMPORTANT: query embeddings must match ingestion embeddings (1536 dims)
_query_embedder = OpenAIEmbeddings(
    model="text-embedding-3-small",
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_key="any value",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
)

class ParentingHit(BaseModel): # this is like a container for the relevant chunks retrieved from the parenting corpus in chromadb, with some metadata about source and title for better presentation in the chat interface
    source: str = Field(..., description="Where this came from (pdf/transcript).")
    title: str = Field(..., description="Document title or section.")
    text: str = Field(..., description="Relevant retrieved chunk.")

@tool
def parenting_search(query: str, n_results: int = 4) -> list[ParentingHit]:
    """
    Semantic search over the parenting corpus.
    Document embeddings are precomputed and stored in Chroma (1536 dims).
    At runtime we embed only the user query (also 1536 dims) via the course gateway.
    """
    qvec = _query_embedder.embed_query(query)

    res = _collection.query( #here is where chromadb does the vector search with the query embedding and returns the most relevant chunks from the parenting corpus
        query_embeddings=[qvec],
        n_results=n_results,
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    hits: list[ParentingHit] = []
    for doc, meta in zip(docs, metas):
        hits.append(
            ParentingHit(
                source=meta.get("source", "unknown"),
                title=meta.get("title", meta.get("section", "unknown")),
                text=doc,
            )
        )
    return hits
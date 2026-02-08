import os
import uuid
import requests
import json
from collections import defaultdict
from contextlib import asynccontextmanager

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct:free"
KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), "knowledge_base.txt")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
MAX_HISTORY = 10  # keep the last 10 messages (5 user + 5 assistant turns)

# ── In-memory conversation store ─────────────────────────────────────────────
# session_id -> list of {"role": ..., "content": ...}
conversations: dict[str, list[dict]] = defaultdict(list)

# ── 1. Chunking ──────────────────────────────────────────────────────────────

def load_and_chunk(file_path: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Read a text file and split it into overlapping chunks."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# ── 2. Vector store ──────────────────────────────────────────────────────────

collection: chromadb.Collection | None = None

def get_or_create_collection() -> chromadb.Collection:
    """Initialise ChromaDB with a default embedding function and ingest the
    knowledge base if the collection is empty."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.DefaultEmbeddingFunction()  # all-MiniLM-L6-v2
    coll = client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=ef,
    )

    if coll.count() == 0:
        print("Ingesting knowledge base …")
        chunks = load_and_chunk(KNOWLEDGE_FILE)
        coll.add(
            documents=chunks,
            ids=[f"chunk_{i}" for i in range(len(chunks))],
            metadatas=[{"source": "knowledge_base.txt"} for _ in chunks],
        )
        print(f"Ingested {len(chunks)} chunks.")
    return coll

# ── 3. Retrieval ─────────────────────────────────────────────────────────────

def retrieve(query: str, n_results: int = 3) -> str:
    """Return the top-n most relevant chunks as a single context string."""
    results = collection.query(query_texts=[query], n_results=n_results)
    docs = results["documents"][0]
    return "\n\n---\n\n".join(docs)

# ── 4. Generation (OpenRouter) ───────────────────────────────────────────────

def ask_llm(question: str, context: str, history: list[dict]) -> str:
    """Send the question + retrieved context + conversation history to the LLM."""
    system_prompt = (
        "You are a helpful assistant. Use ONLY the following context to answer "
        "the user's question. If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)  # prior conversation turns
    messages.append({"role": "user", "content": question})

    response = requests.post(
        url=OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({"model": MODEL, "messages": messages}),
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# ── 5. FastAPI app ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global collection
    collection = get_or_create_collection()
    print("RAG chatbot ready!")
    yield

app = FastAPI(title="RAG Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # omit to start a new conversation

class ChatResponse(BaseModel):
    answer: str
    session_id: str

# ── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    history = conversations[session_id]

    context = retrieve(req.message)
    answer = ask_llm(req.message, context, history)

    # Append both user message and assistant reply to history
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": answer})

    # Trim to last MAX_HISTORY messages
    if len(history) > MAX_HISTORY:
        conversations[session_id] = history[-MAX_HISTORY:]

    return ChatResponse(answer=answer, session_id=session_id)


@app.delete("/chat/{session_id}")
def clear_history(session_id: str):
    conversations.pop(session_id, None)
    return {"status": "cleared"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
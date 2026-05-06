from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

VECTOR_DB = {}

# Lazy-loaded to avoid ~80MB RAM usage at server startup
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def chunk_text(text, size=500, overlap=50):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return chunks


def add_to_vector_store(lecture_id, text):
    chunks = chunk_text(text)
    embeddings = get_embedding_model().encode(chunks)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    VECTOR_DB[lecture_id] = {
        "index": index,
        "chunks": chunks
    }


def retrieve_context(lecture_id, query="", top_k=3):
    data = VECTOR_DB.get(lecture_id)
    if not data:
        return []

    index = data["index"]
    chunks = data["chunks"]

    query_embedding = get_embedding_model().encode([query])
    _, indices = index.search(query_embedding, top_k)

    return [chunks[i] for i in indices[0]]

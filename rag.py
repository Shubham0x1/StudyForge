VECTOR_DB = {}


def chunk_text(text, size=500, overlap=50):
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+size])
        i += size - overlap
    return chunks


def add_to_vector_store(lecture_id, text):
    chunks = chunk_text(text)
    VECTOR_DB[lecture_id] = {"chunks": chunks}


def retrieve_context(lecture_id, query="", top_k=3):
    data = VECTOR_DB.get(lecture_id)
    if not data:
        return []
    return data["chunks"][:top_k]

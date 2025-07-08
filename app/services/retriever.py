from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.document_chunk import DocumentChunk
from sentence_transformers import SentenceTransformer
from app.config.config import settings

model = SentenceTransformer(settings.EMBEDDING_MODEL)

def search_pgvector(db, query, top_k= 5) -> list[dict]:
    query_embedding = model.encode([query])[0].tolist()

    query_vector_str = f"[{', '.join(map(str, query_embedding))}]"

    results = (
        db.query(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector_str))
        .limit(top_k)
        .all()
    )

    return [{"content": row.content} for row in results]

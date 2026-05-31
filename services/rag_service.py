import sqlite3
import json
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DB_PATH = "rag_database.db"
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_document(content: str):
    embedding = model.encode(content).tolist()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (content, embedding) VALUES (?, ?)",
        (content, json.dumps(embedding))
    )
    conn.commit()
    conn.close()

def search_similar(query: str, top_k: int = 5) -> list:
    query_embedding = np.array(model.encode(query))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content, embedding FROM documents")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    results = []
    for content, emb_json in rows:
        emb = np.array(json.loads(emb_json))
        similarity = np.dot(query_embedding, emb) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-9
        )
        results.append((similarity, content))

    results.sort(reverse=True)
    return [content for _, content in results[:top_k]]

def load_sample_documents():
    docs = [
        "Python — жоғары деңгейлі бағдарламалау тілі.",
        "Aiogram — Telegram боттарын жасауға арналған Python кітапханасы.",
        "Groq API — жылдам LLM inference платформасы.",
        "Ollama — локальды AI модельдерін іске қосуға арналған құрал.",
        "RAG — Retrieval Augmented Generation, деректер базасынан ақпарат алып LLM-ге береді.",
        "PostgreSQL — ашық бастапқы реляциялық деректер базасы.",
        "SQLite — жеңіл, файлға негізделген деректер базасы.",
        "Machine Learning — компьютерлерді деректерден үйренуге үйрету.",
        "KazNITU — Қазақстандағы техникалық университет.",
        "Telegram Bot API — боттарды Telegram-мен байланыстыратын API.",
    ]
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        for doc in docs:
            add_document(doc)
        logger.info(f"{len(docs)} документ қосылды.")
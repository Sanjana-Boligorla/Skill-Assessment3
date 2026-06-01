import os
import hashlib
from typing import List, Dict


def _get_backend() -> str:
    return "pinecone" if os.getenv("USE_PINECONE", "false").lower() == "true" else "chroma"


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def _make_id(text: str, prefix: str = "") -> str:
    return prefix + hashlib.md5(text.encode()).hexdigest()[:16]


class VectorStore:
    def __init__(self):
        self.backend = _get_backend()
        self._chroma_client = None
        self._chroma_collection = None
        self._pinecone_index = None
        self._oai_client = None
        self._initialized = False

    def _get_embedding(self, text: str) -> List[float]:
        if self._oai_client is None:
            from utils.llm_client import get_client
            self._oai_client = get_client()
        resp = self._oai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
        )
        return resp.data[0].embedding

    def _init_chroma(self):
        import chromadb
        self._chroma_client = chromadb.Client()
        try:
            self._chroma_collection = self._chroma_client.get_collection("product_strategy")
        except Exception:
            self._chroma_collection = self._chroma_client.create_collection("product_strategy")
        self._initialized = True

    def _init_pinecone(self):
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index_name = os.getenv("PINECONE_INDEX_NAME", "product-strategy")
        existing = [i.name for i in pc.list_indexes()]
        if index_name not in existing:
            pc.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
            )
        self._pinecone_index = pc.Index(index_name)
        self._initialized = True

    def initialize(self):
        if self._initialized:
            return
        if self.backend == "pinecone":
            try:
                self._init_pinecone()
            except Exception:
                self._init_chroma()
                self.backend = "chroma"
        else:
            self._init_chroma()

    def upsert_documents(self, documents: List[Dict]):
        self.initialize()
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            chunks = _chunk_text(text)
            if self.backend == "chroma":
                ids, embeddings, metas, texts = [], [], [], []
                for i, chunk in enumerate(chunks):
                    emb = self._get_embedding(chunk)
                    doc_id = _make_id(chunk, f"doc{i}_")
                    ids.append(doc_id)
                    embeddings.append(emb)
                    metas.append({**metadata, "chunk_index": i})
                    texts.append(chunk)
                if ids:
                    self._chroma_collection.upsert(
                        ids=ids, embeddings=embeddings, metadatas=metas, documents=texts
                    )
            else:
                vectors = []
                for i, chunk in enumerate(chunks):
                    emb = self._get_embedding(chunk)
                    doc_id = _make_id(chunk, f"doc{i}_")
                    vectors.append({"id": doc_id, "values": emb, "metadata": {**metadata, "text": chunk[:500]}})
                if vectors:
                    self._pinecone_index.upsert(vectors=vectors)

    def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
        self.initialize()
        emb = self._get_embedding(query_text)
        if self.backend == "chroma":
            results = self._chroma_collection.query(
                query_embeddings=[emb], n_results=min(top_k, self._chroma_collection.count() or 1)
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            return [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
        else:
            results = self._pinecone_index.query(vector=emb, top_k=top_k, include_metadata=True)
            return [{"text": m.metadata.get("text", ""), "metadata": m.metadata} for m in results.matches]

    def reset(self):
        if self.backend == "chroma" and self._chroma_client:
            try:
                self._chroma_client.delete_collection("product_strategy")
            except Exception:
                pass
            self._chroma_collection = self._chroma_client.create_collection("product_strategy")
        self._initialized = False


_store = VectorStore()


def get_vector_store() -> VectorStore:
    return _store

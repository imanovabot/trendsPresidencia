"""Almacenamiento de errores en Qdrant (búsqueda semántica)"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

# Intentar importar qdrant-client, si no existe usar fallback local
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("⚠️  qdrant-client no instalado — usando almacenamiento local fallback")


class QdrantErrorStore:
    """Almacena y busca errores por similitud semántica"""
    
    def __init__(
        self,
        collection_name: str = "error_memory",
        qdrant_url: str = "http://localhost:6333",
        fallback_dir: str = ".engram_cache"
    ):
        self.collection_name = collection_name
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(exist_ok=True)
        self.fallback_file = self.fallback_dir / "qdrant_fallback.jsonl"
        
        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(url=qdrant_url, timeout=5)
                # Crear colección si no existe
                collections = self.client.get_collections().collections
                if not any(c.name == collection_name for c in collections):
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
                    print(f"✅ Colección Qdrant creada: {collection_name}")
                self.use_qdrant = True
            except Exception as e:
                print(f"⚠️  Qdrant no disponible ({e}) — usando fallback local")
                self.use_qdrant = False
        else:
            self.use_qdrant = False
    
    def _generate_embedding(self, text: str) -> list[float]:
        """Genera embedding simple basado en hash (fallback sin sentence-transformers)"""
        # Embedding determinista de 384 dimensiones basado en hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convertir bytes a floats en [-1, 1]
        embedding = []
        for i in range(384):
            byte_val = hash_bytes[i % len(hash_bytes)]
            embedding.append((byte_val / 127.5) - 1.0)
        return embedding
    
    def index_error(self, error_data: dict) -> str:
        """Indexa un error para búsqueda semántica"""
        text = f"{error_data['error_type']}: {error_data['message']} — {error_data['solution']}"
        embedding = self._generate_embedding(text)
        point_id = hashlib.sha256(error_data.get("fingerprint", "").encode()).hexdigest()[:16]
        
        if self.use_qdrant:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "error_type": error_data["error_type"],
                                "message": error_data["message"],
                                "context": error_data["context"],
                                "solution": error_data["solution"],
                                "severity": error_data["severity"],
                                "timestamp": error_data["timestamp"]
                            }
                        )
                    ]
                )
                return point_id
            except Exception as e:
                print(f"⚠️  Error indexando en Qdrant: {e} — usando fallback")
                self.use_qdrant = False
        
        # Fallback: guardar en JSONL con embedding
        fallback_data = {
            "id": point_id,
            "embedding": embedding,
            **error_data
        }
        with open(self.fallback_file, "a") as f:
            f.write(json.dumps(fallback_data) + "\n")
        return point_id
    
    def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        """Busca errores similares por similitud semántica"""
        query_embedding = self._generate_embedding(query)
        
        if self.use_qdrant:
            try:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    with_payload=True
                )
                return [
                    {
                        "score": r.score,
                        "error_type": r.payload["error_type"],
                        "message": r.payload["message"],
                        "solution": r.payload["solution"],
                        "severity": r.payload["severity"],
                        "timestamp": r.payload["timestamp"]
                    }
                    for r in results
                ]
            except Exception as e:
                print(f"⚠️  Error buscando en Qdrant: {e} — usando fallback")
                self.use_qdrant = False
        
        # Fallback: búsqueda por similitud de coseno en JSONL
        results = []
        with open(self.fallback_file) as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                similarity = self._cosine_similarity(query_embedding, data["embedding"])
                results.append({
                    "score": similarity,
                    "error_type": data["error_type"],
                    "message": data["message"],
                    "solution": data["solution"],
                    "severity": data["severity"],
                    "timestamp": data["timestamp"]
                })
        
        # Ordenar por similitud descendente
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calcula similitud de coseno (sin numpy)"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    
    def get_stats(self) -> dict[str, Any]:
        """Estadísticas del almacén"""
        if self.use_qdrant:
            try:
                info = self.client.get_collection(self.collection_name)
                return {
                    "backend": "qdrant",
                    "points": info.points_count,
                    "status": "ok"
                }
            except:
                self.use_qdrant = False
        
        # Fallback stats
        count = 0
        if self.fallback_file.exists():
            with open(self.fallback_file) as f:
                count = sum(1 for line in f if line.strip())
        return {
            "backend": "local_fallback",
            "points": count,
            "status": "ok"
        }

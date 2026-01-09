"""Vector Store for semantic memory using ChromaDB"""
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class VectorSearchResult:
    id: str
    content: str
    score: float
    metadata: dict[str, Any]

class VectorStore:
    """Vector store for semantic search using ChromaDB."""
    
    def __init__(self, persist_dir: Path, collection_name: str = "forge_memory"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._embedding_fn = None
    
    def _init_client(self):
        if self._client is not None:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Initialized ChromaDB at {self.persist_dir}")
        except ImportError:
            logger.warning("ChromaDB not installed. Install with: pip install chromadb")
            raise
    
    def add(self, id: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
        """Add a document to the vector store."""
        try:
            self._init_client()
            self._collection.add(
                ids=[id],
                documents=[content],
                metadatas=[metadata or {}]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def add_batch(self, ids: list[str], contents: list[str], metadatas: list[dict] | None = None) -> bool:
        """Add multiple documents to the vector store."""
        try:
            self._init_client()
            self._collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas or [{} for _ in ids]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add batch: {e}")
            return False
    
    def search(self, query: str, limit: int = 10, filter: dict | None = None) -> list[VectorSearchResult]:
        """Search for similar documents."""
        try:
            self._init_client()
            results = self._collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter
            )
            
            search_results = []
            if results and results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    search_results.append(VectorSearchResult(
                        id=doc_id,
                        content=results['documents'][0][i] if results['documents'] else "",
                        score=1 - results['distances'][0][i] if results['distances'] else 0.0,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                    ))
            return search_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete(self, ids: list[str]) -> bool:
        """Delete documents by ID."""
        try:
            self._init_client()
            self._collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def count(self) -> int:
        """Get the number of documents in the store."""
        try:
            self._init_client()
            return self._collection.count()
        except Exception:
            return 0


class CodebaseIndex:
    """Index a codebase for semantic search."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
    
    def index_file(self, file_path: Path, chunk_size: int = 1000, overlap: int = 200) -> int:
        """Index a single file, returning the number of chunks created."""
        try:
            content = file_path.read_text()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return 0
        
        chunks = self._chunk_content(content, chunk_size, overlap)
        if not chunks:
            return 0
        
        ids = [f"{file_path}:{i}" for i in range(len(chunks))]
        metadatas = [{"file": str(file_path), "chunk_index": i, "language": file_path.suffix} for i in range(len(chunks))]
        
        self.vector_store.add_batch(ids, chunks, metadatas)
        return len(chunks)
    
    def index_directory(self, directory: Path, extensions: list[str] | None = None) -> dict[str, int]:
        """Index all files in a directory."""
        extensions = extensions or [".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".md"]
        ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        
        stats = {"files": 0, "chunks": 0}
        
        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                if any(ignored in file_path.parts for ignored in ignore_dirs):
                    continue
                chunks = self.index_file(file_path)
                if chunks > 0:
                    stats["files"] += 1
                    stats["chunks"] += chunks
        
        logger.info(f"Indexed {stats['files']} files with {stats['chunks']} chunks")
        return stats
    
    def _chunk_content(self, content: str, chunk_size: int, overlap: int) -> list[str]:
        """Split content into overlapping chunks."""
        if len(content) <= chunk_size:
            return [content] if content.strip() else []
        
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def search_code(self, query: str, limit: int = 10, file_filter: str | None = None) -> list[VectorSearchResult]:
        """Search the indexed codebase."""
        filter_dict = None
        if file_filter:
            filter_dict = {"language": file_filter}
        return self.vector_store.search(query, limit, filter_dict)

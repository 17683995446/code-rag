import time
import json
from typing import Optional, Dict, List, Any
from pathlib import Path


try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FastAPI = HTTPException = BaseModel = None
    uvicorn = None
    FASTAPI_AVAILABLE = False


class BuildRequest:
    def __init__(self, source_path: str = "", chunk_size: int = 512, chunk_overlap: int = 50,
                 embedding_model: str = "all-MiniLM-L6-v2", rebuild: bool = False):
        self.source_path = source_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.rebuild = rebuild


class SearchRequest:
    def __init__(self, query: str = "", top_k: int = 10, language: Optional[str] = None):
        self.query = query
        self.top_k = top_k
        self.language = language


class QARequest:
    def __init__(self, question: str = "", context: Optional[List[Dict]] = None, template: str = "code_search"):
        self.question = question
        self.context = context or []
        self.template = template


if not FASTAPI_AVAILABLE:
    raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")


class CodeRAGAPI:
    def __init__(self, storage_path: str = "./data"):
        self.storage_path = storage_path
        self.app = FastAPI(title="Code RAG API", version="1.0.0")
        self._setup_middleware()
        self._setup_routes()
        self.indexer = None
        self.chunker = None

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            return {"message": "Code RAG API", "version": "1.0.0"}

        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}

        @self.app.post("/build")
        async def build(request: BuildRequest = None):
            try:
                from optimized.embedding import OptimizedIndexer, EmbeddingEngine
                from optimized.chunker import SemanticChunker
                from optimized.storage import StorageFacade

                start = time.time()

                storage = StorageFacade(self.storage_path)

                if request and request.rebuild:
                    storage.clear()

                from stage1.parser import DirectoryParser

                parser = DirectoryParser()
                files, chunks, stats = parser.parse_directory(
                    request.source_path if request else "./"
                )

                chunker = SemanticChunker()
                all_chunks = []
                for file in files:
                    file_chunks = chunker.chunk(
                        file.content,
                        str(file.relative_path),
                        file.language
                    )
                    all_chunks.extend(file_chunks)

                storage.save_chunks(all_chunks)

                embedding = EmbeddingEngine()
                indexer = OptimizedIndexer(embedding_engine=embedding)
                indexer.build_index(all_chunks)
                indexer.save(
                    str(Path(self.storage_path) / "index.npy"),
                    str(Path(self.storage_path) / "metadata.json")
                )

                self.indexer = indexer
                self.chunker = chunker

                return {
                    "status": "success",
                    "files_processed": len(files),
                    "chunks_created": len(all_chunks),
                    "time_seconds": time.time() - start
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/search")
        async def search(request: SearchRequest = None):
            try:
                from optimized.embedding import OptimizedIndexer
                from optimized.storage import StorageFacade

                storage = StorageFacade(self.storage_path)

                if self.indexer is None:
                    index_path = Path(self.storage_path) / "index.npy"
                    meta_path = Path(self.storage_path) / "metadata.json"
                    if index_path.exists():
                        from optimized.embedding import EmbeddingEngine
                        embedding = EmbeddingEngine()
                        self.indexer = OptimizedIndexer(embedding_engine=embedding)
                        self.indexer.load(str(index_path), str(meta_path))
                    else:
                        raise HTTPException(status_code=400, detail="Index not built")

                results = self.indexer.search(
                    request.query if request else "",
                    top_k=request.top_k if request else 10
                )

                return {
                    "query": request.query if request else "",
                    "total": len(results),
                    "results": results
                }

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/qa")
        async def qa(request: QARequest = None):
            try:
                from stage4 import CodeQAEngine

                qa_engine = CodeQAEngine()
                chunks = request.context if request else []

                result = qa_engine.ask(
                    question=request.question if request else "",
                    code_chunks=chunks,
                    template_name=request.template if request else "code_search"
                )

                return {
                    "question": result.question,
                    "answer": result.answer,
                    "sources": result.sources,
                    "latency_ms": result.latency_ms
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/stats")
        async def stats():
            try:
                from optimized.storage import StorageFacade

                storage = StorageFacade(self.storage_path)
                return storage.stats()

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/symbol/{symbol_name}")
        async def get_symbol(symbol_name: str):
            try:
                from optimized.storage import StorageFacade

                storage = StorageFacade(self.storage_path)
                results = storage.get_by_symbol(symbol_name)

                return {
                    "symbol": symbol_name,
                    "definitions": results
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/file/{file_path:path}")
        async def get_file(file_path: str):
            try:
                from optimized.storage import StorageFacade

                storage = StorageFacade(self.storage_path)
                results = storage.get_by_file(file_path)

                return {
                    "file": file_path,
                    "chunks": results
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        uvicorn.run(self.app, host=host, port=port)


def create_app(storage_path: str = "./data") -> FastAPI:
    api = CodeRAGAPI(storage_path)
    return api.app

import os
import asyncio
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Union, Awaitable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading


@dataclass
class AsyncTask:
    task_id: str
    operation: str
    status: str = "pending"
    created_at: float = 0
    started_at: float = 0
    completed_at: float = 0
    result: Any = None
    error: str = None
    progress: float = 0
    metadata: Dict = field(default_factory=dict)


class AsyncTaskManager:
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, AsyncTask] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)

    def create_task(
        self,
        operation: str,
        coro_func: Callable,
        *args,
        **kwargs
    ) -> str:
        task_id = hashlib.md5(f"{operation}{time.time()}".encode()).hexdigest()[:16]

        task = AsyncTask(
            task_id=task_id,
            operation=operation,
            created_at=time.time()
        )

        with self._lock:
            self.tasks[task_id] = task

        future = self._executor.submit(self._run_task, task_id, coro_func, args, kwargs)

        return task_id

    def _run_task(self, task_id: str, coro_func: Callable, args, kwargs):
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "running"
                self.tasks[task_id].started_at = time.time()

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coro_func(*args, **kwargs))
            loop.close()

            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "completed"
                    self.tasks[task_id].result = result
                    self.tasks[task_id].completed_at = time.time()

        except Exception as e:
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id].status = "failed"
                    self.tasks[task_id].error = str(e)
                    self.tasks[task_id].completed_at = time.time()

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        with self._lock:
            return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> str:
        task = self.get_task(task_id)
        return task.status if task else "not_found"

    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "cancelled"
                return True
        return False

    def list_tasks(self, status: str = None) -> List[AsyncTask]:
        with self._lock:
            if status:
                return [t for t in self.tasks.values() if t.status == status]
            return list(self.tasks.values())

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        with self._lock:
            now = time.time()
            to_remove = [
                task_id for task_id, task in self.tasks.items()
                if task.completed_at > 0 and now - task.completed_at > max_age_seconds
            ]
            for task_id in to_remove:
                del self.tasks[task_id]


class AsyncRAGClient:
    def __init__(
        self,
        base_client = None,
        task_manager: AsyncTaskManager = None
    ):
        self.base_client = base_client
        self.task_manager = task_manager or AsyncTaskManager()

    async def index_directory_async(
        self,
        source_path: str,
        extensions: set = None,
        show_progress: bool = False
    ) -> str:
        if not self.base_client:
            raise RuntimeError("Base client not configured")

        from optimized.streaming import StreamingIndexer
        from optimized.chunker import ChunkBuilder

        chunker = ChunkBuilder()
        indexer = StreamingIndexer(chunker=chunker)

        source = Path(source_path)

        results = []
        for batch_result in indexer.index_directory(source, extensions, show_progress):
            results.append(batch_result)

        return {
            "total_batches": len(results),
            "total_chunks": sum(r.chunks_created for r in results),
            "total_files": sum(r.files_processed for r in results),
            "failed_files": sum(len(r.errors) for r in results)
        }

    async def search_async(
        self,
        query: str,
        top_k: int = 10,
        filters: Dict = None
    ) -> Dict:
        if not self.base_client:
            raise RuntimeError("Base client not configured")

        return await asyncio.to_thread(
            self.base_client.search,
            query=query,
            top_k=top_k,
            filters=filters
        )

    async def ask_async(
        self,
        question: str,
        context_chunks: int = 5
    ) -> Dict:
        if not self.base_client:
            raise RuntimeError("Base client not configured")

        return await asyncio.to_thread(
            self.base_client.ask,
            question=question,
            context_chunks=context_chunks
        )

    async def build_index_async(
        self,
        source_path: str,
        rebuild: bool = False,
        show_progress: bool = False
    ) -> str:
        task_id = self.task_manager.create_task(
            operation="build_index",
            coro_func=self._build_index_coro,
            source_path=source_path,
            rebuild=rebuild,
            show_progress=show_progress
        )
        return task_id

    async def _build_index_coro(
        self,
        source_path: str,
        rebuild: bool,
        show_progress: bool
    ) -> Dict:
        if not self.base_client:
            return {"error": "Base client not configured"}

        return await asyncio.to_thread(
            self.base_client.build_index,
            source_path=source_path,
            rebuild=rebuild,
            show_progress=show_progress
        )

    def get_build_status(self, task_id: str) -> Dict:
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"status": "not_found"}

        return {
            "task_id": task.task_id,
            "operation": task.operation,
            "status": task.status,
            "progress": task.progress,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error": task.error
        }

    def wait_for_task(self, task_id: str, timeout: float = None) -> Any:
        start = time.time()
        while True:
            task = self.task_manager.get_task(task_id)
            if not task:
                return {"error": "Task not found"}

            if task.status in ("completed", "failed", "cancelled"):
                return task.result if task.status == "completed" else {"error": task.error}

            if timeout and (time.time() - start) > timeout:
                return {"error": "Timeout"}

            time.sleep(0.1)


class AsyncAPI:
    def __init__(self, rag_system = None):
        self.rag_system = rag_system
        self.task_manager = AsyncTaskManager()
        self._semaphore = asyncio.Semaphore(10)

    async def search(self, query: str, top_k: int = 10) -> Dict:
        async with self._semaphore:
            return await asyncio.to_thread(
                self.rag_system.search,
                query=query,
                top_k=top_k
            )

    async def ask(self, question: str) -> Dict:
        async with self._semaphore:
            return await asyncio.to_thread(
                self.rag_system.ask,
                question=question
            )

    async def build_index(self, source_path: str, rebuild: bool = False) -> str:
        task_id = hashlib.md5(f"build_{time.time()}".encode()).hexdigest()[:16]

        async def _build():
            return await asyncio.to_thread(
                self.rag_system.build_index,
                source_path=source_path,
                rebuild=rebuild
            )

        asyncio.create_task(_build())
        return task_id

    async def health_check(self) -> Dict:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "active_tasks": len(self.task_manager.list_tasks("running"))
        }


class StreamingResponse:
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._done = False

    async def put(self, chunk: str):
        await self._queue.put(chunk)

    async def done(self):
        await self._queue.put(None)
        self._done = True

    async def stream(self):
        while True:
            chunk = await self._queue.get()
            if chunk is None:
                break
            yield chunk

    def __aiter__(self):
        return self.stream()


class AsyncBatchProcessor:
    def __init__(self, batch_size: int = 10, max_concurrent: int = 5):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process(
        self,
        items: List[Any],
        process_func: Callable[[Any], Awaitable[Any]]
    ) -> List[Any]:
        results = [None] * len(items)
        tasks = []

        for i, item in enumerate(items):
            task = asyncio.create_task(
                self._process_item(i, item, process_func, results)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
        return results

    async def _process_item(
        self,
        index: int,
        item: Any,
        process_func: Callable[[Any], Awaitable[Any]],
        results: List
    ):
        async with self._semaphore:
            try:
                result = await process_func(item)
                results[index] = result
            except Exception as e:
                results[index] = {"error": str(e)}


class AsyncCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._global_lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any):
        async with self._global_lock:
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[key] = value

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Awaitable[Any]]
    ) -> Any:
        value = await self.get(key)
        if value is not None:
            return value

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            value = await self.get(key)
            if value is not None:
                return value

            value = await factory()
            await self.set(key, value)
            return value

    async def delete(self, key: str):
        async with self._global_lock:
            self._cache.pop(key, None)

    async def clear(self):
        async with self._global_lock:
            self._cache.clear()


class AsyncRateLimiter:
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self._requests: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.time()
            self._requests = [t for t in self._requests if now - t < self.time_window]

            if len(self._requests) < self.max_requests:
                self._requests.append(now)
                return True
            return False

    async def wait_and_acquire(self):
        while not await self.acquire():
            await asyncio.sleep(0.1)


class AsyncCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"
        self._lock = asyncio.Lock()
        self._half_open_calls = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "half_open"
                    self._half_open_calls = 0
                else:
                    raise Exception("Circuit breaker is OPEN")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = await asyncio.to_thread(func, *args, **kwargs)

            async with self._lock:
                if self.state == "half_open":
                    self._half_open_calls += 1
                    if self._half_open_calls >= self.half_open_max_calls:
                        self.state = "closed"
                        self.failure_count = 0

            return result

        except Exception as e:
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "open"

            raise e

    async def reset(self):
        async with self._lock:
            self.state = "closed"
            self.failure_count = 0
            self._half_open_calls = 0


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket):
        async with self._lock:
            self.connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        async with self._lock:
            self.connections.pop(client_id, None)

    async def send_to(self, client_id: str, message: str):
        async with self._lock:
            websocket = self.connections.get(client_id)
            if websocket:
                await websocket.send_text(message)

    async def broadcast(self, message: str):
        async with self._lock:
            for client_id, websocket in list(self.connections.items()):
                try:
                    await websocket.send_text(message)
                except Exception:
                    self.connections.pop(client_id, None)

    async def send_progress(self, client_id: str, progress: float, status: str):
        message = json.dumps({
            "type": "progress",
            "progress": progress,
            "status": status,
            "timestamp": time.time()
        })
        await self.send_to(client_id, message)

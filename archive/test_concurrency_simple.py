#!/usr/bin/env python3
"""
多Agent并发控制示例 - 简化版
"""

import sys
import time
import threading
import uuid
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from collections import defaultdict


class LockType(Enum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


class ConflictResolution(Enum):
    LAST_WRITE_WINS = "last_write_wins"
    EARLY_WRITE_WINS = "early_write_wins"
    MERGE = "merge"
    REJECT = "reject"


@dataclass
class LockEntry:
    resource_id: str
    lock_type: LockType
    holder_id: str
    acquired_at: float
    expires_at: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class Operation:
    op_id: str
    operation_type: str
    resource_id: str
    payload: Dict
    submitted_by: str
    submitted_at: float
    sequence_num: int = 0


@dataclass
class ChangeRecord:
    record_id: str
    resource_id: str
    change_type: str
    old_value: Any
    new_value: Any
    changed_by: str
    changed_at: float
    version: int
    metadata: Dict = field(default_factory=dict)


class DistributedLockManager:
    def __init__(self):
        self._locks: Dict[str, LockEntry] = {}
        self._lock = threading.Lock()
        self._watchers: List[Callable] = []

    def acquire(
        self,
        resource_id: str,
        holder_id: str = None,
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout_seconds: float = 30.0,
        wait: bool = True
    ) -> Optional[str]:
        holder_id = holder_id or str(uuid.uuid4())

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            with self._lock:
                existing = self._locks.get(resource_id)

                if existing:
                    if existing.holder_id == holder_id:
                        return holder_id

                    if existing.expires_at < time.time():
                        del self._locks[resource_id]
                    elif not wait:
                        return None
                    else:
                        time.sleep(0.01)
                        continue

                self._locks[resource_id] = LockEntry(
                    resource_id=resource_id,
                    lock_type=lock_type,
                    holder_id=holder_id,
                    acquired_at=time.time(),
                    expires_at=time.time() + timeout_seconds
                )

                return holder_id

            time.sleep(0.01)

        return None

    def release(self, resource_id: str, holder_id: str) -> bool:
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing and existing.holder_id == holder_id:
                del self._locks[resource_id]
                return True
            return False

    def is_locked(self, resource_id: str) -> bool:
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing and existing.expires_at > time.time():
                return True
            return False


class OptimisticLockManager:
    def __init__(self):
        self._versions: Dict[str, int] = {}
        self._lock = threading.Lock()

    def get_version(self, resource_id: str) -> int:
        with self._lock:
            return self._versions.get(resource_id, 0)

    def check_and_update(
        self,
        resource_id: str,
        expected_version: int,
        new_version: int = None
    ) -> Tuple[bool, int]:
        with self._lock:
            current = self._versions.get(resource_id, 0)
            if current != expected_version:
                return False, current

            new_v = new_version if new_version is not None else current + 1
            self._versions[resource_id] = new_v
            return True, new_v

    def increment(self, resource_id: str) -> int:
        with self._lock:
            new_v = self._versions.get(resource_id, 0) + 1
            self._versions[resource_id] = new_v
            return new_v


@contextmanager
def distributed_lock(
    lock_manager: DistributedLockManager,
    resource_id: str,
    holder_id: str = None,
    timeout_seconds: float = 30.0
):
    holder_id = lock_manager.acquire(
        resource_id, holder_id, timeout_seconds=timeout_seconds
    )
    if not holder_id:
        raise Exception(f"Failed to acquire lock for {resource_id}")
    try:
        yield holder_id
    finally:
        lock_manager.release(resource_id, holder_id)


class VersionedState:
    def __init__(self):
        self._changes: List[ChangeRecord] = []
        self._state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._version_manager = OptimisticLockManager()

    def get(self, resource_id: str) -> Optional[Any]:
        with self._lock:
            return self._state.get(resource_id)

    def get_with_version(self, resource_id: str) -> Tuple[Optional[Any], int]:
        with self._lock:
            return (
                self._state.get(resource_id),
                self._version_manager.get_version(resource_id)
            )

    def update(
        self,
        resource_id: str,
        new_value: Any,
        changed_by: str,
        expected_version: int = None
    ) -> Tuple[bool, int, Optional[ChangeRecord]]:
        with self._lock:
            current_version = self._version_manager.get_version(resource_id)

            if expected_version is not None and current_version != expected_version:
                return False, current_version, None

            old_value = self._state.get(resource_id)
            new_version = self._version_manager.increment(resource_id)

            self._state[resource_id] = new_value

            record = ChangeRecord(
                record_id=str(uuid.uuid4()),
                resource_id=resource_id,
                change_type='update' if old_value is not None else 'create',
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
                changed_at=time.time(),
                version=new_version
            )

            self._changes.append(record)
            return True, new_version, record

    def delete(
        self,
        resource_id: str,
        changed_by: str
    ) -> Tuple[bool, int, Optional[ChangeRecord]]:
        with self._lock:
            if resource_id not in self._state:
                return False, 0, None

            old_value = self._state[resource_id]
            new_version = self._version_manager.increment(resource_id)

            del self._state[resource_id]

            record = ChangeRecord(
                record_id=str(uuid.uuid4()),
                resource_id=resource_id,
                change_type='delete',
                old_value=old_value,
                new_value=None,
                changed_by=changed_by,
                changed_at=time.time(),
                version=new_version
            )

            self._changes.append(record)
            return True, new_version, record


class ConcurrencyFacade:
    def __init__(self):
        self.lock_manager = DistributedLockManager()
        self.state = VersionedState()

    def create_operation(
        self,
        operation_type: str,
        resource_id: str,
        payload: Dict,
        submitted_by: str = None
    ) -> Operation:
        return Operation(
            op_id=str(uuid.uuid4()),
            operation_type=operation_type,
            resource_id=resource_id,
            payload=payload,
            submitted_by=submitted_by or "unknown",
            submitted_at=time.time()
        )

    @contextmanager
    def safe_update(self, resource_id: str, agent_id: str = None):
        agent_id = agent_id or str(uuid.uuid4())
        holder_id = self.lock_manager.acquire(resource_id, agent_id)
        if not holder_id:
            raise Exception(f"Cannot acquire lock for {resource_id}")
        try:
            current_value, current_version = self.state.get_with_version(resource_id)
            yield current_value, current_version
        finally:
            self.lock_manager.release(resource_id, agent_id)

    def optimistic_update(
        self,
        resource_id: str,
        new_value: Any,
        expected_version: int,
        changed_by: str = None
    ) -> Tuple[bool, int, Optional[ChangeRecord]]:
        return self.state.update(
            resource_id, new_value, changed_by, expected_version
        )

    def get_resource(self, resource_id: str) -> Optional[Any]:
        return self.state.get(resource_id)

    def get_resource_history(self, resource_id: str, limit: int = 100) -> List[ChangeRecord]:
        with self.state._lock:
            history = [
                c for c in reversed(self.state._changes)
                if c.resource_id == resource_id
            ]
            return history[:limit]


def demo_pessimistic_locking():
    print("\n" + "="*60)
    print("演示1: 悲观锁（分布式锁）")
    print("="*60)

    concurrency = ConcurrencyFacade()
    resource_id = "demo/config:settings"
    results = []
    errors = []

    def agent_task(agent_id: int):
        try:
            with concurrency.safe_update(resource_id, f"agent_{agent_id}") as (value, version):
                current_value = value or {"count": 0, "agents": []}
                current_value["count"] += 1
                current_value["agents"].append(agent_id)

                time.sleep(0.1)

                concurrency.state.update(
                    resource_id,
                    current_value,
                    f"agent_{agent_id}"
                )

                results.append((agent_id, current_value["count"]))
        except Exception as e:
            errors.append((agent_id, str(e)))

    print("启动5个Agent并发更新...")
    threads = []
    for i in range(5):
        t = threading.Thread(target=agent_task, args=(i,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    final_value = concurrency.get_resource(resource_id)
    print(f"\n最终状态: {final_value}")
    print(f"成功更新次数: {len(results)}")
    print(f"错误数量: {len(errors)}")

    if final_value:
        print(f"计数器值: {final_value.get('count')}")
        if final_value.get('count') == 5:
            print("✅ 悲观锁成功：结果正确，没有冲突")
        else:
            print("⚠️ 结果不符预期")

    return final_value


def demo_optimistic_locking():
    print("\n" + "="*60)
    print("演示2: 乐观锁（版本控制）")
    print("="*60)

    concurrency = ConcurrencyFacade()
    resource_id = "demo/config:optimistic"
    success_count = 0
    conflict_count = 0

    concurrency.state.update(resource_id, {"version": 1, "value": "initial"}, "system")

    def agent_task(agent_id: int):
        nonlocal success_count, conflict_count

        for attempt in range(3):
            value, version = concurrency.state.get_with_version(resource_id)

            new_value = {
                **value,
                f"agent_{agent_id}": f"update_{attempt}",
                "version": version + 1
            }

            success, new_version, record = concurrency.optimistic_update(
                resource_id,
                new_value,
                version,
                f"agent_{agent_id}"
            )

            if success:
                success_count += 1
                break
            else:
                conflict_count += 1
                time.sleep(0.05)

    print("启动5个Agent并发更新，使用乐观锁...")
    threads = []
    for i in range(5):
        t = threading.Thread(target=agent_task, args=(i,), daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    final_value = concurrency.get_resource(resource_id)
    print(f"\n最终状态: {final_value}")
    print(f"成功更新数: {success_count}")
    print(f"冲突检测数: {conflict_count}")

    print("\n修改历史:")
    history = concurrency.get_resource_history(resource_id)
    for record in history:
        print(f"  版本 {record.version}: Agent {record.changed_by}")

    return final_value


def demo_rag_concurrent_indexing():
    print("\n" + "="*60)
    print("实际场景: 多Agent并发更新RAG索引")
    print("="*60)

    concurrency = ConcurrencyFacade()
    index_file = "rag/index:chunk_metadata"
    query_cache = "rag/cache:recent_queries"

    concurrency.state.update(index_file, {"chunks": {}, "last_updated": time.time()}, "system")
    concurrency.state.update(query_cache, {"cache": {}, "hits": 0}, "system")

    stats = {"index_updates": 0, "cache_updates": 0, "conflicts": 0}

    def indexer_agent(agent_id: int):
        for i in range(3):
            try:
                with concurrency.safe_update(index_file, f"indexer_{agent_id}") as (index, ver):
                    time.sleep(0.05)

                    new_index = {
                        "chunks": {
                            **(index["chunks"] if index else {}),
                            f"chunk_{agent_id}_{i}": {
                                "file": f"file_{agent_id}.py",
                                "line": i * 10
                            }
                        },
                        "last_updated": time.time()
                    }

                    success, _, _ = concurrency.state.update(
                        index_file, new_index, f"indexer_{agent_id}"
                    )

                    if success:
                        stats["index_updates"] += 1

            except Exception as e:
                stats["conflicts"] += 1

    def query_agent(agent_id: int):
        for i in range(3):
            try:
                value, version = concurrency.state.get_with_version(query_cache)
                if value:
                    new_cache = {
                        **value,
                        "cache": {
                            **value.get("cache", {}),
                            f"query_{agent_id}_{i}": "result"
                        },
                        "hits": value.get("hits", 0) + 1
                    }
                    success, _, _ = concurrency.optimistic_update(
                        query_cache, new_cache, version, f"query_agent_{agent_id}"
                    )
                    if success:
                        stats["cache_updates"] += 1
            except Exception:
                pass

    print("启动5个索引更新Agent和5个查询Agent...")
    threads = []
    for i in range(5):
        t1 = threading.Thread(target=indexer_agent, args=(i,), daemon=True)
        t2 = threading.Thread(target=query_agent, args=(i,), daemon=True)
        threads.extend([t1, t2])
        t1.start()
        t2.start()

    for t in threads:
        t.join()

    index = concurrency.get_resource(index_file)
    cache = concurrency.get_resource(query_cache)

    print("\n结果:")
    print(f"  索引更新次数: {stats['index_updates']}")
    print(f"  缓存更新次数: {stats['cache_updates']}")
    print(f"  冲突次数: {stats['conflicts']}")
    print(f"  索引中chunk数: {len(index.get('chunks', {}))}")
    print(f"  缓存中查询数: {len(cache.get('cache', {}))}")
    print(f"  缓存命中数: {cache.get('hits', 0)}")

    return index, cache


def main():
    print("\n" + "="*60)
    print("多Agent并发控制演示")
    print("="*60)
    print("\n本示例演示了多种并发控制策略，")
    print("确保多个Agent同时修改时结果的准确性。")

    demo_pessimistic_locking()
    demo_optimistic_locking()
    demo_rag_concurrent_indexing()

    print("\n" + "="*60)
    print("所有演示完成！")
    print("\n总结说明:")
    print("1. 悲观锁：适合写多读少，保证安全但有性能开销")
    print("2. 乐观锁：适合读多写少，无锁但需处理冲突重试")
    print("3. 事务：提供原子性，支持回滚（可扩展）")
    print("4. 队列串行化：顺序执行，无冲突但吞吐量较低（可扩展）")
    print("5. 冲突解决策略：根据业务需求选择合适策略")
    print("="*60)


if __name__ == "__main__":
    main()

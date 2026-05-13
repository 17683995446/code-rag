import os
import time
import json
import hashlib
import threading
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Tuple
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
    conflict_resolution: ConflictResolution = ConflictResolution.LAST_WRITE_WINS


class DistributedLockManager:
    def __init__(self, storage_path: str = "./data/locks"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, LockEntry] = {}
        self._lock = threading.Lock()
        self._watchers: List[Callable] = []
        self._cleanup_thread = None
        self._start_cleanup()

    def acquire(
        self,
        resource_id: str,
        holder_id: str = None,
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout_seconds: float = 30.0,
        wait: bool = True
    ) -> Optional[str]:
        holder_id = holder_id or str(uuid.uuid4())
        lock_id = hashlib.md5(f"{resource_id}:{holder_id}".encode()).hexdigest()

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            with self._lock:
                existing = self._locks.get(resource_id)

                if existing:
                    if existing.holder_id == holder_id:
                        return lock_id

                    if existing.lock_type == LockType.SHARED and lock_type == LockType.SHARED:
                        pass
                    else:
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
                    expires_at=time.time() + timeout_seconds,
                    metadata={'lock_id': lock_id}
                )

                self._save_locks()
                self._notify_watchers(resource_id, 'acquired', holder_id)
                return lock_id

            time.sleep(0.01)

        return None

    def release(self, resource_id: str, holder_id: str) -> bool:
        with self._lock:
            existing = self._locks.get(resource_id)

            if existing and existing.holder_id == holder_id:
                del self._locks[resource_id]
                self._save_locks()
                self._notify_watchers(resource_id, 'released', holder_id)
                return True

            return False

    def is_locked(self, resource_id: str) -> bool:
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing:
                if existing.expires_at < time.time():
                    del self._locks[resource_id]
                    self._save_locks()
                    return False
                return True
            return False

    def get_lock_holder(self, resource_id: str) -> Optional[str]:
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing and existing.expires_at > time.time():
                return existing.holder_id
            return None

    def renew_lock(self, resource_id: str, holder_id: str, extend_seconds: float = 30.0) -> bool:
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing and existing.holder_id == holder_id:
                existing.expires_at = max(existing.expires_at, time.time() + extend_seconds)
                self._save_locks()
                return True
            return False

    def add_watcher(self, callback: Callable):
        self._watchers.append(callback)

    def _notify_watchers(self, resource_id: str, event: str, holder_id: str):
        for callback in self._watchers:
            try:
                callback(resource_id, event, holder_id)
            except Exception:
                pass

    def _save_locks(self):
        lock_file = self.storage_path / "locks.json"
        data = {}
        for resource_id, entry in self._locks.items():
            data[resource_id] = {
                'lock_type': entry.lock_type.value,
                'holder_id': entry.holder_id,
                'acquired_at': entry.acquired_at,
                'expires_at': entry.expires_at,
                'metadata': entry.metadata
            }
        with open(lock_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_locks(self):
        lock_file = self.storage_path / "locks.json"
        if lock_file.exists():
            try:
                with open(lock_file) as f:
                    data = json.load(f)
                for resource_id, entry_data in data.items():
                    self._locks[resource_id] = LockEntry(
                        resource_id=resource_id,
                        lock_type=LockType(entry_data['lock_type']),
                        holder_id=entry_data['holder_id'],
                        acquired_at=entry_data['acquired_at'],
                        expires_at=entry_data['expires_at'],
                        metadata=entry_data.get('metadata', {})
                    )
            except Exception:
                pass

    def _start_cleanup(self):
        self._load_locks()

        def cleanup_loop():
            while True:
                with self._lock:
                    now = time.time()
                    expired = [
                        resource_id for resource_id, entry in self._locks.items()
                        if entry.expires_at < now
                    ]
                    for resource_id in expired:
                        del self._locks[resource_id]
                    if expired:
                        self._save_locks()
                        for resource_id in expired:
                            self._notify_watchers(resource_id, 'expired', '')
                time.sleep(10)

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def force_release(self, resource_id: str) -> bool:
        with self._lock:
            if resource_id in self._locks:
                del self._locks[resource_id]
                self._save_locks()
                self._notify_watchers(resource_id, 'forced_release', '')
                return True
            return False


class OptimisticLockManager:
    def __init__(self, storage_path: str = "./data/versions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._versions: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._load_versions()

    def get_version(self, resource_id: str) -> int:
        with self._lock:
            return self._versions.get(resource_id, 0)

    def set_version(self, resource_id: str, version: int):
        with self._lock:
            self._versions[resource_id] = version
            self._save_versions()

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
            self._save_versions()
            return True, new_v

    def increment(self, resource_id: str) -> int:
        with self._lock:
            new_v = self._versions.get(resource_id, 0) + 1
            self._versions[resource_id] = new_v
            self._save_versions()
            return new_v

    def _save_versions(self):
        version_file = self.storage_path / "versions.json"
        with open(version_file, 'w') as f:
            json.dump(self._versions, f, indent=2)

    def _load_versions(self):
        version_file = self.storage_path / "versions.json"
        if version_file.exists():
            try:
                with open(version_file) as f:
                    self._versions = json.load(f)
            except Exception:
                pass


@contextmanager
def distributed_lock(
    lock_manager: DistributedLockManager,
    resource_id: str,
    holder_id: str = None,
    timeout_seconds: float = 30.0
):
    lock_id = lock_manager.acquire(resource_id, holder_id, timeout_seconds=timeout_seconds)
    if not lock_id:
        raise Exception(f"Failed to acquire lock for {resource_id}")
    try:
        yield lock_id
    finally:
        lock_manager.release(resource_id, holder_id)


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


class VersionedState:
    def __init__(self, storage_path: str = "./data/state"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._changes: List[ChangeRecord] = []
        self._state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._version_manager = OptimisticLockManager(storage_path)
        self._load_state()

    def get(self, resource_id: str) -> Optional[Any]:
        with self._lock:
            return self._state.get(resource_id)

    def get_with_version(self, resource_id: str) -> Tuple[Optional[Any], int]:
        with self._lock:
            return self._state.get(resource_id), self._version_manager.get_version(resource_id)

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
            self._save_state()

            return True, new_version, record

    def delete(
        self,
        resource_id: str,
        changed_by: str,
        expected_version: int = None
    ) -> Tuple[bool, int, Optional[ChangeRecord]]:
        with self._lock:
            if resource_id not in self._state:
                return False, 0, None

            current_version = self._version_manager.get_version(resource_id)

            if expected_version is not None and current_version != expected_version:
                return False, current_version, None

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
            self._save_state()

            return True, new_version, record

    def get_history(
        self,
        resource_id: str,
        limit: int = 100
    ) -> List[ChangeRecord]:
        with self._lock:
            history = [
                c for c in reversed(self._changes)
                if c.resource_id == resource_id
            ]
            return history[:limit]

    def revert_to_version(
        self,
        resource_id: str,
        target_version: int,
        reverted_by: str
    ) -> Tuple[bool, Optional[ChangeRecord]]:
        with self._lock:
            history = [
                c for c in self._changes
                if c.resource_id == resource_id
            ]

            for record in history:
                if record.version == target_version:
                    old_value = self._state.get(resource_id)
                    new_value = record.old_value if record.change_type == 'update' else None

                    success, new_version, revert_record = self.update(
                        resource_id, new_value, reverted_by
                    )

                    if success and revert_record:
                        revert_record.metadata['reverted_from'] = target_version

                    return success, revert_record

            return False, None

    def _save_state(self):
        state_file = self.storage_path / "state.json"
        with open(state_file, 'w') as f:
            json.dump(self._state, f, indent=2)

        changes_file = self.storage_path / "changes.json"
        with open(changes_file, 'w') as f:
            serializable = [
                {
                    'record_id': r.record_id,
                    'resource_id': r.resource_id,
                    'change_type': r.change_type,
                    'old_value': r.old_value,
                    'new_value': r.new_value,
                    'changed_by': r.changed_by,
                    'changed_at': r.changed_at,
                    'version': r.version,
                    'metadata': r.metadata
                }
                for r in self._changes[-1000:]
            ]
            json.dump(serializable, f, indent=2)

    def _load_state(self):
        state_file = self.storage_path / "state.json"
        if state_file.exists():
            try:
                with open(state_file) as f:
                    self._state = json.load(f)
            except Exception:
                pass

        changes_file = self.storage_path / "changes.json"
        if changes_file.exists():
            try:
                with open(changes_file) as f:
                    data = json.load(f)
                self._changes = [
                    ChangeRecord(**r) for r in data
                ]
            except Exception:
                pass


class Transaction:
    def __init__(self, txn_id: str, state: VersionedState):
        self.txn_id = txn_id
        self.state = state
        self._operations: List[Tuple[Callable, Dict]] = []
        self._changes: List[ChangeRecord] = []
        self._committed = False
        self._locked_resources: List[str] = []

    def update(self, resource_id: str, value: Any, changed_by: str = None):
        self._operations.append(
            (self._do_update, {
                'resource_id': resource_id,
                'value': value,
                'changed_by': changed_by
            })
        )

    def delete(self, resource_id: str, changed_by: str = None):
        self._operations.append(
            (self._do_delete, {
                'resource_id': resource_id,
                'changed_by': changed_by
            })
        )

    def _do_update(self, resource_id: str, value: Any, changed_by: str = None):
        success, _, record = self.state.update(
            resource_id, value, changed_by or self.txn_id
        )
        if success and record:
            self._changes.append(record)
        return success

    def _do_delete(self, resource_id: str, changed_by: str = None):
        success, _, record = self.state.delete(
            resource_id, changed_by or self.txn_id
        )
        if success and record:
            self._changes.append(record)
        return success

    def commit(self) -> Tuple[bool, List[ChangeRecord]]:
        if self._committed:
            return False, []

        try:
            for op, args in self._operations:
                success = op(**args)
                if not success:
                    self.rollback()
                    return False, []

            self._committed = True
            return True, self._changes

        except Exception:
            self.rollback()
            return False, []

    def rollback(self):
        if self._committed:
            return

        for record in reversed(self._changes):
            try:
                if record.change_type == 'update':
                    self.state.update(
                        record.resource_id,
                        record.old_value,
                        'rollback'
                    )
                elif record.change_type == 'delete':
                    self.state.update(
                        record.resource_id,
                        record.old_value,
                        'rollback'
                    )
                elif record.change_type == 'create':
                    self.state.delete(
                        record.resource_id,
                        'rollback'
                    )
            except Exception:
                pass

        self._changes = []


class TransactionManager:
    def __init__(self, state: VersionedState):
        self.state = state
        self._transactions: Dict[str, Transaction] = {}
        self._lock = threading.Lock()

    def begin(self) -> Transaction:
        txn_id = str(uuid.uuid4())
        txn = Transaction(txn_id, self.state)
        with self._lock:
            self._transactions[txn_id] = txn
        return txn

    def get_transaction(self, txn_id: str) -> Optional[Transaction]:
        with self._lock:
            return self._transactions.get(txn_id)

    def commit(self, txn_id: str) -> Tuple[bool, List[ChangeRecord]]:
        txn = self.get_transaction(txn_id)
        if not txn:
            return False, []

        success, changes = txn.commit()

        with self._lock:
            if txn_id in self._transactions:
                del self._transactions[txn_id]

        return success, changes

    def rollback(self, txn_id: str):
        txn = self.get_transaction(txn_id)
        if txn:
            txn.rollback()
            with self._lock:
                if txn_id in self._transactions:
                    del self._transactions[txn_id]

    @contextmanager
    def transaction_context(self):
        txn = self.begin()
        try:
            yield txn
            self.commit(txn.txn_id)
        except Exception:
            self.rollback(txn.txn_id)
            raise


class ConflictDetector:
    def __init__(self):
        self._pending_operations: Dict[str, List[Operation]] = defaultdict(list)
        self._lock = threading.Lock()
        self._sequence_counter = 0

    def submit_operation(self, operation: Operation) -> int:
        with self._lock:
            self._sequence_counter += 1
            operation.sequence_num = self._sequence_counter
            self._pending_operations[operation.resource_id].append(operation)
            return operation.sequence_num

    def detect_conflicts(
        self,
        resource_id: str
    ) -> Tuple[List[Operation], List[Tuple[Operation, Operation]]]:
        with self._lock:
            operations = self._pending_operations.get(resource_id, [])
            conflicts = []

            if len(operations) <= 1:
                return operations, conflicts

            for i, op1 in enumerate(operations):
                for op2 in operations[i + 1:]:
                    if self._operations_conflict(op1, op2):
                        conflicts.append((op1, op2))

            return operations, conflicts

    def _operations_conflict(self, op1: Operation, op2: Operation) -> bool:
        if op1.operation_type == 'delete' or op2.operation_type == 'delete':
            return True

        if op1.operation_type == op2.operation_type:
            return True

        return False

    def resolve_conflicts(
        self,
        resource_id: str,
        strategy: ConflictResolution = ConflictResolution.LAST_WRITE_WINS
    ) -> List[Operation]:
        with self._lock:
            operations = self._pending_operations.get(resource_id, [])

            if not operations:
                return []

            if strategy == ConflictResolution.LAST_WRITE_WINS:
                operations.sort(key=lambda o: o.submitted_at, reverse=True)
                resolved = [operations[0]]
            elif strategy == ConflictResolution.EARLY_WRITE_WINS:
                operations.sort(key=lambda o: o.submitted_at)
                resolved = [operations[0]]
            elif strategy == ConflictResolution.MERGE:
                resolved = self._merge_operations(operations)
            else:
                resolved = []

            self._pending_operations[resource_id] = resolved
            return resolved

    def _merge_operations(self, operations: List[Operation]) -> List[Operation]:
        if not operations:
            return []

        merged = Operation(
            op_id=str(uuid.uuid4()),
            operation_type='merge',
            resource_id=operations[0].resource_id,
            payload={
                'merged_ops': [op.payload for op in operations]
            },
            submitted_by='system',
            submitted_at=time.time()
        )
        return [merged]

    def get_operation(self, op_id: str) -> Optional[Operation]:
        with self._lock:
            for operations in self._pending_operations.values():
                for op in operations:
                    if op.op_id == op_id:
                        return op
        return None

    def complete_operation(self, op_id: str) -> bool:
        with self._lock:
            for resource_id in list(self._pending_operations.keys()):
                operations = self._pending_operations[resource_id]
                filtered = [o for o in operations if o.op_id != op_id]
                self._pending_operations[resource_id] = filtered
                if len(filtered) != len(operations):
                    return True
        return False

    def clear_resource_operations(self, resource_id: str):
        with self._lock:
            if resource_id in self._pending_operations:
                del self._pending_operations[resource_id]


class OperationQueue:
    def __init__(self):
        self._queue: List[Operation] = []
        self._processing: List[Operation] = []
        self._completed: List[Operation] = []
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def enqueue(self, operation: Operation):
        with self._lock:
            self._queue.append(operation)
            self._cond.notify()

    def dequeue(self, timeout: float = None) -> Optional[Operation]:
        with self._lock:
            if not self._queue:
                if not self._cond.wait(timeout=timeout):
                    return None

            if self._queue:
                operation = self._queue.pop(0)
                self._processing.append(operation)
                return operation

            return None

    def complete(self, operation: Operation):
        with self._lock:
            if operation in self._processing:
                self._processing.remove(operation)
                self._completed.append(operation)

    def get_pending(self) -> List[Operation]:
        with self._lock:
            return list(self._queue)

    def get_processing(self) -> List[Operation]:
        with self._lock:
            return list(self._processing)

    def get_all(self) -> Dict[str, List[Operation]]:
        with self._lock:
            return {
                'pending': list(self._queue),
                'processing': list(self._processing),
                'completed': list(self._completed[-100:])
            }


class SerialExecutor:
    def __init__(self, state: VersionedState, lock_manager: DistributedLockManager):
        self.state = state
        self.lock_manager = lock_manager
        self.queue = OperationQueue()
        self.conflict_detector = ConflictDetector()
        self._running = False
        self._worker_thread = None
        self._callbacks: List[Callable] = []

    def start(self):
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop(self):
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

    def submit(self, operation: Operation) -> str:
        self.conflict_detector.submit_operation(operation)
        self.queue.enqueue(operation)
        return operation.op_id

    def add_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def _worker_loop(self):
        while self._running:
            operation = self.queue.dequeue(timeout=1)

            if not operation:
                continue

            try:
                resource_id = operation.resource_id

                lock_id = self.lock_manager.acquire(
                    resource_id,
                    operation.submitted_by
                )

                if lock_id:
                    try:
                        result = self._execute_operation(operation)
                        self._notify_callbacks(operation, 'completed', result)
                        self.conflict_detector.complete_operation(operation.op_id)
                    finally:
                        self.lock_manager.release(resource_id, operation.submitted_by)
                else:
                    self._notify_callbacks(operation, 'locked', None)

            except Exception as e:
                self._notify_callbacks(operation, 'failed', {'error': str(e)})

            self.queue.complete(operation)

    def _execute_operation(self, operation: Operation) -> Dict:
        if operation.operation_type == 'update':
            success, version, record = self.state.update(
                operation.resource_id,
                operation.payload.get('value'),
                operation.submitted_by
            )
            return {
                'success': success,
                'version': version,
                'record': record
            }
        elif operation.operation_type == 'delete':
            success, version, record = self.state.delete(
                operation.resource_id,
                operation.submitted_by
            )
            return {
                'success': success,
                'version': version,
                'record': record
            }
        elif operation.operation_type == 'read':
            value, version = self.state.get_with_version(operation.resource_id)
            return {
                'success': True,
                'value': value,
                'version': version
            }
        return {'success': False, 'error': 'Unknown operation'}

    def _notify_callbacks(self, operation: Operation, status: str, result: Any):
        for callback in self._callbacks:
            try:
                callback(operation, status, result)
            except Exception:
                pass


class ConcurrencyFacade:
    def __init__(self, base_path: str = "./data/concurrency"):
        self.lock_manager = DistributedLockManager(f"{base_path}/locks")
        self.state = VersionedState(f"{base_path}/state")
        self.txn_manager = TransactionManager(self.state)
        self.executor = SerialExecutor(self.state, self.lock_manager)

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
        lock_id = self.lock_manager.acquire(resource_id, agent_id)
        if not lock_id:
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

    def start_executor(self):
        self.executor.start()

    def stop_executor(self):
        self.executor.stop()

    def submit_and_execute(self, operation: Operation) -> str:
        return self.executor.submit(operation)

    def get_resource(self, resource_id: str) -> Optional[Any]:
        return self.state.get(resource_id)

    def get_resource_history(self, resource_id: str, limit: int = 100) -> List[ChangeRecord]:
        return self.state.get_history(resource_id, limit)

    @contextmanager
    def transaction(self):
        txn = self.txn_manager.begin()
        try:
            yield txn
            success, changes = self.txn_manager.commit(txn.txn_id)
            if not success:
                raise Exception("Transaction failed")
        except Exception:
            self.txn_manager.rollback(txn.txn_id)
            raise

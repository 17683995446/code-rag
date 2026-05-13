#!/usr/bin/env python3
"""
多Agent并发控制示例

演示如何使用并发控制模块保证多个Agent同时修改时的结果准确性
"""

import sys
import time
import threading
from typing import Dict, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from optimized.concurrency import (
    ConcurrencyFacade,
    ConflictResolution,
    LockType,
    Operation
)


def demo_pessimistic_locking():
    """
    演示悲观锁：使用分布式锁防止并发冲突
    """
    print("\n" + "="*60)
    print("演示1: 悲观锁（分布式锁）")
    print("="*60)

    concurrency = ConcurrencyFacade("/tmp/rag_concurrency/demo1")
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
    """
    演示乐观锁：使用版本控制检测并发冲突
    """
    print("\n" + "="*60)
    print("演示2: 乐观锁（版本控制）")
    print("="*60)

    concurrency = ConcurrencyFacade("/tmp/rag_concurrency/demo2")
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


def demo_transactions():
    """
    演示事务：支持回滚的原子性操作
    """
    print("\n" + "="*60)
    print("演示3: 事务（原子性与回滚）")
    print("="*60)

    concurrency = ConcurrencyFacade("/tmp/rag_concurrency/demo3")
    resource1 = "demo/txn:balance_a"
    resource2 = "demo/txn:balance_b"

    concurrency.state.update(resource1, {"balance": 1000}, "system")
    concurrency.state.update(resource2, {"balance": 2000}, "system")

    print("初始状态:")
    print(f"  Balance A: {concurrency.get_resource(resource1)}")
    print(f"  Balance B: {concurrency.get_resource(resource2)}")

    print("\n执行转账事务...")
    txn_successful = False

    try:
        with concurrency.transaction() as txn:
            a = concurrency.get_resource(resource1)
            b = concurrency.get_resource(resource2)

            txn.update(resource1, {"balance": a["balance"] - 500}, "txn_agent")
            txn.update(resource2, {"balance": b["balance"] + 500}, "txn_agent")

            txn_successful = True

    except Exception as e:
        print(f"事务失败: {e}")

    print("\n事务后状态:")
    print(f"  Balance A: {concurrency.get_resource(resource1)}")
    print(f"  Balance B: {concurrency.get_resource(resource2)}")

    print("\n现在模拟一个会失败的事务（中途出错）:")
    try:
        with concurrency.transaction() as txn:
            a = concurrency.get_resource(resource1)
            txn.update(resource1, {"balance": a["balance"] - 10000}, "txn_agent")
            raise Exception("模拟错误，触发回滚")
    except Exception as e:
        print(f"事务已失败并回滚: {e}")

    print("\n回滚后状态:")
    print(f"  Balance A: {concurrency.get_resource(resource1)}")
    print(f"  Balance B: {concurrency.get_resource(resource2)}")

    return txn_successful


def demo_serial_execution():
    """
    演示操作队列串行化执行
    """
    print("\n" + "="*60)
    print("演示4: 操作队列串行化")
    print("="*60)

    concurrency = ConcurrencyFacade("/tmp/rag_concurrency/demo4")
    resource_id = "demo/serial:counter"
    concurrency.state.update(resource_id, {"count": 0}, "system")

    results = []

    def on_operation_completed(operation: Operation, status: str, result: Any):
        if status == 'completed' and result.get('success'):
            results.append((operation.submitted_by, result))

    concurrency.executor.add_callback(on_operation_completed)
    concurrency.start_executor()

    print("提交10个并发操作，通过队列串行化执行...")

    for i in range(10):
        op = concurrency.create_operation(
            "update",
            resource_id,
            {"value": {"count": i+1}},
            f"agent_{i}"
        )
        concurrency.submit_and_execute(op)

    time.sleep(1)

    concurrency.stop_executor()

    final_value = concurrency.get_resource(resource_id)
    queue_state = concurrency.executor.queue.get_all()

    print(f"\n最终值: {final_value}")
    print(f"执行结果数: {len(results)}")
    print(f"队列待处理: {len(queue_state['pending'])}")
    print(f"队列处理中: {len(queue_state['processing'])}")
    print(f"队列已完成: {len(queue_state['completed'])}")

    return final_value


def demo_conflict_detection():
    """
    演示冲突检测与解决
    """
    print("\n" + "="*60)
    print("演示5: 冲突检测与解决策略")
    print("="*60)

    concurrency = ConcurrencyFacade("/tmp/rag_concurrency/demo5")
    resource_id = "demo/conflict:file"

    detector = concurrency.executor.conflict_detector

    print("\n提交多个冲突的操作...")
    op1 = Operation(
        op_id="op1",
        operation_type="update",
        resource_id=resource_id,
        payload={"value": "version_a"},
        submitted_by="agent_a",
        submitted_at=time.time() - 0.5
    )

    op2 = Operation(
        op_id="op2",
        operation_type="update",
        resource_id=resource_id,
        payload={"value": "version_b"},
        submitted_by="agent_b",
        submitted_at=time.time()
    )

    op3 = Operation(
        op_id="op3",
        operation_type="delete",
        resource_id=resource_id,
        payload={},
        submitted_by="agent_c",
        submitted_at=time.time() + 0.5
    )

    detector.submit_operation(op1)
    detector.submit_operation(op2)
    detector.submit_operation(op3)

    operations, conflicts = detector.detect_conflicts(resource_id)

    print(f"\n检测到冲突数: {len(conflicts)}")
    for i, (op_a, op_b) in enumerate(conflicts):
        print(f"  冲突 {i+1}: {op_a.op_id} ({op_a.submitted_by}) vs {op_b.op_id} ({op_b.submitted_by})")

    print("\n使用 '最后写入优先' 策略解决...")
    resolved = detector.resolve_conflicts(
        resource_id, ConflictResolution.LAST_WRITE_WINS
    )

    print(f"解决后的操作数: {len(resolved)}")
    for op in resolved:
        print(f"  - {op.op_id} ({op.submitted_by}): {op.payload}")

    return resolved


def demo_rag_concurrent_indexing():
    """
    演示RAG系统中的并发索引更新场景
    """
    print("\n" + "="*60)
    print("实际场景: 多Agent并发更新RAG索引")
    print("="*60)

    concurrency = ConcurrencyFacade("/tmp/rag_concurrency/demo_rag")
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

    try:
        demo_pessimistic_locking()
        demo_optimistic_locking()
        demo_transactions()
        demo_serial_execution()
        demo_conflict_detection()
        demo_rag_concurrent_indexing()

        print("\n" + "="*60)
        print("所有演示完成！")
        print("\n总结说明:")
        print("1. 悲观锁：适合写多读少，保证安全但有性能开销")
        print("2. 乐观锁：适合读多写少，无锁但需处理冲突重试")
        print("3. 事务：提供原子性，支持回滚")
        print("4. 队列串行化：顺序执行，无冲突但吞吐量较低")
        print("5. 冲突解决策略：根据业务需求选择合适策略")
        print("="*60)

    except KeyboardInterrupt:
        print("\n\n演示已停止")


if __name__ == "__main__":
    main()

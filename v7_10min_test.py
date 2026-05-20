#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 10分钟快速压力测试
用于快速验证系统稳定性
"""
import sys
import os
import time
import random
import json
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType

duration_seconds = 600  # 10分钟

print("=" * 80)
print("Starting 10-minute stress test")
print("=" * 80)

memory = MemorySystemV7()
start_time = time.time()

# 准备初始数据
print("Preparing initial data...")
for i in range(1000):
    memory.remember("w{}_n0".format(i), node_type=NodeType.ENTITY)

for i in range(500):
    a = random.randint(0, 999)
    b = random.randint(0, 999)
    if a != b:
        try:
            memory.connect("w{}_n0".format(a), "w{}_n0".format(b))
        except:
            pass

print("Initial data ready: 1000 nodes, 500 edges")

# 初始化计数器
ops_data = {"total": 0, "success": 0, "failure": 0}
ops_lock = threading.Lock()

# 工作线程
stop_flag = threading.Event()
num_workers = 20

def worker(worker_id):
    while not stop_flag.is_set():
        try:
            op = random.choice(['add_node', 'add_edge', 'search', 'infer', 'semantic', 'recommend', 'recall'])
            
            try:
                if op == 'add_node':
                    label = "w{}_n{}".format(worker_id, random.randint(0, 99999))
                    memory.remember(label, node_type=NodeType.ENTITY)
                elif op == 'add_edge':
                    stats = memory.get_statistics()
                    if stats['nodes'] >= 2:
                        a = random.randint(0, min(100, stats['nodes']-1))
                        b = random.randint(0, min(100, stats['nodes']-1))
                        if a != b:
                            memory.connect("w{}_n0".format(a), "w{}_n0".format(b))
                elif op == 'search':
                    memory.recall("w", k=10)
                elif op == 'infer':
                    memory.infer("w0_n0", max_depth=3)
                elif op == 'semantic':
                    memory.semantic_search("test", k=5)
                elif op == 'recommend':
                    memory.recommend_connections("w0_n0", k=3)
                elif op == 'recall':
                    memory.recall("w", k=20)
                
                with ops_lock:
                    ops_data['total'] += 1
                    ops_data['success'] += 1
                    
            except Exception as e:
                with ops_lock:
                    ops_data['total'] += 1
                    ops_data['failure'] += 1
        
        except Exception as e:
            pass

print("Starting {} worker threads...".format(num_workers))

worker_threads = []
for i in range(num_workers):
    t = threading.Thread(target=worker, args=(i,))
    t.daemon = True
    t.start()
    worker_threads.append(t)

# 监控线程
last_checkpoint = 0
last_progress = 0

print("\nTest running... (target: 10 minutes)")
print("=" * 80)

try:
    while True:
        elapsed = time.time() - start_time
        remaining = duration_seconds - elapsed
        
        if remaining <= 0:
            print("\nTarget duration reached!")
            break
        
        # 检查点
        if elapsed - last_checkpoint >= 60:
            stats = memory.get_statistics()
            ops = ops_data['total']
            rate = ops / elapsed if elapsed > 0 else 0
            
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            secs = int(elapsed % 60)
            
            print("Checkpoint @ {:02d}:{:02d}:{:02d} | Nodes: {:,} | Edges: {:,} | Ops: {:,} ({:.0f} ops/s)".format(
                hours, minutes, secs, stats['nodes'], stats['edges'], ops, rate
            ))
            
            last_checkpoint = elapsed
        
        # 进度
        if elapsed - last_progress >= 30:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            secs = int(elapsed % 60)
            remaining_m = int(remaining // 60)
            
            print("Progress: {:02d}:{:02d}:{:02d} / 00:10:00 | Ops: {:,} | {:.1f}% complete".format(
                hours, minutes, secs, ops_data['total'], 100*elapsed/duration_seconds
            ))
            
            last_progress = elapsed
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\nUser interrupted!")

finally:
    print("\nStopping threads...")
    stop_flag.set()
    
    for t in worker_threads:
        t.join(timeout=2)
    
    duration = time.time() - start_time
    final_stats = memory.get_statistics()
    
    print("\n" + "=" * 80)
    print("FINAL REPORT - 10 Minute Stress Test")
    print("=" * 80)
    
    print("\nTime Statistics:")
    print("  Target: {} seconds (10 minutes)".format(duration_seconds))
    print("  Actual: {:.0f} seconds ({:.2f} minutes)".format(duration, duration/60))
    print("  Completion: {:.1f}%".format(100*duration/duration_seconds))
    
    print("\nOperations Statistics:")
    print("  Total: {:,}".format(ops_data['total']))
    print("  Success: {:,} ({:.2f}%)".format(ops_data['success'], 100*ops_data['success']/max(ops_data['total'],1)))
    print("  Failure: {:,} ({:.2f}%)".format(ops_data['failure'], 100*ops_data['failure']/max(ops_data['total'],1)))
    print("  Average Rate: {:.0f} ops/s".format(ops_data['total']/duration))
    
    print("\nFinal State:")
    print("  Nodes: {:,}".format(final_stats['nodes']))
    print("  Edges: {:,}".format(final_stats['edges']))
    
    # 保存报告
    report = {
        "test_type": "10_minute_stress_test",
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.now().isoformat(),
        "duration": duration,
        "target_duration": duration_seconds,
        "operations": ops_data,
        "final_stats": final_stats,
        "success": ops_data['failure'] == 0
    }
    
    report_path = "/workspace/code-rag/v7_10min_test_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\nReport saved: {}".format(report_path))
    
    print("\n" + "=" * 80)
    if ops_data['failure'] == 0:
        print("SUCCESS! 10-minute test passed perfectly!")
        print("System is stable. Ready for 1-hour test.")
    else:
        print("FAILURE! Found {} errors".format(ops_data['failure']))
        print("System has issues that need to be fixed.")
    print("=" * 80)

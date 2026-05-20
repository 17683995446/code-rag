#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 超长时间压力测试（无缓冲版本）
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


class HourLongStressTest:
    def __init__(self, duration_seconds=3600):
        self.duration_seconds = duration_seconds
        self.progress_file = "/workspace/code-rag/test_progress.txt"
        self.start_time = None
        self.stop_flag = threading.Event()
        self.memory = None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = "[{}] {}".format(timestamp, message)
        print(log_line, flush=True)
        try:
            with open(self.progress_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except:
            pass
    
    def run(self):
        print("=" * 80)
        print("Starting 1-hour stress test")
        print("=" * 80)
        
        # 清理旧文件
        for f in [self.progress_file, "/workspace/code-rag/test_ops.json", "/workspace/code-rag/test_running.json"]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        
        print("Target duration: {} seconds ({} hours)".format(self.duration_seconds, self.duration_seconds/3600))
        print("Start time: {}".format(datetime.now()))
        print("=" * 80)
        
        self.memory = MemorySystemV7()
        self.start_time = time.time()
        
        # 准备初始数据
        self.log("Preparing initial data...")
        for i in range(1000):
            self.memory.remember(
                "w{}_n0".format(i), 
                node_type=NodeType.ENTITY,
                properties={"initial": True}
            )
        self.log("Created 1000 initial nodes")
        
        for i in range(500):
            a = random.randint(0, 999)
            b = random.randint(0, 999)
            if a != b:
                try:
                    self.memory.connect("w{}_n0".format(a), "w{}_n0".format(b))
                except:
                    pass
        self.log("Created 500 initial edges")
        
        # 初始化操作计数器
        ops_data = {"total": 0, "success": 0, "failure": 0}
        with open("/workspace/code-rag/test_ops.json", 'w') as f:
            json.dump(ops_data, f)
        
        # 启动操作线程
        num_workers = 20
        self.log("Starting {} worker threads...".format(num_workers))
        
        def worker(worker_id):
            ops = 0
            while not self.stop_flag.is_set():
                try:
                    op = random.choice(['add_node', 'add_edge', 'search', 'infer', 'semantic', 'recommend', 'recall', 'connect'])
                    
                    try:
                        if op == 'add_node':
                            label = "w{}_n{}".format(worker_id, random.randint(0, 99999))
                            self.memory.remember(label, node_type=random.choice([NodeType.ENTITY, NodeType.CONCEPT]))
                        elif op == 'add_edge':
                            stats = self.memory.get_statistics()
                            if stats['nodes'] >= 2:
                                a = random.randint(0, min(100, stats['nodes']-1))
                                b = random.randint(0, min(100, stats['nodes']-1))
                                if a != b:
                                    self.memory.connect("w{}_n0".format(a), "w{}_n0".format(b))
                        elif op == 'search':
                            self.memory.recall("w", k=10)
                        elif op == 'infer':
                            self.memory.infer("w0_n0", max_depth=3)
                        elif op == 'semantic':
                            self.memory.semantic_search("test", k=5)
                        elif op == 'recommend':
                            self.memory.recommend_connections("w0_n0", k=3)
                        elif op == 'recall':
                            self.memory.recall("w", k=20)
                        elif op == 'connect':
                            stats = self.memory.get_statistics()
                            if stats['nodes'] >= 2:
                                a = random.randint(0, min(100, stats['nodes'])-1)
                                b = random.randint(0, min(100, stats['nodes'])-1)
                                if a != b:
                                    self.memory.connect("w{}_n0".format(a), "w{}_n0".format(b))
                        
                        # 记录成功
                        with open("/workspace/code-rag/test_ops.json", 'r+') as f:
                            data = json.load(f)
                            data['total'] += 1
                            data['success'] += 1
                            f.seek(0)
                            json.dump(data, f)
                            
                    except Exception as e:
                        with open("/workspace/code-rag/test_ops.json", 'r+') as f:
                            data = json.load(f)
                            data['total'] += 1
                            data['failure'] += 1
                            f.seek(0)
                            json.dump(data, f)
                
                except Exception as e:
                    pass
                
                ops += 1
        
        worker_threads = []
        for i in range(num_workers):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            t.start()
            worker_threads.append(t)
        
        # 启动监控线程
        self.log("Starting monitoring thread...")
        def monitor():
            last_checkpoint = 0
            last_progress_update = 0
            
            while not self.stop_flag.is_set():
                try:
                    elapsed = time.time() - self.start_time
                    
                    # 检查点
                    if elapsed - last_checkpoint >= 60:
                        stats = self.memory.get_statistics()
                        
                        try:
                            with open("/workspace/code-rag/test_ops.json", 'r') as f:
                                ops_data = json.load(f)
                            total_ops = ops_data.get('total', 0)
                            ops_per_second = total_ops / elapsed if elapsed > 0 else 0
                        except:
                            total_ops = 0
                            ops_per_second = 0
                        
                        hours = int(elapsed // 3600)
                        minutes = int((elapsed % 3600) // 60)
                        secs = int(elapsed % 60)
                        
                        self.log("Checkpoint @ {:02d}:{:02d}:{:02d} | Nodes: {:,} | Edges: {:,} | Ops: {:,} ({:.0f} ops/s)".format(
                            hours, minutes, secs, stats['nodes'], stats['edges'], total_ops, ops_per_second
                        ))
                        
                        last_checkpoint = elapsed
                    
                    # 更新进度
                    if elapsed - last_progress_update >= 5:
                        progress = {
                            "elapsed": elapsed,
                            "running": True,
                            "pid": os.getpid()
                        }
                        with open("/workspace/code-rag/test_running.json", 'w') as f:
                            json.dump(progress, f)
                        last_progress_update = elapsed
                    
                    time.sleep(1)
                    
                except Exception as e:
                    self.log("Monitor error: {}".format(e))
        
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 运行
        self.log("Starting {} hour stress test...".format(self.duration_seconds/3600))
        self.log("Press Ctrl+C to stop early\n")
        
        try:
            last_progress = 0
            
            while True:
                elapsed = time.time() - self.start_time
                remaining = self.duration_seconds - elapsed
                
                if remaining <= 0:
                    self.log("Target duration reached: {:.0f} seconds".format(elapsed))
                    break
                
                # 每30秒显示一次进度
                if int(elapsed) % 30 == 0 and elapsed - last_progress >= 30:
                    try:
                        with open("/workspace/code-rag/test_ops.json", 'r') as f:
                            ops_data = json.load(f)
                        ops = ops_data.get('total', 0)
                        rate = ops / elapsed if elapsed > 0 else 0
                    except:
                        ops = 0
                        rate = 0
                    
                    hours = int(elapsed // 3600)
                    minutes = int((elapsed % 3600) // 60)
                    secs = int(elapsed % 60)
                    remaining_h = int(remaining // 3600)
                    remaining_m = int((remaining % 3600) // 60)
                    
                    self.log("Progress: {:02d}:{:02d}:{:02d} / {:02d}:{:02d}:00 | Ops: {:,} | Rate: {:.0f} ops/s".format(
                        hours, minutes, secs, remaining_h, remaining_m, ops, rate
                    ))
                    last_progress = elapsed
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.log("User interrupted (ran {:.0f} seconds)".format(time.time() - self.start_time))
        finally:
            self.log("Stopping all threads...")
            self.stop_flag.set()
            
            for t in worker_threads:
                t.join(timeout=2)
            monitor_thread.join(timeout=2)
            
            self.log("Collecting final statistics...")
            final_stats = self.memory.get_statistics()
            
            try:
                with open("/workspace/code-rag/test_ops.json", 'r') as f:
                    ops_data = json.load(f)
            except:
                ops_data = {"total": 0, "success": 0, "failure": 0}
            
            duration = time.time() - self.start_time
            
            print("\n" + "=" * 80)
            print("FINAL REPORT - 1 Hour Stress Test")
            print("=" * 80)
            
            print("\nTime Statistics:")
            print("  Target: {} seconds ({} hours)".format(self.duration_seconds, self.duration_seconds/3600))
            print("  Actual: {:.0f} seconds ({:.2f} hours)".format(duration, duration/3600))
            print("  Completion: {:.1f}%".format(100*duration/self.duration_seconds))
            
            print("\nOperations Statistics:")
            print("  Total: {:,}".format(ops_data['total']))
            print("  Success: {:,} ({:.2f}%)".format(ops_data['success'], 100*ops_data['success']/max(ops_data['total'],1)))
            print("  Failure: {:,} ({:.2f}%)".format(ops_data['failure'], 100*ops_data['failure']/max(ops_data['total'],1)))
            print("  Average Rate: {:.0f} ops/s".format(ops_data['total']/duration))
            
            print("\nFinal State:")
            print("  Nodes: {:,}".format(final_stats.get('nodes', 0)))
            print("  Edges: {:,}".format(final_stats.get('edges', 0)))
            
            # 保存报告
            report = {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": duration,
                "target_duration": self.duration_seconds,
                "operations": ops_data,
                "final_stats": final_stats,
                "success": ops_data['failure'] == 0
            }
            
            report_path = "/workspace/code-rag/v7_hour_long_test_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            print("\nFull report saved: {}".format(report_path))
            
            print("\n" + "=" * 80)
            if ops_data['failure'] == 0:
                print("SUCCESS! 1-hour stress test passed perfectly!")
            else:
                print("Test completed with {:.2f}% failure rate".format(100*ops_data['failure']/ops_data['total']))
            print("=" * 80)
            
            # 清理
            try:
                os.remove("/workspace/code-rag/test_ops.json")
                os.remove("/workspace/code-rag/test_running.json")
            except:
                pass


if __name__ == "__main__":
    tester = HourLongStressTest(duration_seconds=3600)
    tester.run()

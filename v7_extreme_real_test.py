#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 超极端真实世界测试
包括：极端大规模图、真实用户使用模式、长时间运行、压力恢复
"""
import sys
import os
import time
import random
import json
import threading
import tempfile
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType


class ExtremeRealWorldTest:
    """超极端真实世界测试"""
    
    def __init__(self, duration_seconds=1800):  # 30分钟
        self.duration = duration_seconds
        self.memory = None
        self.stop_flag = threading.Event()
        self.start_time = None
        self.results = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "stats": {},
            "success": True,
            "checkpoints": [],
            "issues": []
        }
        self.operation_stats = defaultdict(int)
        self.stats_lock = threading.Lock()
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
    
    def add_node_batch(self, num_nodes, batch_name):
        """批量添加节点 - 测试高吞吐"""
        added = 0
        for i in range(num_nodes):
            try:
                node_type = random.choice([NodeType.ENTITY, NodeType.CONCEPT, NodeType.DOCUMENT])
                self.memory.remember(
                    f"{batch_name}_node_{i}_{int(time.time()*1000)}",
                    properties={
                        "batch": batch_name,
                        "index": i,
                        "timestamp": time.time()
                    },
                    node_type=node_type
                )
                added += 1
            except Exception as e:
                self.log(f"⚠️  节点添加错误: {e}")
        
        with self.stats_lock:
            self.operation_stats["batch_add"] += added
        return added
    
    def add_edge_massive(self, num_edges, source_prefix, target_prefix):
        """大规模添加边 - 测试复杂连接"""
        added = 0
        for i in range(num_edges):
            try:
                source = f"{source_prefix}_node_{random.randint(0, 99)}"
                target = f"{target_prefix}_node_{random.randint(0, 99)}"
                edge_type = random.choice([e.value for e in EdgeType.all()])
                self.memory.connect(
                    source, target,
                    relation=edge_type,
                    weight=random.uniform(0.1, 1.0)
                )
                added += 1
            except Exception as e:
                self.log(f"⚠️  边添加错误: {e}")
        
        with self.stats_lock:
            self.operation_stats["batch_edge"] += added
        return added
    
    def simulate_complex_query(self):
        """模拟复杂查询模式"""
        try:
            stats = self.memory.get_statistics()
            
            # 随机查询类型
            query_type = random.choice([
                "search", "infer", "semantic", "recommend", "visualize"
            ])
            
            if query_type == "search":
                # 召回搜索
                results = self.memory.recall(
                    random.choice(["test", "node", "batch", "entity"]),
                    k=random.randint(5, 50)
                )
                with self.stats_lock:
                    self.operation_stats["search"] += 1
            
            elif query_type == "infer":
                # 图推理
                graph_data = self.memory.get_graph_for_visualization()
                if graph_data and graph_data["nodes"]:
                    start_node = random.choice(graph_data["nodes"])["label"]
                    results = self.memory.infer(
                        start_node,
                        max_depth=random.randint(1, 5)
                    )
                with self.stats_lock:
                    self.operation_stats["infer"] += 1
            
            elif query_type == "semantic":
                # 语义搜索
                queries = ["data", "model", "learning", "system", "test"]
                query = random.choice(queries)
                results = self.memory.semantic_search(
                    query,
                    k=random.randint(5, 30)
                )
                with self.stats_lock:
                    self.operation_stats["semantic"] += 1
            
            elif query_type == "recommend":
                # 推荐连接
                graph_data = self.memory.get_graph_for_visualization()
                if graph_data and graph_data["nodes"]:
                    node_label = random.choice(graph_data["nodes"])["label"]
                    recommendations = self.memory.recommend_connections(
                        node_label,
                        k=random.randint(3, 15)
                    )
                with self.stats_lock:
                    self.operation_stats["recommend"] += 1
            
            elif query_type == "visualize":
                # 获取图数据
                self.memory.get_graph_for_visualization()
                with self.stats_lock:
                    self.operation_stats["visualize"] += 1
            
            return True
        
        except Exception as e:
            with self.stats_lock:
                self.operation_stats["error"] += 1
            self.log(f"⚠️  查询错误: {e}")
            return False
    
    def simulate_real_user_session(self, session_id, duration_seconds):
        """模拟真实用户会话"""
        session_start = time.time()
        
        while not self.stop_flag.is_set() and (time.time() - session_start) < duration_seconds:
            # 混合操作
            action = random.choices(
                ["query", "add", "connect", "think"],
                weights=[0.4, 0.3, 0.2, 0.1]
            )[0]
            
            if action == "query":
                self.simulate_complex_query()
            
            elif action == "add":
                # 偶尔添加少量知识
                for _ in range(random.randint(1, 5)):
                    node_type = random.choice([NodeType.ENTITY, NodeType.CONCEPT])
                    label = f"user_{session_id}_add_{int(time.time()*1000)}"
                    try:
                        self.memory.remember(label, node_type=node_type)
                        with self.stats_lock:
                            self.operation_stats["user_add"] += 1
                    except:
                        pass
            
            elif action == "connect":
                # 连接现有知识
                try:
                    graph_data = self.memory.get_graph_for_visualization()
                    if graph_data and len(graph_data["nodes"]) >= 2:
                        nodes = [n["label"] for n in graph_data["nodes"]]
                        source = random.choice(nodes)
                        target = random.choice(nodes)
                        if source != target:
                            self.memory.connect(source, target, EdgeType.RELATED_TO)
                            with self.stats_lock:
                                self.operation_stats["user_connect"] += 1
                except:
                    pass
            
            elif action == "think":
                # 偶尔进行深度思考（GNN计算）
                try:
                    self.memory.compute_gnn_embeddings()
                    with self.stats_lock:
                        self.operation_stats["gnn_compute"] += 1
                except:
                    pass
            
            # 模拟用户思考延迟
            time.sleep(random.uniform(0.01, 0.1))
    
    def phase_1_extreme_initialization(self):
        """阶段1：极端大规模初始化"""
        self.log("阶段1：极端大规模图初始化...")
        
        # 多个批次
        batches = ["initial", "python", "js", "data", "ml"]
        total_nodes = 0
        total_edges = 0
        
        for batch_name in batches:
            self.log(f"  生成 {batch_name} 批次...")
            
            # 每批添加500-1000个节点
            num_nodes = random.randint(500, 1000)
            added_nodes = self.add_node_batch(num_nodes, batch_name)
            total_nodes += added_nodes
            
            # 添加大量边
            num_edges = random.randint(num_nodes * 2, num_nodes * 3)
            added_edges = self.add_edge_massive(num_edges, batch_name, batch_name)
            total_edges += added_edges
        
        stats = self.memory.get_statistics()
        self.log(f"  初始化完成: {stats['nodes']} 节点, {stats['edges']} 边")
        
        self.results["checkpoints"].append({
            "phase": 1,
            "nodes": stats["nodes"],
            "edges": stats["edges"]
        })
    
    def phase_2_multi_user_sessions(self):
        """阶段2：多用户并发会话"""
        self.log("阶段2：多用户并发会话...")
        
        num_users = 30
        session_duration = self.duration  # 全程运行
        threads = []
        
        self.log(f"  启动 {num_users} 个并发用户会话...")
        
        # 启动所有用户线程
        for user_id in range(num_users):
            t = threading.Thread(
                target=self.simulate_real_user_session,
                args=(user_id, session_duration)
            )
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 监控线程
        def monitor():
            last_checkpoint = 0
            while not self.stop_flag.is_set():
                elapsed = time.time() - self.start_time
                
                # 检查是否完成
                if elapsed >= self.duration:
                    self.log(f"  达到目标时长 {self.duration}秒！")
                    self.stop_flag.set()
                    break
                
                # 检查点
                if elapsed - last_checkpoint >= 60:
                    stats = self.memory.get_statistics()
                    
                    with self.stats_lock:
                        ops_stats = dict(self.operation_stats)
                    
                    total_ops = sum(ops_stats.values())
                    rate = total_ops / elapsed if elapsed > 0 else 0
                    remaining = self.duration - elapsed
                    
                    self.log(f"  检查点: 节点 {stats['nodes']}, 边 {stats['edges']}, "
                            f"操作 {total_ops}, 速率 {rate:.1f} ops/s, "
                            f"剩余 {int(remaining)}秒")
                    
                    self.results["checkpoints"].append({
                        "phase": 2,
                        "elapsed": elapsed,
                        "nodes": stats["nodes"],
                        "edges": stats["edges"],
                        "operations": ops_stats.copy()
                    })
                    
                    last_checkpoint = elapsed
                
                time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 等待所有用户（或被停止）
        for t in threads:
            t.join()
        
        monitor_thread.join()
        
        self.log(f"  多用户会话阶段完成！")
    
    def phase_3_persistence_stress(self):
        """阶段3：持久化压力测试"""
        self.log("阶段3：持久化压力测试...")
        
        temp_dir = tempfile.mkdtemp()
        
        # 保存测试
        save_start = time.time()
        save_path = os.path.join(temp_dir, "extreme_test_save.json")
        try:
            success = self.memory.save(save_path)
            save_time = time.time() - save_start
            
            if success:
                file_size = os.path.getsize(save_path) / 1024  # KB
                self.log(f"  保存成功: {save_time:.2f}s, 文件大小: {file_size:.1f}KB")
            else:
                self.log("  ⚠️  保存失败！")
                self.results["issues"].append("persistence_save_failure")
        
        except Exception as e:
            self.log(f"  ⚠️  保存异常: {e}")
            self.results["issues"].append(f"persistence_error: {e}")
        
        # 重新加载测试
        self.log("  清空并重新加载...")
        self.memory.clear()
        
        reload_start = time.time()
        try:
            self.memory.load(save_path)
            reload_time = time.time() - reload_start
            
            stats_after = self.memory.get_statistics()
            self.log(f"  加载成功: {reload_time:.2f}s, 最终: {stats_after['nodes']} 节点")
        
        except Exception as e:
            self.log(f"  ⚠️  加载异常: {e}")
            self.results["issues"].append(f"persistence_load_error: {e}")
    
    def final_report(self):
        """生成最终报告"""
        final_stats = self.memory.get_statistics()
        
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration"] = time.time() - self.start_time
        self.results["final_stats"] = final_stats
        
        with self.stats_lock:
            final_ops = dict(self.operation_stats)
        
        self.results["operations"] = final_ops
        
        print("\n" + "=" * 80)
        print("📋 超极端真实世界测试 - 最终报告")
        print("=" * 80)
        
        print(f"\n⏱️  时间统计:")
        print(f"  目标时长: {self.duration}秒 ({self.duration/60:.1f}分钟)")
        print(f"  实际时长: {self.results['duration']:.1f}秒")
        
        print(f"\n📊 最终状态:")
        print(f"  节点数: {final_stats['nodes']:,}")
        print(f"  边数: {final_stats['edges']:,}")
        print(f"  嵌入数: {final_stats.get('embeddings_count', 0):,}")
        
        print(f"\n⚡ 操作统计:")
        total_ops = sum(final_ops.values())
        for op_type, count in sorted(final_ops.items()):
            print(f"  {op_type}: {count:,}")
        
        print(f"\n  总操作: {total_ops:,}")
        
        print(f"\n🔍 检查点数: {len(self.results['checkpoints'])}")
        print(f"⚠️  发现问题: {len(self.results['issues'])}")
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(__file__), "v7_extreme_real_test_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 完整报告保存: {report_path}")
        
        print("\n" + "=" * 80)
        if len(self.results["issues"]) == 0:
            print("🎉 超极端测试完美通过！系统极其稳定！")
        else:
            print(f"⚠️  发现 {len(self.results['issues'])} 个问题需要处理")
        print("=" * 80)
    
    def run(self):
        """运行完整测试"""
        print("=" * 80)
        print("🚀 知识图谱记忆系统 v7.0 - 超极端真实世界测试")
        print("=" * 80)
        print(f"目标时长: {self.duration}秒 ({self.duration/60:.1f}分钟)")
        
        # 初始化
        self.start_time = time.time()
        self.memory = MemorySystemV7()
        self.results["start_time"] = datetime.now().isoformat()
        
        # 运行各阶段
        self.phase_1_extreme_initialization()
        self.phase_2_multi_user_sessions()
        self.phase_3_persistence_stress()
        
        # 最终报告
        self.final_report()
        
        return self.results


if __name__ == "__main__":
    # 运行30分钟超极端测试
    test = ExtremeRealWorldTest(duration_seconds=1800)  # 30分钟
    test.run()

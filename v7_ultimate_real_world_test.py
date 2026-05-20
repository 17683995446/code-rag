#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 终极真实世界场景测试
模拟真实的多语言代码库、文档管理、智能搜索等场景
"""
import sys
import os
import time
import random
import json
import threading
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType

# ===========================================================================
# 真实世界数据生成器
# ===========================================================================

class RealWorldDataGenerator:
    """生成真实世界的知识图谱数据"""
    
    PYTHON_PACKAGES = ["numpy", "pandas", "scikit-learn", "tensorflow", "pytorch", 
                      "flask", "django", "fastapi", "requests", "httpx"]
    JS_FRAMEWORKS = ["react", "vue", "angular", "svelte", "next.js", "nuxt.js"]
    CONCEPTS = ["machine_learning", "deep_learning", "neural_networks", "data_science",
                "natural_language_processing", "computer_vision", "reinforcement_learning",
                "web_development", "backend", "frontend", "api", "database", "cache"]
    
    CODE_FILE_TYPES = ["model.py", "controller.py", "service.py", "utils.py", "config.py",
                      "index.js", "app.js", "router.js", "middleware.js", "constants.js"]
    
    @staticmethod
    def generate_python_codebase(memory, num_modules=50):
        """生成Python代码库结构"""
        modules = []
        
        # 生成模块
        for i in range(num_modules):
            package = random.choice(RealWorldDataGenerator.PYTHON_PACKAGES)
            module_type = random.choice(["model", "view", "controller", "utils"])
            module_name = f"{package}_{module_type}_{i}"
            memory.remember(
                module_name,
                properties={
                    "language": "python",
                    "type": module_type,
                    "package": package,
                    "lines_of_code": random.randint(50, 500),
                    "complexity": random.randint(1, 10)
                },
                node_type=NodeType.ENTITY
            )
            modules.append(module_name)
        
        # 生成依赖关系
        for i in range(min(100, num_modules * 2)):
            a = random.choice(modules)
            b = random.choice(modules)
            if a != b:
                memory.connect(a, b, EdgeType.USES, weight=random.uniform(0.5, 1.0))
        
        return modules
    
    @staticmethod
    def generate_javascript_project(memory, num_files=40):
        """生成JavaScript项目结构"""
        files = []
        
        for i in range(num_files):
            framework = random.choice(RealWorldDataGenerator.JS_FRAMEWORKS)
            file_type = random.choice(RealWorldDataGenerator.CODE_FILE_TYPES)
            file_name = f"{framework}_{file_type.replace('.', '_')}_{i}"
            memory.remember(
                file_name,
                properties={
                    "language": "javascript",
                    "framework": framework,
                    "type": file_type,
                    "size_kb": random.randint(1, 100)
                },
                node_type=NodeType.ENTITY
            )
            files.append(file_name)
        
        # 连接文件
        for i in range(min(80, num_files * 2)):
            a = random.choice(files)
            b = random.choice(files)
            if a != b:
                memory.connect(a, b, EdgeType.REFERENCES, weight=random.uniform(0.3, 0.9))
        
        return files
    
    @staticmethod
    def generate_concepts_and_documents(memory, num_docs=30):
        """生成概念和文档"""
        concepts = RealWorldDataGenerator.CONCEPTS
        docs = []
        
        # 添加概念
        for concept in concepts:
            memory.remember(
                concept,
                properties={
                    "domain": "technology",
                    "complexity": random.randint(1, 5)
                },
                node_type=NodeType.CONCEPT
            )
        
        # 添加文档
        for i in range(num_docs):
            related_concept = random.choice(concepts)
            doc_name = f"doc_{related_concept}_{i}"
            memory.remember(
                doc_name,
                properties={
                    "type": "documentation",
                    "topic": related_concept,
                    "words": random.randint(100, 5000)
                },
                node_type=NodeType.DOCUMENT
            )
            docs.append(doc_name)
            
            # 连接文档到概念
            memory.connect(doc_name, related_concept, EdgeType.RELATED_TO, weight=0.95)
        
        return concepts, docs

# ===========================================================================
# 复杂操作模拟器
# ===========================================================================

class ComplexOperationSimulator:
    """模拟真实用户的复杂操作"""
    
    def __init__(self, memory):
        self.memory = memory
        self.stats = {
            "add_node": 0, "add_edge": 0, "search": 0, "infer": 0,
            "semantic": 0, "recommend": 0, "errors": 0
        }
        self.stats_lock = threading.Lock()
    
    def simulate_user_search(self):
        """模拟用户搜索"""
        queries = ["model", "controller", "service", "python", "javascript", "react",
                   "data", "machine", "learning", "api", "database", "cache"]
        query = random.choice(queries)
        try:
            results = self.memory.recall(query, k=random.randint(5, 20))
            with self.stats_lock:
                self.stats["search"] += 1
            return len(results)
        except Exception as e:
            with self.stats_lock:
                self.stats["errors"] += 1
            return 0
    
    def simulate_semantic_search(self):
        """模拟语义搜索"""
        terms = ["data science", "web development", "machine learning", "api design",
                "database optimization", "cache strategies"]
        term = random.choice(terms)
        try:
            results = self.memory.semantic_search(term, k=random.randint(3, 15))
            with self.stats_lock:
                self.stats["semantic"] += 1
            return len(results)
        except Exception as e:
            with self.stats_lock:
                self.stats["errors"] += 1
            return 0
    
    def simulate_inference(self, graph_data):
        """模拟图推理"""
        if graph_data and graph_data.get("nodes"):
            start_node = random.choice(graph_data["nodes"])["label"]
            try:
                results = self.memory.infer(start_node, max_depth=random.randint(2, 4))
                with self.stats_lock:
                    self.stats["infer"] += 1
                return len(results)
            except Exception as e:
                with self.stats_lock:
                    self.stats["errors"] += 1
                return 0
        return 0
    
    def simulate_recommendation(self, graph_data):
        """模拟推荐"""
        if graph_data and graph_data.get("nodes"):
            node = random.choice(graph_data["nodes"])["label"]
            try:
                recs = self.memory.recommend_connections(node, k=random.randint(3, 10))
                with self.stats_lock:
                    self.stats["recommend"] += 1
                return len(recs)
            except Exception as e:
                with self.stats_lock:
                    self.stats["errors"] += 1
                return 0
        return 0
    
    def simulate_add_knowledge(self):
        """模拟添加新知识"""
        types = [NodeType.ENTITY, NodeType.CONCEPT, NodeType.DOCUMENT]
        node_type = random.choice(types)
        node_label = f"knowledge_{int(time.time() * 1000)}_{random.randint(0, 1000)}"
        try:
            self.memory.remember(
                node_label,
                properties={
                    "timestamp": time.time(),
                    "source": "test",
                    "priority": random.randint(1, 5)
                },
                node_type=node_type
            )
            with self.stats_lock:
                self.stats["add_node"] += 1
            return True
        except Exception as e:
            with self.stats_lock:
                self.stats["errors"] += 1
            return False
    
    def simulate_connect_knowledge(self, graph_data):
        """模拟连接知识"""
        if graph_data and len(graph_data.get("nodes", [])) >= 2:
            nodes = [n["label"] for n in graph_data["nodes"]]
            a = random.choice(nodes)
            b = random.choice(nodes)
            if a != b:
                edge_types = [e.value for e in EdgeType.all()]
                try:
                    self.memory.connect(a, b, random.choice(edge_types))
                    with self.stats_lock:
                        self.stats["add_edge"] += 1
                    return True
                except Exception as e:
                    with self.stats_lock:
                        self.stats["errors"] += 1
        return False

# ===========================================================================
# 测试主类
# ===========================================================================

class UltimateRealWorldTest:
    """终极真实世界测试"""
    
    def __init__(self, duration_seconds=1800):  # 30分钟
        self.duration = duration_seconds
        self.memory = None
        self.stop_flag = threading.Event()
        self.simulator = None
        self.start_time = None
        self.results = {
            "start_time": None,
            "end_time": None,
            "duration": 0,
            "stats": {},
            "success": True,
            "checkpoints": []
        }
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
    
    def run(self):
        """运行完整测试"""
        print("=" * 80)
        print("🚀 知识图谱记忆系统 v7.0 - 终极真实世界场景测试")
        print("=" * 80)
        print(f"目标时长: {self.duration}秒 ({self.duration/60:.1f}分钟)")
        
        # 初始化和记录开始时间
        self.start_time = time.time()
        self.memory = MemorySystemV7()
        self.simulator = ComplexOperationSimulator(self.memory)
        self.results["start_time"] = datetime.now().isoformat()
        
        # 阶段1: 构建基础数据
        self.log("阶段1: 构建真实世界知识图谱...")
        self.phase_1_build_initial_data()
        
        # 阶段2: 多线程操作（主测试阶段，持续到目标时长）
        self.log("阶段2: 多线程真实场景操作...")
        self.phase_2_multi_thread_operations()
        
        # 阶段3: 高级功能测试
        self.log("阶段3: 高级功能压力测试...")
        self.phase_3_advanced_features()
        
        # 完成
        self.complete_test()
        return self.results
    
    def phase_1_build_initial_data(self):
        """构建初始知识图谱"""
        start_time = time.time()
        
        self.log("  生成Python代码库...")
        python_modules = RealWorldDataGenerator.generate_python_codebase(self.memory, num_modules=80)
        
        self.log("  生成JavaScript项目...")
        js_files = RealWorldDataGenerator.generate_javascript_project(self.memory, num_files=60)
        
        self.log("  生成技术概念和文档...")
        concepts, docs = RealWorldDataGenerator.generate_concepts_and_documents(self.memory, num_docs=50)
        
        duration = time.time() - start_time
        stats = self.memory.get_statistics()
        self.log(f"  完成! 节点: {stats['nodes']}, 边: {stats['edges']}, 耗时: {duration:.1f}秒")
        
        self.results["checkpoints"].append({
            "phase": 1,
            "nodes": stats['nodes'],
            "edges": stats['edges'],
            "duration": duration
        })
    
    def phase_2_multi_thread_operations(self):
        """多线程操作 - 运行到目标时长"""
        num_threads = 15
        
        self.log(f"  启动 {num_threads}个线程...")
        
        def worker(worker_id):
            last_graph = None
            thread_ops = 0
            
            while not self.stop_flag.is_set():
                # 检查时间是否超过
                if time.time() - self.start_time >= self.duration:
                    break
                
                # 获取当前图状态（偶尔）
                if thread_ops % 20 == 0:
                    try:
                        last_graph = self.memory.get_graph_for_visualization()
                    except:
                        pass
                
                # 随机选择操作
                operation = random.choice([
                    "search", "semantic", "infer", "recommend",
                    "add", "connect"
                ])
                
                if operation == "search":
                    self.simulator.simulate_user_search()
                elif operation == "semantic":
                    self.simulator.simulate_semantic_search()
                elif operation == "infer" and last_graph:
                    self.simulator.simulate_inference(last_graph)
                elif operation == "recommend" and last_graph:
                    self.simulator.simulate_recommendation(last_graph)
                elif operation == "add":
                    self.simulator.simulate_add_knowledge()
                elif operation == "connect" and last_graph:
                    self.simulator.simulate_connect_knowledge(last_graph)
                
                thread_ops += 1
        
        threads = []
        start_time = time.time()
        last_checkpoint = 0
        
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # 监控线程
        def monitor():
            nonlocal last_checkpoint
            while not self.stop_flag.is_set():
                elapsed = time.time() - start_time
                
                # 检查是否达到目标时长
                if elapsed >= self.duration:
                    self.log(f"  达到目标时长 {self.duration}秒！")
                    self.stop_flag.set()
                    break
                
                if elapsed - last_checkpoint >= 60:
                    stats = self.memory.get_statistics()
                    op_stats = self.simulator.stats.copy()
                    
                    total_ops = sum(op_stats[k] for k in op_stats if k != "errors")
                    rate = total_ops / elapsed if elapsed > 0 else 0
                    remaining = self.duration - elapsed
                    
                    self.log(f"  检查点: 节点 {stats['nodes']}, 边 {stats['edges']}, "
                            f"操作 {total_ops}, 速率 {rate:.1f} ops/s, "
                            f"错误 {op_stats['errors']}, 剩余 {int(remaining)}秒")
                    
                    self.results["checkpoints"].append({
                        "phase": 2,
                        "elapsed": elapsed,
                        "nodes": stats['nodes'],
                        "edges": stats['edges'],
                        "operations": op_stats.copy()
                    })
                    
                    last_checkpoint = elapsed
                
                time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 等待完成
        for t in threads:
            t.join()
        
        # 停止监控
        self.stop_flag.set()
        monitor_thread.join(timeout=2)
        
        duration = time.time() - start_time
        self.log(f"  多线程阶段完成! 耗时: {duration:.1f}秒")
        
        # 收集最终统计
        self.results["stats"] = self.simulator.stats
        
        final_stats = self.memory.get_statistics()
        self.log(f"  最终状态: 节点 {final_stats['nodes']}, 边 {final_stats['edges']}")
    
    def phase_3_advanced_features(self):
        """高级功能测试"""
        start_time = time.time()
        
        self.log("  计算GNN嵌入...")
        gnn_start = time.time()
        try:
            self.memory.compute_gnn_embeddings()
            gnn_duration = time.time() - gnn_start
            stats = self.memory.get_statistics()
            self.log(f"  GNN完成! 嵌入数: {stats.get('embeddings_count', 0)}, 耗时: {gnn_duration:.2f}秒")
        except Exception as e:
            self.log(f"  GNN错误: {e}")
        
        self.log("  密集语义搜索...")
        semantic_count = 0
        semantic_start = time.time()
        queries = ["python machine learning", "web development framework", "data science",
                  "javascript react", "database optimization", "api design"]
        for _ in range(100):
            query = random.choice(queries)
            try:
                self.memory.semantic_search(query, k=random.randint(5, 15))
                semantic_count += 1
            except:
                pass
        semantic_duration = time.time() - semantic_start
        self.log(f"  完成 {semantic_count}次语义搜索, 耗时: {semantic_duration:.2f}秒")
        
        self.log("  深度图推理...")
        graph_data = self.memory.get_graph_for_visualization()
        if graph_data and graph_data["nodes"]:
            infer_count = 0
            infer_start = time.time()
            for i in range(50):
                node = random.choice(graph_data["nodes"])["label"]
                try:
                    self.memory.infer(node, max_depth=random.randint(3, 6))
                    infer_count += 1
                except:
                    pass
            infer_duration = time.time() - infer_start
            self.log(f"  完成 {infer_count}次深度推理, 耗时: {infer_duration:.2f}秒")
        
        duration = time.time() - start_time
        self.log(f"  高级功能阶段完成! 耗时: {duration:.1f}秒")
    
    def complete_test(self):
        """完成测试并生成报告"""
        final_stats = self.memory.get_statistics()
        
        self.results["end_time"] = datetime.now().isoformat()
        self.results["duration"] = time.time() - datetime.fromisoformat(self.results["start_time"]).timestamp()
        self.results["final_stats"] = final_stats
        
        # 生成报告
        print("\n" + "=" * 80)
        print("📋 终极真实世界场景测试 - 最终报告")
        print("=" * 80)
        
        print(f"\n⏱️  时间统计:")
        print(f"  目标时长: {self.duration}秒")
        print(f"  实际时长: {self.results['duration']:.1f}秒")
        
        print(f"\n📊 最终状态:")
        print(f"  节点数: {final_stats['nodes']:,}")
        print(f"  边数: {final_stats['edges']:,}")
        print(f"  嵌入数: {final_stats.get('embeddings_count', 0):,}")
        
        print(f"\n⚡ 操作统计:")
        ops = self.results.get("stats", {})
        for key in sorted(ops.keys()):
            if key != "errors":
                print(f"  {key}: {ops[key]:,}")
        
        total_ops = sum(ops[k] for k in ops if k != "errors")
        error_count = ops.get("errors", 0)
        print(f"\n  总操作: {total_ops:,}")
        print(f"  错误数: {error_count:,}")
        print(f"  成功率: {(100 * (total_ops - error_count) / max(total_ops, 1)):.2f}%")
        
        print(f"\n📊 检查点数: {len(self.results.get('checkpoints', []))}")
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(__file__), "v7_ultimate_real_world_test_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 报告保存: {report_path}")
        
        print("\n" + "=" * 80)
        if error_count == 0:
            print("🎉 完美通过! 系统表现极其稳定!")
        else:
            print("✅ 测试完成!")
        print("=" * 80)


if __name__ == "__main__":
    test = UltimateRealWorldTest(duration_seconds=1800)  # 30分钟
    test.run()

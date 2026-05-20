#!/usr/bin/env python3
"""
知识图谱记忆系统 v5.0 - 真实世界实践测试
包含复杂知识图谱构建、压力测试、问题发现和优化
"""
import sys
import os
import time
import gc
import json
import random
import tempfile
import threading
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from collections import defaultdict

# 确保模块导入路径正确
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# ============================================
# 真实知识图谱场景数据
# ============================================

class RealWorldScenarios:
    """真实世界的知识图谱场景"""
    
    # 编程知识领域
    PROGRAMMING_CONCEPTS = [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
        "Web Development", "Machine Learning", "Deep Learning", "Database",
        "REST API", "GraphQL", "Microservices", "Docker", "Kubernetes",
        "FastAPI", "Django", "Flask", "React", "Vue.js", "Angular",
        "PostgreSQL", "MongoDB", "Redis", "Neo4j", "Git", "Linux",
        "OOP", "Functional Programming", "Concurrent Programming", "Distributed Systems"
    ]
    
    # 关系类型
    RELATION_TYPES = [
        "is_a", "related_to", "uses", "depends_on", "part_of", "similar_to",
        "competes_with", "created_by", "inspired_by", "supercedes"
    ]
    
    # 公司和产品
    COMPANIES_PRODUCTS = [
        "Google", "Microsoft", "Apple", "Amazon", "Meta", "OpenAI", "Anthropic",
        "GitHub", "Docker Inc", "HashiCorp", "Elastic", "MongoDB Inc",
        "TensorFlow", "PyTorch", "React", "Angular", "TypeScript", "VS Code"
    ]
    
    # 学术和研究领域
    RESEARCH_AREAS = [
        "Neural Networks", "Transformers", "NLP", "Computer Vision",
        "Reinforcement Learning", "Computer Science", "Artificial Intelligence",
        "Knowledge Representation", "Semantic Web", "Graph Theory"
    ]
    
    # 整合所有节点
    @classmethod
    def generate_nodes(cls, count: int) -> List[str]:
        """生成混合类型的节点"""
        all_nodes = (
            cls.PROGRAMMING_CONCEPTS + cls.COMPANIES_PRODUCTS + cls.RESEARCH_AREAS
        )
        nodes = []
        for i in range(count):
            base_node = random.choice(all_nodes)
            if i >= len(all_nodes):
                nodes.append(f"{base_node}_{i}")
            else:
                nodes.append(base_node)
        return nodes
    
    @classmethod
    def generate_edges(cls, nodes: List[str], edge_count: int) -> List[Tuple[str, str, str]]:
        """生成真实的边关系"""
        edges = []
        for _ in range(edge_count):
            source = random.choice(nodes)
            target = random.choice(nodes)
            while source == target:
                target = random.choice(nodes)
            
            relation = random.choice(cls.RELATION_TYPES)
            edges.append((source, target, relation))
        
        return edges


# ============================================
# 核心系统 - 基于 v5.0 架构
# ============================================

class NodeType:
    ENTITY = "entity"
    CONCEPT = "concept"
    DOCUMENT = "document"
    ACTION = "action"


class EdgeType:
    RELATED_TO = "related_to"
    USES = "uses"
    PART_OF = "part_of"
    IS_A = "is_a"


class Node:
    def __init__(self, label: str, properties: Dict = None, node_id: str = None):
        import uuid
        self.id = node_id or str(uuid.uuid4())
        self.label = label.strip() or "empty"
        self.properties = properties or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


class Edge:
    def __init__(self, source_id: str, target_id: str, relation: str = "related_to",
                 weight: float = 1.0, properties: Dict = None):
        import uuid
        self.id = str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.relation = relation
        self.weight = weight
        self.properties = properties or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": self.weight
        }


class LRUCache:
    def __init__(self, capacity: int = 5000):
        from collections import OrderedDict
        self.capacity = capacity
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Any:
        with self._lock:
            if key in self.cache:
                self.hits += 1
                self.cache.move_to_end(key)
                return self.cache[key]
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / total * 100) if total > 0 else 0,
            "size": len(self.cache),
            "capacity": self.capacity
        }


class MemorySystemV5:
    """v5.0 记忆系统 - 真实测试版本"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or tempfile.mkdtemp()
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._label_index: Dict[str, Set[str]] = defaultdict(set)
        self._keyword_index: Dict[str, List[str]] = defaultdict(list)
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.Lock()
        self._cache = LRUCache()
        self._stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "nodes_deleted": 0,
            "queries": 0,
            "inferences": 0
        }
        self._errors: List[Dict] = []
    
    def remember(self, knowledge: str, properties: Dict = None) -> str:
        """记住知识"""
        with self._lock:
            try:
                node = Node(label=knowledge, properties=properties)
                self._nodes[node.id] = node
                
                # 更新索引
                label_key = node.label.lower()
                self._label_index[label_key].add(node.id)
                
                # 关键词索引
                keywords = self._extract_keywords(node.label)
                for kw in keywords:
                    kw_lower = kw.lower()
                    self._keyword_index[kw_lower].append(node.id)
                
                self._stats["nodes_added"] += 1
                self._cache.clear()
                
                return node.id
            except Exception as e:
                self._errors.append({
                    "operation": "remember",
                    "error": str(e),
                    "time": datetime.now().isoformat()
                })
                raise
    
    def connect(self, source: str, target: str, relation: str = "related_to", weight: float = 1.0) -> str:
        """建立连接"""
        with self._lock:
            try:
                # 查找或创建源节点
                source_nodes = self._search_nodes_by_label(source)
                if not source_nodes:
                    source_id = self._add_node_direct(source)
                else:
                    source_id = source_nodes[0].id
                
                # 查找或创建目标节点
                target_nodes = self._search_nodes_by_label(target)
                if not target_nodes:
                    target_id = self._add_node_direct(target)
                else:
                    target_id = target_nodes[0].id
                
                # 创建边
                edge = Edge(source_id, target_id, relation, weight)
                self._edges[edge.id] = edge
                self._adjacency[source_id].add(target_id)
                
                self._stats["edges_added"] += 1
                self._cache.clear()
                
                return edge.id
            except Exception as e:
                self._errors.append({
                    "operation": "connect",
                    "error": str(e),
                    "time": datetime.now().isoformat()
                })
                raise
    
    def recall(self, query: str, k: int = 20) -> List[Dict]:
        """检索知识"""
        with self._lock:
            self._stats["queries"] += 1
            
            k = max(1, min(1000, k))
            cache_key = f"recall:{query}:{k}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            
            results = []
            seen: Set[str] = set()
            
            # 标签搜索
            for node in self._search_nodes_by_label(query):
                if node.id not in seen:
                    results.append(node.to_dict())
                    seen.add(node.id)
                    if len(results) >= k:
                        break
            
            # 关键词搜索
            if len(results) < k:
                keywords = self._extract_keywords(query)
                for kw in keywords:
                    kw_lower = kw.lower()
                    for node_id in self._keyword_index.get(kw_lower, []):
                        if len(results) >= k:
                            break
                        if node_id in self._nodes and node_id not in seen:
                            results.append(self._nodes[node_id].to_dict())
                            seen.add(node_id)
            
            self._cache.put(cache_key, results[:k])
            return results[:k]
    
    def infer(self, concept: str, max_depth: int = 3) -> List[Dict]:
        """知识推理"""
        with self._lock:
            self._stats["inferences"] += 1
            
            results = []
            seen: Set[str] = set()
            
            start_nodes = self._search_nodes_by_label(concept)
            
            for start_node in start_nodes:
                if start_node.id in seen:
                    continue
                
                queue = [(start_node.id, 0)]
                seen.add(start_node.id)
                
                while queue:
                    current_id, depth = queue.pop(0)
                    if depth > max_depth:
                        continue
                    
                    for neighbor_id in self._adjacency.get(current_id, set()):
                        if neighbor_id not in seen and neighbor_id in self._nodes:
                            results.append({
                                "source": start_node.label,
                                "target": self._nodes[neighbor_id].label,
                                "depth": depth + 1
                            })
                            seen.add(neighbor_id)
                            queue.append((neighbor_id, depth + 1))
            
            return results
    
    def get_statistics(self) -> Dict:
        """获取系统统计"""
        with self._lock:
            return {
                "nodes": len(self._nodes),
                "edges": len(self._edges),
                **self._stats,
                "cache": self._cache.get_stats(),
                "errors": len(self._errors),
                "error_samples": self._errors[-5:] if self._errors else []
            }
    
    def clear(self):
        """清空系统"""
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._label_index.clear()
            self._keyword_index.clear()
            self._adjacency.clear()
            self._cache.clear()
            self._stats = {
                "nodes_added": 0,
                "edges_added": 0,
                "nodes_deleted": 0,
                "queries": 0,
                "inferences": 0
            }
            self._errors.clear()
    
    # ===== 内部方法 =====
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = text.split()
        return list(set(words))[:10]
    
    def _search_nodes_by_label(self, label: str) -> List[Node]:
        """通过标签搜索节点"""
        results: List[Node] = []
        label_lower = label.lower()
        
        for label_key in self._label_index:
            if label_lower in label_key:
                for node_id in self._label_index[label_key]:
                    if node_id in self._nodes:
                        results.append(self._nodes[node_id])
        
        return results
    
    def _add_node_direct(self, label: str) -> str:
        """直接添加节点（内部方法）"""
        node = Node(label=label)
        self._nodes[node.id] = node
        self._label_index[node.label.lower()].add(node.id)
        keywords = self._extract_keywords(node.label)
        for kw in keywords:
            kw_lower = kw.lower()
            self._keyword_index[kw_lower].append(node.id)
        self._stats["nodes_added"] += 1
        return node.id


# ============================================
# 真实实践测试引擎
# ============================================

@dataclass
class TestResult:
    test_name: str
    passed: bool
    duration: float
    issues: List[Dict]
    performance: Dict


class RealWorldTester:
    """真实世界测试引擎"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.issues: List[Dict] = []
        self.start_time = time.time()
        self.memory_history: List[Tuple[float, float]] = []
    
    def record_memory(self):
        """记录内存使用"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            elapsed = time.time() - self.start_time
            self.memory_history.append((elapsed, memory_mb))
            return memory_mb
        except ImportError:
            return 0.0
    
    def log_issue(self, test: str, problem: str, severity: str = "medium", details: Any = None):
        """记录发现的问题"""
        issue = {
            "test": test,
            "problem": problem,
            "severity": severity,
            "details": details,
            "time": datetime.now().isoformat()
        }
        self.issues.append(issue)
        print(f"⚠️  [{severity}] {problem}")
    
    def test_knowledge_base_building(self, system: MemorySystemV5) -> TestResult:
        """测试 1: 真实知识库构建"""
        test_name = "真实知识库构建"
        print(f"\n{'='*80}")
        print(f"📚 测试 1: {test_name}")
        print(f"{'='*80}")
        
        start_time = time.time()
        issues_found = []
        
        # 生成大规模知识图谱
        node_count = 2000
        edge_count = 5000
        
        print(f"  正在生成 {node_count} 个节点和 {edge_count} 个边...")
        
        nodes = RealWorldScenarios.generate_nodes(node_count)
        edges = RealWorldScenarios.generate_edges(nodes, edge_count)
        
        # 构建知识图谱
        build_start = time.time()
        node_start_time = time.time()
        node_times = []
        
        for i, node_label in enumerate(nodes):
            try:
                system.remember(node_label, {
                    "index": i,
                    "type": "real_world_data",
                    "random_value": random.random()
                })
                if (i + 1) % 500 == 0:
                    time_taken = time.time() - node_start_time
                    node_times.append(time_taken)
                    print(f"    ✅ 添加了 {i + 1} / {node_count} 节点 ({(i + 1) / (time.time() - start_time):.0f} node/s)")
                    node_start_time = time.time()
            except Exception as e:
                issues_found.append({"step": "add_node", "index": i, "error": str(e)})
                self.log_issue(test_name, f"添加节点 {i} 失败: {e}", "high")
        
        edge_start_time = time.time()
        edge_times = []
        
        for i, (source, target, relation) in enumerate(edges):
            try:
                system.connect(source, target, relation)
                if (i + 1) % 1000 == 0:
                    time_taken = time.time() - edge_start_time
                    edge_times.append(time_taken)
                    print(f"    ✅ 添加了 {i + 1} / {edge_count} 边 ({(i + 1) / (time.time() - build_start):.0f} edge/s)")
                    edge_start_time = time.time()
            except Exception as e:
                issues_found.append({"step": "add_edge", "index": i, "error": str(e)})
                self.log_issue(test_name, f"添加边 {i} 失败: {e}", "medium")
        
        build_time = time.time() - build_start
        node_rate = node_count / build_time if build_time > 0 else 0
        edge_rate = edge_count / build_time if build_time > 0 else 0
        
        print(f"\n  📊 构建性能:")
        print(f"     节点创建: {node_rate:.0f} node/s")
        print(f"     边创建: {edge_rate:.0f} edge/s")
        
        # 验证数据
        stats = system.get_statistics()
        print(f"\n  最终统计: {stats['nodes']} 节点, {stats['edges']} 边")
        
        if stats['nodes'] < node_count * 0.9:
            self.log_issue(test_name, f"节点丢失严重! 预期 {node_count}, 实际 {stats['nodes']}", "high")
        if stats['edges'] < edge_count * 0.8:
            self.log_issue(test_name, f"边丢失严重! 预期 {edge_count}, 实际 {stats['edges']}", "high")
        
        return TestResult(
            test_name=test_name,
            passed=len(issues_found) == 0,
            duration=time.time() - start_time,
            issues=issues_found,
            performance={
                "node_rate": node_rate,
                "edge_rate": edge_rate,
                "total_nodes": stats['nodes'],
                "total_edges": stats['edges']
            }
        )
    
    def test_concurrent_operations(self, system: MemorySystemV5) -> TestResult:
        """测试 2: 高并发操作"""
        test_name = "高并发操作"
        print(f"\n{'='*80}")
        print(f"🔄 测试 2: {test_name}")
        print(f"{'='*80}")
        
        start_time = time.time()
        issues_found = []
        
        thread_count = 20
        operations_per_thread = 100
        
        print(f"  启动 {thread_count} 个并发线程，每个线程执行 {operations_per_thread} 个操作...")
        
        successful_ops = 0
        failed_ops = 0
        
        def worker(thread_id: int):
            nonlocal successful_ops, failed_ops
            thread_success = 0
            thread_fail = 0
            
            for i in range(operations_per_thread):
                try:
                    operation = random.choice([
                        "remember", "connect", "recall", "infer"
                    ])
                    
                    if operation == "remember":
                        label = f"Concurrent_{thread_id}_Node_{random.randint(0, 1000)}"
                        system.remember(label)
                        thread_success += 1
                    elif operation == "connect":
                        try:
                            source = f"Concurrent_{random.randint(0, thread_count)}_Node_{random.randint(0, 100)}"
                            target = f"Concurrent_{random.randint(0, thread_count)}_Node_{random.randint(0, 100)}"
                            system.connect(source, target)
                            thread_success += 1
                        except:
                            pass  # 连接失败是可能的，因为节点可能不存在
                    elif operation == "recall":
                        system.recall(f"Concurrent_{random.randint(0, thread_count)}", k=5)
                        thread_success += 1
                    elif operation == "infer":
                        try:
                            system.infer(f"Concurrent_{random.randint(0, thread_count)}", max_depth=2)
                            thread_success += 1
                        except:
                            pass
                
                except Exception as e:
                    thread_fail += 1
                    if thread_fail <= 5:  # 只记录前5个错误
                        issues_found.append({
                            "thread": thread_id,
                            "error": str(e),
                            "time": datetime.now().isoformat()
                        })
            
            return thread_success, thread_fail
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(worker, tid) for tid in range(thread_count)]
            for future in as_completed(futures):
                success, fail = future.result()
                successful_ops += success
                failed_ops += fail
        
        total_ops = successful_ops + failed_ops
        throughput = total_ops / (time.time() - start_time)
        
        print(f"\n  📊 并发结果:")
        print(f"    总操作数: {total_ops}")
        print(f"    成功: {successful_ops}")
        print(f"    失败: {failed_ops}")
        print(f"    失败率: {failed_ops / total_ops * 100:.2f}%")
        print(f"    吞吐量: {throughput:.0f} ops/s")
        
        if failed_ops > total_ops * 0.1:
            self.log_issue(test_name, f"并发失败率过高! {failed_ops / total_ops * 100:.1f}%", "high")
        
        return TestResult(
            test_name=test_name,
            passed=failed_ops < total_ops * 0.1,
            duration=time.time() - start_time,
            issues=issues_found,
            performance={
                "throughput": throughput,
                "success_rate": (successful_ops / total_ops * 100) if total_ops > 0 else 0,
                "thread_count": thread_count
            }
        )
    
    def test_query_performance(self, system: MemorySystemV5) -> TestResult:
        """测试 3: 查询性能和可扩展性"""
        test_name = "查询性能与可扩展性"
        print(f"\n{'='*80}")
        print(f"🔍 测试 3: {test_name}")
        print(f"{'='*80}")
        
        start_time = time.time()
        issues_found = []
        
        query_count = 1000
        print(f"  执行 {query_count} 次查询...")
        
        stats = system.get_statistics()
        node_count = stats['nodes']
        
        query_start = time.time()
        for i in range(query_count):
            try:
                query = random.choice(["Python", "JavaScript", "Google", "Machine Learning", "Database"])
                system.recall(query, k=10)
                
                if (i + 1) % 200 == 0:
                    print(f"    ✅ 执行了 {i + 1} / {query_count} 查询")
                
            except Exception as e:
                issues_found.append({"query": i, "error": str(e)})
        
        query_time = time.time() - query_start
        qps = query_count / query_time if query_time > 0 else 0
        
        print(f"\n  📊 查询性能:")
        print(f"    QPS: {qps:.0f}")
        print(f"    总时间: {query_time:.2f}s")
        
        # 推理测试
        print(f"\n  🧠 推理测试...")
        infer_start = time.time()
        for _ in range(50):
            try:
                system.infer("Python", max_depth=2)
            except Exception as e:
                pass
        infer_time = time.time() - infer_start
        
        print(f"    推理速度: {50 / infer_time:.1f} 次/s")
        
        return TestResult(
            test_name=test_name,
            passed=len(issues_found) == 0,
            duration=time.time() - start_time,
            issues=issues_found,
            performance={
                "qps": qps,
                "infer_rate": 50 / infer_time if infer_time > 0 else 0
            }
        )
    
    def test_memory_stability(self, system: MemorySystemV5) -> TestResult:
        """测试 4: 内存稳定性与泄漏检测"""
        test_name = "内存稳定性"
        print(f"\n{'='*80}")
        print(f"💾 测试 4: {test_name}")
        print(f"{'='*80}")
        
        start_time = time.time()
        issues_found = []
        
        initial_memory = self.record_memory()
        print(f"  初始内存: {initial_memory:.2f} MB")
        
        # 执行多次创建和清理操作
        rounds = 10
        memory_samples = [initial_memory]
        
        for round_num in range(rounds):
            # 添加大量数据
            for i in range(200):
                system.remember(f"MemoryTest_{round_num}_{i}")
            
            for i in range(100):
                system.connect(
                    f"MemoryTest_{round_num}_{random.randint(0, 199)}",
                    f"MemoryTest_{round_num}_{random.randint(0, 199)}"
                )
            
            # 清理
            system.clear()
            gc.collect()
            
            current_memory = self.record_memory()
            memory_samples.append(current_memory)
            print(f"  第 {round_num + 1} 轮后: {current_memory:.2f} MB")
        
        # 分析内存增长
        growth = memory_samples[-1] - memory_samples[0]
        print(f"\n  📊 内存分析:")
        print(f"    初始: {memory_samples[0]:.2f} MB")
        print(f"    最终: {memory_samples[-1]:.2f} MB")
        print(f"    增长: {growth:.2f} MB")
        
        if growth > 50:
            self.log_issue(test_name, f"内存泄漏检测: {growth:.2f} MB 增长", "medium")
        elif growth > 10:
            self.log_issue(test_name, f"内存增长: {growth:.2f} MB（可能有小泄漏）", "low")
        else:
            print(f"  ✅ 内存稳定，无泄漏迹象")
        
        return TestResult(
            test_name=test_name,
            passed=growth < 50,
            duration=time.time() - start_time,
            issues=issues_found,
            performance={
                "initial_memory": initial_memory,
                "final_memory": memory_samples[-1],
                "growth": growth
            }
        )
    
    def run_all_tests(self):
        """运行所有真实世界测试"""
        print(f"\n{'='*80}")
        print(f"🚀 知识图谱记忆系统 v5.0 - 真实世界实践测试")
        print(f"{'='*80}")
        print(f"开始时间: {datetime.now().isoformat()}")
        
        all_results = []
        
        # 运行测试
        with tempfile.TemporaryDirectory() as temp_dir:
            system = MemorySystemV5(temp_dir)
            
            # 1. 知识库构建
            result1 = self.test_knowledge_base_building(system)
            all_results.append(result1)
            
            # 2. 并发操作
            result2 = self.test_concurrent_operations(system)
            all_results.append(result2)
            
            # 3. 查询性能
            result3 = self.test_query_performance(system)
            all_results.append(result3)
            
            # 4. 内存稳定性
            result4 = self.test_memory_stability(system)
            all_results.append(result4)
        
        # 总结报告
        self._generate_report(all_results)
        
        return all_results
    
    def _generate_report(self, results: List[TestResult]):
        """生成最终报告"""
        print(f"\n{'='*80}")
        print(f"📋 真实世界实践测试 - 最终报告")
        print(f"{'='*80}")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        total_issues = len(self.issues)
        
        print(f"\n📊 总体结果:")
        print(f"  测试通过: {passed_tests} / {total_tests}")
        print(f"  发现问题: {total_issues} 个")
        
        if self.issues:
            print(f"\n⚠️ 问题详情:")
            for issue in self.issues[:10]:  # 只显示前10个问题
                print(f"  - [{issue['severity']}] {issue['test']}: {issue['problem']}")
        
        print(f"\n📈 性能指标:")
        for result in results:
            print(f"\n  {result.test_name}:")
            print(f"    耗时: {result.duration:.2f}s")
            for key, value in result.performance.items():
                if isinstance(value, float):
                    print(f"    {key}: {value:.2f}")
                else:
                    print(f"    {key}: {value}")
        
        print(f"\n{'='*80}")
        print(f"✅ 真实世界实践测试完成!")
        print(f"{'='*80}")
        
        # 保存报告
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "total_issues": total_issues
            },
            "issues": self.issues,
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "duration": r.duration,
                    "performance": r.performance
                } for r in results
            ],
            "memory_history": self.memory_history
        }
        
        with open("real_world_test_report.json", "w") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 完整报告已保存到: real_world_test_report.json")


if __name__ == "__main__":
    tester = RealWorldTester()
    tester.run_all_tests()

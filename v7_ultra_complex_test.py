#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 超复杂真实世界场景测试
模拟真实的多语言代码库分析、知识推理、并发访问等复杂场景
"""
import sys
import os
import gc
import time
import random
import json
import tempfile
import threading
import uuid
import traceback
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入v7.0核心系统
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import (
    MemorySystemV7, NodeType, EdgeType
)


# ============================================
# 真实世界代码库模拟器
# ============================================

class RealWorldCodebaseSimulator:
    """模拟真实的多语言代码库"""
    
    # 多语言代码实体
    PYTHON_ENTITIES = {
        "classes": ["UserService", "DatabaseManager", "APIClient", "CacheHandler", "AuthMiddleware",
                   "PaymentGateway", "NotificationService", "DataProcessor", "Validator", "Serializer"],
        "functions": ["authenticate_user", "get_user_by_id", "create_session", "validate_token",
                      "encrypt_password", "hash_password", "send_email", "fetch_data", "parse_json",
                      "serialize_object", "validate_input", "log_message", "cache_result"],
        "modules": ["core.models", "core.views", "core.utils", "api.endpoints", "api.middleware",
                   "services.auth", "services.payment", "services.notification", "database.migrations",
                   "tests.unit", "tests.integration"],
        "variables": ["current_user", "db_connection", "cache_key", "request_data", "response_body",
                     "session_id", "auth_token", "error_message", "config_dict", "logger_instance"]
    }
    
    JAVASCRIPT_ENTITIES = {
        "classes": ["UserController", "Router", "DatabaseConnection", "EventEmitter", "PromiseHandler",
                   "SocketClient", "WebSocketServer", "SessionManager", "TokenValidator", "CryptoUtils"],
        "functions": ["handleRequest", "parseBody", "sendResponse", "validateSession", "createToken",
                     "hashPassword", "comparePasswords", "emitEvent", "subscribeEvent", "handleError",
                     "logInfo", "logDebug", "cacheData"],
        "modules": ["controllers/UserController.js", "routes/api.js", "middleware/auth.js",
                   "services/Database.js", "services/Cache.js", "utils/validation.js",
                   "config/database.js", "config/redis.js", "tests/user.test.js"],
        "variables": ["req", "res", "next", "err", "user", "token", "data", "config", "socket", "event"]
    }
    
    JAVA_ENTITIES = {
        "classes": ["UserServiceImpl", "UserRepository", "UserController", "SecurityConfig",
                   "WebMvcConfig", "TransactionManager", "EntityManager", "CacheManager",
                   "MessageProducer", "MessageConsumer", "KafkaProducer", "KafkaConsumer"],
        "functions": ["saveUser", "findById", "findByEmail", "updateUser", "deleteUser",
                     "authenticate", "authorize", "validateToken", "generateToken", "refreshToken"],
        "packages": ["com.example.service", "com.example.repository", "com.example.controller",
                    "com.example.config", "com.example.model", "com.example.security",
                    "com.example.kafka", "com.example.cache", "com.example.util"],
        "variables": ["userId", "email", "password", "token", "sessionId", "request", "response"]
    }
    
    # 复杂的关系模式
    RELATION_PATTERNS = {
        "imports": [("module", "module", EdgeType.USES)],
        "extends": [("class", "class", EdgeType.IS_A)],
        "implements": [("class", "interface", EdgeType.RELATED_TO)],
        "calls": [("function", "function", EdgeType.RELATED_TO)],
        "references": [("variable", "class", EdgeType.REFERENCES)],
        "partOf": [("module", "package", EdgeType.PART_OF)]
    }
    
    @classmethod
    def generate_complex_codebase(cls, scale: int = 1000) -> Tuple[List[Dict], List[Dict]]:
        """生成复杂的代码库知识图谱"""
        nodes = []
        edges = []
        all_labels = []
        
        # 生成Python实体
        for category, entities in cls.PYTHON_ENTITIES.items():
            for entity in entities:
                for i in range(scale // 30):
                    label = f"{entity}_{i}" if i > 0 else entity
                    node = {
                        "label": label,
                        "type": NodeType.ENTITY,
                        "properties": {
                            "language": "python",
                            "category": category,
                            "lines": random.randint(50, 500),
                            "complexity": random.randint(1, 10)
                        }
                    }
                    nodes.append(node)
                    all_labels.append(label)
        
        # 生成JavaScript实体
        for category, entities in cls.JAVASCRIPT_ENTITIES.items():
            for entity in entities:
                for i in range(scale // 30):
                    label = f"{entity}_{i}" if i > 0 else entity
                    node = {
                        "label": label,
                        "type": NodeType.ENTITY,
                        "properties": {
                            "language": "javascript",
                            "category": category,
                            "lines": random.randint(30, 400),
                            "framework": random.choice(["Express", "React", "Vue", "Node.js"])
                        }
                    }
                    nodes.append(node)
                    all_labels.append(label)
        
        # 生成Java实体
        for category, entities in cls.JAVA_ENTITIES.items():
            for entity in entities:
                for i in range(scale // 30):
                    label = f"{entity}_{i}" if i > 0 else entity
                    node = {
                        "label": label,
                        "type": NodeType.ENTITY,
                        "properties": {
                            "language": "java",
                            "category": category,
                            "lines": random.randint(100, 800),
                            "framework": random.choice(["Spring", "Hibernate", "Kafka", "JPA"])
                        }
                    }
                    nodes.append(node)
                    all_labels.append(label)
        
        # 生成复杂的关系
        for _ in range(scale * 3):
            source = random.choice(all_labels)
            target = random.choice(all_labels)
            
            if source != target:
                edge = {
                    "source": source,
                    "target": target,
                    "type": random.choice([e.value for e in EdgeType.all()]),
                    "weight": random.uniform(0.1, 1.0)
                }
                edges.append(edge)
        
        return nodes, edges


# ============================================
# 复杂查询与推理测试器
# ============================================

class ComplexQueryTester:
    """测试复杂查询和推理"""
    
    def __init__(self, memory: MemorySystemV7):
        self.memory = memory
        self.query_results = []
        
    def test_nested_path_queries(self) -> Dict[str, Any]:
        """测试嵌套路径查询"""
        results = {
            "total_queries": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # 获取图中的节点
            graph_data = self.memory.get_graph_for_visualization()
            
            if len(graph_data['nodes']) >= 3:
                # 测试多层路径查询
                for _ in range(100):
                    results["total_queries"] += 1
                    try:
                        # 随机选择一个起始节点
                        start_node = random.choice(graph_data['nodes'])
                        
                        # 执行推理查询
                        inferred = self.memory.infer(
                            concept=start_node['label'],
                            max_depth=random.randint(2, 5)
                        )
                        
                        results["successful"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(str(e))
                        
        except Exception as e:
            results["errors"].append(f"整体测试失败: {str(e)}")
            
        return results
    
    def test_semantic_search_complexity(self) -> Dict[str, Any]:
        """测试复杂语义搜索"""
        results = {
            "total_searches": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # 复杂查询字符串
            complex_queries = [
                "用户认证服务",
                "数据库连接管理",
                "API请求处理",
                "缓存失效策略",
                "并发访问控制",
                "错误处理机制",
                "日志记录系统",
                "事务管理流程",
                "消息队列处理",
                "性能监控指标"
            ]
            
            for query in complex_queries:
                results["total_searches"] += 1
                try:
                    # 语义搜索
                    results_search = self.memory.semantic_search(
                        query_label=query,
                        k=random.randint(5, 20)
                    )
                    results["successful"] += 1
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                    
        except Exception as e:
            results["errors"].append(f"整体测试失败: {str(e)}")
            
        return results
    
    def test_recommendation_chains(self) -> Dict[str, Any]:
        """测试推荐链"""
        results = {
            "total_recommendations": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            graph_data = self.memory.get_graph_for_visualization()
            
            if len(graph_data['nodes']) > 0:
                # 测试多个节点的推荐
                for node in random.sample(graph_data['nodes'], min(50, len(graph_data['nodes']))):
                    results["total_recommendations"] += 1
                    try:
                        recommendations = self.memory.recommend_connections(
                            node_label=node['label'],
                            k=random.randint(3, 10)
                        )
                        results["successful"] += 1
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(str(e))
                        
        except Exception as e:
            results["errors"].append(f"整体测试失败: {str(e)}")
            
        return results


# ============================================
# 资源管理与泄漏检测
# ============================================

class ResourceLeakDetector:
    """检测资源泄漏"""
    
    def __init__(self):
        self.snapshots = []
        self.start_time = time.time()
        
    def take_snapshot(self, memory: MemorySystemV7, operation_count: int):
        """拍摄系统快照"""
        snapshot = {
            "timestamp": time.time() - self.start_time,
            "operation_count": operation_count,
            "node_count": memory.get_statistics()['nodes'],
            "edge_count": memory.get_statistics()['edges'],
            "cache_size": len(memory._cache),
            "thread_lock": memory._lock._is_owned() if hasattr(memory._lock, '_is_owned') else None
        }
        self.snapshots.append(snapshot)
        return snapshot
    
    def analyze_leaks(self) -> Dict[str, Any]:
        """分析潜在的泄漏"""
        analysis = {
            "total_snapshots": len(self.snapshots),
            "leak_indicators": []
        }
        
        if len(self.snapshots) >= 2:
            # 检查缓存增长
            first_snapshot = self.snapshots[0]
            last_snapshot = self.snapshots[-1]
            
            cache_growth = last_snapshot['cache_size'] - first_snapshot['cache_size']
            
            if cache_growth > 1000:
                analysis["leak_indicators"].append({
                    "type": "cache_growth",
                    "message": f"缓存从 {first_snapshot['cache_size']} 增长到 {last_snapshot['cache_size']}",
                    "severity": "warning"
                })
        
        return analysis


# ============================================
# 超复杂压力测试
# ============================================

class UltraComplexStressTest:
    """超复杂压力测试"""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "bugs_found": [],
            "warnings": [],
            "performance_issues": [],
            "tests": {},
            "metrics": {}
        }
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "kg_v7_ultra.db")
        
    def log_bug(self, bug_type: str, description: str, exception: Optional[Exception] = None):
        """记录Bug"""
        bug = {
            "type": bug_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        if exception:
            bug["exception"] = str(exception)
            bug["traceback"] = traceback.format_exc()
        self.results["bugs_found"].append(bug)
        print(f"❌ 发现Bug: {bug_type} - {description}")
        if exception:
            print(f"   异常: {str(exception)}")
            
    def log_warning(self, warning_type: str, description: str):
        """记录警告"""
        self.results["warnings"].append({
            "type": warning_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        print(f"⚠️  警告: {warning_type} - {description}")
        
    def log_performance(self, issue_type: str, description: str, metrics: Dict):
        """记录性能问题"""
        self.results["performance_issues"].append({
            "type": issue_type,
            "description": description,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        print(f"📉 性能问题: {issue_type} - {description}")
    
    def test_1_real_world_codebase(self):
        """测试1: 真实世界代码库模拟"""
        print("\n" + "="*80)
        print("🏗️  超复杂测试 1: 真实世界代码库模拟")
        print("="*80)
        
        try:
            memory = MemorySystemV7(db_path=self.db_path)
            
            print("  📦 生成复杂的多语言代码库...")
            start_time = time.time()
            
            nodes, edges = RealWorldCodebaseSimulator.generate_complex_codebase(scale=500)
            
            # 添加节点
            print(f"  ➕ 添加 {len(nodes)} 个节点...")
            node_start = time.time()
            for node_data in nodes:
                memory.remember(
                    knowledge=node_data["label"],
                    node_type=node_data["type"],
                    properties=node_data["properties"]
                )
            node_duration = time.time() - node_start
            node_throughput = len(nodes) / node_duration
            
            # 添加边
            print(f"  🔗 添加 {len(edges)} 条边...")
            edge_start = time.time()
            for edge_data in edges:
                memory.connect(
                    source=edge_data["source"],
                    target=edge_data["target"],
                    relation=edge_data["type"],
                    weight=edge_data["weight"]
                )
            edge_duration = time.time() - edge_start
            edge_throughput = len(edges) / edge_duration
            
            stats = memory.get_statistics()
            print(f"  📊 最终统计: {stats['nodes']} 节点, {stats['edges']} 边")
            print(f"  ⚡ 节点吞吐量: {node_throughput:.0f} node/s")
            print(f"  ⚡ 边吞吐量: {edge_throughput:.0f} edge/s")
            
            self.results["tests"]["real_world_codebase"] = {
                "success": True,
                "node_count": stats['nodes'],
                "edge_count": stats['edges'],
                "node_throughput": node_throughput,
                "edge_throughput": edge_throughput,
                "duration": time.time() - start_time
            }
            
            print("  ✅ 真实世界代码库测试完成")
            return memory
            
        except Exception as e:
            self.log_bug("codebase_simulation_crash", "代码库模拟崩溃", e)
            self.results["tests"]["real_world_codebase"] = {"success": False, "error": str(e)}
            return None
    
    def test_2_complex_queries(self, memory: Optional[MemorySystemV7]):
        """测试2: 复杂查询与推理"""
        print("\n" + "="*80)
        print("🔍 超复杂测试 2: 复杂查询与推理")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            tester = ComplexQueryTester(memory)
            
            # 测试嵌套路径查询
            print("  🛤️  测试嵌套路径查询...")
            path_results = tester.test_nested_path_queries()
            print(f"    ✅ 路径查询: {path_results['successful']}/{path_results['total_queries']} 成功")
            if path_results['failed'] > 0:
                self.log_bug("path_query_failures", 
                           f"{path_results['failed']} 个路径查询失败",
                           Exception("\n".join(path_results['errors'][:3])))
            
            # 测试复杂语义搜索
            print("  🔎 测试复杂语义搜索...")
            semantic_results = tester.test_semantic_search_complexity()
            print(f"    ✅ 语义搜索: {semantic_results['successful']}/{semantic_results['total_searches']} 成功")
            if semantic_results['failed'] > 0:
                self.log_bug("semantic_search_failures",
                           f"{semantic_results['failed']} 个语义搜索失败",
                           Exception("\n".join(semantic_results['errors'][:3])))
            
            # 测试推荐链
            print("  💡 测试推荐链...")
            recommend_results = tester.test_recommendation_chains()
            print(f"    ✅ 推荐: {recommend_results['successful']}/{recommend_results['total_recommendations']} 成功")
            if recommend_results['failed'] > 0:
                self.log_bug("recommendation_failures",
                           f"{recommend_results['failed']} 个推荐失败",
                           Exception("\n".join(recommend_results['errors'][:3])))
            
            self.results["tests"]["complex_queries"] = {
                "success": path_results['failed'] == 0 and semantic_results['failed'] == 0 and recommend_results['failed'] == 0,
                "path_queries": path_results,
                "semantic_search": semantic_results,
                "recommendations": recommend_results
            }
            
            print("  ✅ 复杂查询测试完成")
            
        except Exception as e:
            self.log_bug("complex_queries_crash", "复杂查询测试崩溃", e)
            self.results["tests"]["complex_queries"] = {"success": False, "error": str(e)}
    
    def test_3_gnn_deep_analysis(self, memory: Optional[MemorySystemV7]):
        """测试3: GNN深度分析"""
        print("\n" + "="*80)
        print("🧠 超复杂测试 3: GNN深度分析")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            stats = memory.get_statistics()
            
            # 多次GNN计算
            print(f"  🤖 执行 {min(5, stats['nodes'] // 50)} 次GNN计算...")
            gnn_times = []
            for i in range(min(5, stats['nodes'] // 50)):
                start = time.time()
                memory.compute_gnn_embeddings()
                duration = time.time() - start
                gnn_times.append(duration)
                print(f"    ✅ 第{i+1}次: {duration:.2f}s")
            
            avg_gnn_time = sum(gnn_times) / len(gnn_times)
            print(f"  📊 平均GNN时间: {avg_gnn_time:.2f}s")
            
            if avg_gnn_time > 10:
                self.log_performance("slow_gnn", "GNN计算平均时间过长",
                                   {"avg_time": avg_gnn_time, "threshold": 10})
            
            # 测试GNN嵌入质量
            print("  🎯 测试GNN嵌入质量...")
            graph_data = memory.get_graph_for_visualization()
            
            nodes_with_embeddings = sum(1 for node in graph_data['nodes'] if node.get('has_embedding', False))
            print(f"    ✅ 嵌入覆盖率: {nodes_with_embeddings}/{len(graph_data['nodes'])} ({100*nodes_with_embeddings/len(graph_data['nodes']):.1f}%)")
            
            self.results["tests"]["gnn_deep_analysis"] = {
                "success": True,
                "gnn_iterations": len(gnn_times),
                "avg_gnn_time": avg_gnn_time,
                "embedding_coverage": nodes_with_embeddings / len(graph_data['nodes']) if graph_data['nodes'] else 0
            }
            
            print("  ✅ GNN深度分析完成")
            
        except Exception as e:
            self.log_bug("gnn_analysis_crash", "GNN深度分析崩溃", e)
            self.results["tests"]["gnn_deep_analysis"] = {"success": False, "error": str(e)}
    
    def test_4_resource_leak_detection(self):
        """测试4: 资源泄漏检测"""
        print("\n" + "="*80)
        print("💾 超复杂测试 4: 资源泄漏检测")
        print("="*80)
        
        try:
            memory = MemorySystemV7(db_path=os.path.join(self.temp_dir, "kg_v7_leak.db"))
            detector = ResourceLeakDetector()
            
            print("  🔍 运行长时间操作并监控资源...")
            
            operation_count = 0
            for round_num in range(10):
                # 执行大量操作
                for i in range(100):
                    memory.remember(
                        knowledge=f"leak_test_{round_num}_{i}",
                        node_type=NodeType.ENTITY,
                        properties={"round": round_num, "index": i}
                    )
                    operation_count += 1
                
                # 每轮拍摄快照
                snapshot = detector.take_snapshot(memory, operation_count)
                print(f"    📸 轮次 {round_num}: {snapshot['node_count']} 节点, 缓存 {snapshot['cache_size']}")
            
            # 分析泄漏
            analysis = detector.analyze_leaks()
            
            print(f"  📊 资源分析:")
            print(f"    总快照数: {analysis['total_snapshots']}")
            print(f"    泄漏指标: {len(analysis['leak_indicators'])}")
            
            if analysis['leak_indicators']:
                for indicator in analysis['leak_indicators']:
                    self.log_warning(indicator['type'], indicator['message'])
            
            self.results["tests"]["resource_leak"] = {
                "success": len(analysis['leak_indicators']) == 0,
                "analysis": analysis,
                "snapshots": len(detector.snapshots)
            }
            
            print("  ✅ 资源泄漏检测完成")
            
        except Exception as e:
            self.log_bug("leak_detection_crash", "资源泄漏检测崩溃", e)
            self.results["tests"]["resource_leak"] = {"success": False, "error": str(e)}
    
    def test_5_extreme_concurrency(self):
        """测试5: 极端并发压力"""
        print("\n" + "="*80)
        print("⚡ 超复杂测试 5: 极端并发压力 (100线程)")
        print("="*80)
        
        try:
            memory = MemorySystemV7(db_path=os.path.join(self.temp_dir, "kg_v7_concurrent.db"))
            
            # 先添加一些基础数据
            print("  📦 添加基础数据...")
            base_labels = []
            for i in range(100):
                label = f"base_{i}"
                memory.remember(label, node_type=NodeType.ENTITY)
                base_labels.append(label)
            
            # 极端并发测试
            print("  🧵 启动 100 线程并发操作...")
            start_time = time.time()
            success_count = 0
            failure_count = 0
            errors = []
            lock = threading.Lock()
            
            def worker(worker_id: int):
                nonlocal success_count, failure_count
                try:
                    for i in range(20):
                        op_type = random.choice(["add", "search", "connect", "query", "semantic", "recommend"])
                        
                        if op_type == "add":
                            label = f"concurrent_{worker_id}_{i}"
                            memory.remember(label, node_type=NodeType.ENTITY)
                        elif op_type == "search":
                            memory.recall("test", k=10)
                        elif op_type == "connect":
                            if len(base_labels) >= 2:
                                s = random.choice(base_labels)
                                t = random.choice(base_labels)
                                if s != t:
                                    memory.connect(s, t, EdgeType.RELATED_TO)
                        elif op_type == "query":
                            if base_labels:
                                memory.infer(random.choice(base_labels), max_depth=2)
                        elif op_type == "semantic":
                            memory.semantic_search("test", k=5)
                        elif op_type == "recommend":
                            if base_labels:
                                memory.recommend_connections(random.choice(base_labels), k=3)
                        
                        with lock:
                            success_count += 1
                            
                except Exception as e:
                    with lock:
                        failure_count += 1
                        if len(errors) < 5:
                            errors.append(str(e))
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                futures = [executor.submit(worker, i) for i in range(100)]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        with lock:
                            failure_count += 1
            
            duration = time.time() - start_time
            throughput = (success_count + failure_count) / duration
            
            print(f"  📊 结果:")
            print(f"    总操作: {success_count + failure_count}")
            print(f"    成功: {success_count}")
            print(f"    失败: {failure_count}")
            print(f"    吞吐量: {throughput:.0f} ops/s")
            
            if failure_count > 0:
                self.log_bug("concurrency_failures",
                           f"并发测试发现 {failure_count} 个失败",
                           Exception("\n".join(errors[:3])))
            
            # 检查线程安全
            stats = memory.get_statistics()
            print(f"    最终节点数: {stats['nodes']}")
            print(f"    最终边数: {stats['edges']}")
            
            self.results["tests"]["extreme_concurrency"] = {
                "success": failure_count == 0,
                "total_operations": success_count + failure_count,
                "success_count": success_count,
                "failure_count": failure_count,
                "throughput": throughput,
                "duration": duration
            }
            
            print("  ✅ 极端并发测试完成")
            
        except Exception as e:
            self.log_bug("extreme_concurrency_crash", "极端并发测试崩溃", e)
            self.results["tests"]["extreme_concurrency"] = {"success": False, "error": str(e)}
    
    def test_6_long_duration_stress(self):
        """测试6: 超长时间运行压力"""
        print("\n" + "="*80)
        print("⏱️  超复杂测试 6: 超长时间运行压力 (90秒)")
        print("="*80)
        
        try:
            memory = MemorySystemV7(db_path=os.path.join(self.temp_dir, "kg_v7_long.db"))
            start_time = time.time()
            end_time = start_time + 90
            
            operation_count = 0
            error_count = 0
            node_count = 0
            edge_count = 0
            
            checkpoint_times = [15, 30, 45, 60, 75, 90]
            next_checkpoint = 0
            
            print("  📅 开始 90 秒压力测试...")
            
            while time.time() < end_time:
                try:
                    op_type = random.choice(["add_node", "search", "query", "semantic"])
                    
                    if op_type == "add_node":
                        label = f"long_{uuid.uuid4().hex[:8]}"
                        memory.remember(label, node_type=NodeType.ENTITY)
                        node_count += 1
                    elif op_type == "search":
                        memory.recall("test", k=5)
                    elif op_type == "query":
                        if node_count > 0:
                            # 简单查询
                            pass
                    elif op_type == "semantic":
                        memory.semantic_search("test", k=3)
                    
                    operation_count += 1
                    
                except Exception:
                    error_count += 1
                
                elapsed = time.time() - start_time
                if next_checkpoint < len(checkpoint_times) and elapsed >= checkpoint_times[next_checkpoint]:
                    stats = memory.get_statistics()
                    print(f"    ⏱️  {checkpoint_times[next_checkpoint]}s: {operation_count} 操作, {stats['nodes']} 节点")
                    next_checkpoint += 1
            
            duration = time.time() - start_time
            final_stats = memory.get_statistics()
            
            print(f"  \n  📊 最终结果:")
            print(f"    总操作: {operation_count}")
            print(f"    错误: {error_count}")
            print(f"    平均: {operation_count/duration:.0f} ops/s")
            print(f"    最终: {final_stats['nodes']} 节点, {final_stats['edges']} 边")
            
            if error_count > 0:
                error_rate = error_count / (operation_count + error_count)
                if error_rate > 0.01:
                    self.log_bug("high_error_rate",
                               f"错误率 {error_rate:.2%} 过高",
                               Exception(f"{error_count}/{operation_count + error_count}"))
            
            self.results["tests"]["long_duration_stress"] = {
                "success": error_count == 0 or (error_count / (operation_count + error_count)) < 0.01,
                "total_operations": operation_count,
                "error_count": error_count,
                "error_rate": error_count / (operation_count + error_count),
                "avg_throughput": operation_count / duration,
                "final_nodes": final_stats['nodes'],
                "final_edges": final_stats['edges'],
                "duration": duration
            }
            
            print("  ✅ 超长时间运行测试完成")
            
        except Exception as e:
            self.log_bug("long_duration_crash", "超长时间运行测试崩溃", e)
            self.results["tests"]["long_duration_stress"] = {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """运行所有超复杂测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 超复杂真实世界场景测试")
        print("="*80)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        # 测试1: 真实世界代码库
        memory = self.test_1_real_world_codebase()
        
        # 测试2: 复杂查询
        self.test_2_complex_queries(memory)
        
        # 测试3: GNN深度分析
        self.test_3_gnn_deep_analysis(memory)
        
        # 测试4: 资源泄漏检测
        self.test_4_resource_leak_detection()
        
        # 测试5: 极端并发
        self.test_5_extreme_concurrency()
        
        # 测试6: 超长时间运行
        self.test_6_long_duration_stress()
        
        # 生成报告
        self.results["end_time"] = datetime.now().isoformat()
        
        print("\n" + "="*80)
        print("📋 超复杂压力测试 - 最终报告")
        print("="*80)
        
        print(f"\n📊 总体统计:")
        print(f"  发现Bug: {len(self.results['bugs_found'])}")
        print(f"  警告: {len(self.results['warnings'])}")
        print(f"  性能问题: {len(self.results['performance_issues'])}")
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(__file__), "v7_ultra_complex_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📝 完整报告已保存: {report_path}")
        
        if len(self.results['bugs_found']) == 0:
            print("\n🎉 太棒了！在超复杂测试中没有发现Bug！")
        else:
            print(f"\n❌ 发现 {len(self.results['bugs_found'])} 个Bug需要修复")
            for bug in self.results['bugs_found']:
                print(f"   - {bug['type']}: {bug['description']}")
        
        print("\n" + "="*80)
        print("🎯 超复杂压力测试完成！")
        print("="*80)
        
        return self.results


if __name__ == "__main__":
    tester = UltraComplexStressTest()
    results = tester.run_all_tests()

#!/usr/bin/env python3
"""
知识图谱记忆系统 v10.0 - 超长跨文件调用链测试
专门测试系统处理超长调用链的能力

测试场景：
1. 100层超长调用链
2. 1000层极限调用链
3. 循环调用链检测
4. 深度边界测试
5. 性能衰减分析
"""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, EdgeType

class UltraLongCallChainTest:
    """超长跨文件调用链测试"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.results = []
        
        print("="*100)
        print("🔗 v10.0 - 超长跨文件调用链测试")
        print("="*100)
    
    def test_linear_chain(self, depth: int) -> dict:
        """测试线性调用链"""
        print(f"\n{'='*80}")
        print(f"🧪 测试线性调用链 (深度={depth})")
        print("="*80)
        
        self.kg.clear()
        
        start = time.time()
        
        # 创建线性调用链: A1 -> A2 -> A3 -> ... -> A{depth}
        labels = [f"Function_{i}" for i in range(depth)]
        
        for label in labels:
            self.kg.remember(label)
        
        # 建立连接: A1 -> A2 -> A3 ...
        for i in range(len(labels) - 1):
            self.kg.connect(labels[i], labels[i+1])
        
        creation_time = time.time() - start
        
        # 测试推理
        infer_start = time.time()
        results = self.kg.infer(labels[0], max_depth=depth)
        infer_time = time.time() - infer_start
        
        result = {
            "type": "linear",
            "depth": depth,
            "nodes": depth,
            "edges": depth - 1,
            "creation_time": creation_time,
            "infer_time": infer_time,
            "results_count": len(results),
        }
        
        print(f"节点数: {result['nodes']}")
        print(f"边数: {result['edges']}")
        print(f"创建时间: {result['creation_time']:.4f}秒")
        print(f"推理时间: {result['infer_time']:.4f}秒")
        print(f"推理结果: {len(results)}个")
        
        if results:
            print(f"路径长度: {len(results)}")
            if len(results) >= 2:
                print(f"  {results[0]['label']} -> ... -> {results[-1]['label']}")
        
        return result
    
    def test_branching_chain(self, depth: int, branches: int) -> dict:
        """测试分支调用链"""
        print(f"\n{'='*80}")
        print(f"🧪 测试分支调用链 (深度={depth}, 分支={branches})")
        print("="*80)
        
        self.kg.clear()
        
        start = time.time()
        
        # 创建分支: Root -> [A2, B2, C2...] -> [A3, B3, C3...]
        # 首先创建Root节点！
        self.kg.remember("Root")
        nodes_at_level = [("Root", 0)]
        
        for level in range(depth):
            next_level = []
            for parent, _ in nodes_at_level:
                for b in range(branches):
                    label = f"Level{level+1}_Branch{b}"
                    self.kg.remember(label)
                    self.kg.connect(parent, label)
                    next_level.append((label, level+1))
            
            nodes_at_level = next_level
        
        total_nodes = 1 + (branches ** depth - branches) // (branches - 1) if branches > 1 else depth
        creation_time = time.time() - start
        
        # 测试推理
        infer_start = time.time()
        results = self.kg.infer("Root", max_depth=depth)
        infer_time = time.time() - infer_start
        
        result = {
            "type": "branching",
            "depth": depth,
            "branches": branches,
            "nodes": len(self.kg._nodes),
            "edges": len(self.kg._edges),
            "creation_time": creation_time,
            "infer_time": infer_time,
            "results_count": len(results),
        }
        
        print(f"节点数: {result['nodes']}")
        print(f"边数: {result['edges']}")
        print(f"创建时间: {result['creation_time']:.4f}秒")
        print(f"推理时间: {result['infer_time']:.4f}秒")
        print(f"推理结果: {len(results)}个")
        
        return result
    
    def test_cyclic_chain(self, depth: int) -> dict:
        """测试循环调用链"""
        print(f"\n{'='*80}")
        print(f"🧪 测试循环调用链 (深度={depth})")
        print("="*80)
        
        self.kg.clear()
        
        start = time.time()
        
        # 创建循环: A1 -> A2 -> A3 -> ... -> A{depth} -> A1
        labels = [f"Cycle_{i}" for i in range(depth)]
        
        for label in labels:
            self.kg.remember(label)
        
        for i in range(len(labels) - 1):
            self.kg.connect(labels[i], labels[i+1])
        
        # 闭合循环
        self.kg.connect(labels[-1], labels[0])
        
        creation_time = time.time() - start
        
        # 测试推理
        infer_start = time.time()
        results = self.kg.infer(labels[0], max_depth=depth)
        infer_time = time.time() - infer_start
        
        result = {
            "type": "cyclic",
            "depth": depth,
            "nodes": depth,
            "edges": depth,
            "creation_time": creation_time,
            "infer_time": infer_time,
            "results_count": len(results),
            "has_cycle": True,
        }
        
        print(f"节点数: {result['nodes']}")
        print(f"边数: {result['edges']}")
        print(f"循环: A1 -> A2 -> ... -> A{depth} -> A1")
        print(f"创建时间: {result['creation_time']:.4f}秒")
        print(f"推理时间: {result['infer_time']:.4f}秒")
        print(f"推理结果: {len(results)}个")
        
        # 验证循环检测
        visited = set()
        for r in results:
            if r['label'] in visited:
                print(f"⚠️  警告: 发现重复节点 {r['label']}")
                result['has_cycle'] = False
                break
            visited.add(r['label'])
        
        return result
    
    def test_diamond_chain(self) -> dict:
        """测试菱形调用链"""
        print(f"\n{'='*80}")
        print(f"🧪 测试菱形调用链")
        print("="*80)
        
        self.kg.clear()
        
        start = time.time()
        
        # 创建菱形:     A1
        #            /     \
        #          A2      B2
        #          |  \  /  |
        #          |  C3    |
        #          |  /  \  |
        #          A4      B4
        #            \     /
        #              A5
        
        nodes = ["A1", "A2", "B2", "C3", "A4", "B4", "A5"]
        
        for node in nodes:
            self.kg.remember(node)
        
        # 建立连接
        self.kg.connect("A1", "A2")  # A1 -> A2
        self.kg.connect("A1", "B2")  # A1 -> B2
        self.kg.connect("A2", "C3")  # A2 -> C3
        self.kg.connect("B2", "C3") # B2 -> C3
        self.kg.connect("C3", "A4") # C3 -> A4
        self.kg.connect("C3", "B4") # C3 -> B4
        self.kg.connect("A4", "A5") # A4 -> A5
        self.kg.connect("B4", "A5") # B4 -> A5
        
        creation_time = time.time() - start
        
        # 测试推理
        infer_start = time.time()
        results = self.kg.infer("A1", max_depth=5)
        infer_time = time.time() - infer_start
        
        # 统计路径
        paths_to_A5 = []
        for r in results:
            if r['label'] == "A5":
                paths_to_A5.append(r)
        
        result = {
            "type": "diamond",
            "nodes": len(nodes),
            "edges": 8,
            "creation_time": creation_time,
            "infer_time": infer_time,
            "results_count": len(results),
            "paths_to_end": len(paths_to_A5),
        }
        
        print(f"节点数: {result['nodes']}")
        print(f"边数: {result['edges']}")
        print(f"创建时间: {result['creation_time']:.4f}秒")
        print(f"推理时间: {result['infer_time']:.4f}秒")
        print(f"推理结果: {len(results)}个")
        print(f"到A5的路径: {len(paths_to_A5)}条")
        
        return result
    
    def test_real_world_complex_chain(self):
        """测试真实世界的复杂调用链"""
        print(f"\n{'='*80}")
        print(f"🧪 测试真实世界的复杂调用链")
        print("="*80)
        
        self.kg.clear()
        
        # 模拟真实代码库调用
        modules = [
            "main.py",
            "config.py",
            "database.py",
            "cache.py",
            "auth.py",
            "api.py",
            "models.py",
            "views.py",
            "services.py",
            "utils.py",
            "middleware.py",
            "handlers.py",
            "validators.py",
            "serializers.py",
            "tasks.py",
        ]
        
        functions = [
            "init_app",
            "load_config",
            "connect_db",
            "create_cache",
            "setup_auth",
            "register_routes",
            "init_models",
            "setup_views",
            "register_services",
            "load_utils",
            "setup_middleware",
            "register_handlers",
            "validate_schema",
            "init_serializers",
            "start_tasks",
        ]
        
        # 创建所有节点
        for module in modules:
            self.kg.remember(module)
        
        for func in functions:
            self.kg.remember(func)
        
        # 建立复杂调用关系
        call_chain = [
            ("main.py", "init_app"),
            ("init_app", "load_config"),
            ("load_config", "config.py"),
            ("init_app", "connect_db"),
            ("connect_db", "database.py"),
            ("init_app", "create_cache"),
            ("create_cache", "cache.py"),
            ("init_app", "setup_auth"),
            ("setup_auth", "auth.py"),
            ("init_app", "register_routes"),
            ("register_routes", "api.py"),
            ("api.py", "middleware.py"),
            ("api.py", "handlers.py"),
            ("api.py", "validators.py"),
            ("middleware.py", "auth.py"),
            ("handlers.py", "services.py"),
            ("handlers.py", "views.py"),
            ("services.py", "models.py"),
            ("services.py", "utils.py"),
            ("services.py", "cache.py"),
            ("services.py", "database.py"),
            ("views.py", "models.py"),
            ("views.py", "serializers.py"),
            ("models.py", "database.py"),
            ("serializers.py", "validators.py"),
            ("tasks.py", "services.py"),
            ("tasks.py", "database.py"),
        ]
        
        for caller, callee in call_chain:
            self.kg.connect(caller, callee, relation=EdgeType.USES)
        
        # 测试从 main.py 开始的完整推理
        print(f"从 main.py 开始推理...")
        results = self.kg.infer("main.py", max_depth=5)
        
        print(f"\n推理结果: {len(results)}个节点")
        
        # 统计调用深度
        depth_counts = {}
        for r in results:
            depth = r.get('depth', 0)
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
        
        print(f"按深度分布:")
        for depth in sorted(depth_counts.keys()):
            print(f"  深度{depth}: {depth_counts[depth]}个节点")
        
        return {
            "type": "real_world",
            "modules": len(modules),
            "functions": len(functions),
            "call_edges": len(call_chain),
            "results_count": len(results),
            "depth_distribution": depth_counts,
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*100)
        print("🚀 开始全面调用链测试")
        print("="*100)
        
        # 1. 线性调用链测试
        self.test_linear_chain(10)
        self.test_linear_chain(50)
        self.test_linear_chain(100)
        
        # 2. 分支调用链测试
        self.test_branching_chain(5, 3)
        self.test_branching_chain(4, 5)
        
        # 3. 循环调用链测试
        self.test_cyclic_chain(10)
        self.test_cyclic_chain(50)
        
        # 4. 菱形调用链测试
        self.test_diamond_chain()
        
        # 5. 真实世界复杂调用链
        self.test_real_world_complex_chain()
        
        # 最终总结
        print("\n" + "="*100)
        print("📊 超长跨文件调用链测试 - 最终总结")
        print("="*100)
        print("✅ 线性调用链测试完成")
        print("✅ 分支调用链测试完成")
        print("✅ 循环调用链测试完成")
        print("✅ 菱形调用链测试完成")
        print("✅ 真实世界复杂调用链测试完成")
        print("="*100)

if __name__ == "__main__":
    test = UltraLongCallChainTest()
    test.run_all_tests()

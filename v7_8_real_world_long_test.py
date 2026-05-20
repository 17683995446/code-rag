#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.8 - 真实应用场景长时间测试
模拟真实用户：添加知识、建立关联、查询、推理、搜索
运行时间：15分钟
"""
import sys
import os
import random
import time
from typing import List, Dict, Any
from datetime import datetime

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class RealWorldLongRunTest:
    """真实世界场景长时间测试"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.operations_count = 0
        self.error_count = 0
        
        # 真实世界知识
        self.concepts = [
            "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
            "计算机视觉", "强化学习", "监督学习", "无监督学习", "Transformer",
            "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
            "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI",
            "数据库", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "Redis",
            "云计算", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
            "Git", "GitHub", "CI/CD", "DevOps", "敏捷开发", "Scrum",
        ]
        
        self.people = [
            "张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十",
            "Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry",
        ]
        
        self.projects = [
            "电商平台", "社交网络", "在线教育", "医疗系统", "金融科技",
            "游戏开发", "数据分析", "IoT平台", "区块链应用", "AR/VR",
        ]
        
        self.relations = [
            "学习", "使用", "开发", "部署", "优化", "测试", "研究", "合作",
            "包含", "依赖", "关联", "引用", "相似", "相反", "导致", "属于",
        ]
    
    def record_error(self, operation: str, error: Exception, context: str = ""):
        self.error_count += 1
        self.errors.append({
            "operation": operation,
            "error": str(error),
            "type": type(error).__name__,
            "context": context,
            "time": datetime.now().isoformat(),
            "total_ops": self.operations_count
        })
        print(f"\n❌ ERROR [{operation}] #{self.operations_count}: {type(error).__name__}")
        print(f"   {error}")
    
    def random_operation(self):
        """执行随机真实操作"""
        op_type = random.choices(
            ["add", "connect", "query", "semantic_search", "infer", "recommend"],
            weights=[0.3, 0.2, 0.25, 0.15, 0.05, 0.05]
        )[0]
        
        self.operations_count += 1
        
        try:
            if op_type == "add":
                # 混合添加概念、人员、项目
                category = random.choice(["concept", "person", "project"])
                if category == "concept":
                    base = random.choice(self.concepts)
                    label = f"{base} {random.randint(1, 100)}" if random.random() > 0.3 else base
                elif category == "person":
                    base = random.choice(self.people)
                    label = f"{base}"
                else:
                    base = random.choice(self.projects)
                    label = f"{base} V{random.randint(1, 10)}"
                
                self.kg.remember(
                    label,
                    properties={
                        "category": category,
                        "created_at": datetime.now().isoformat(),
                        "importance": random.random()
                    },
                    node_type=random.choice(list(NodeType))
                )
            
            elif op_type == "connect":
                # 获取现有标签
                with self.kg._node_lock:
                    labels = list(self.kg._label_to_node.keys())
                
                if len(labels) >= 2:
                    source = random.choice(labels)
                    target = random.choice(labels)
                    relation = random.choice(self.relations)
                    weight = random.random() * 2
                    
                    self.kg.connect(
                        source, target,
                        relation=relation,
                        weight=weight
                    )
            
            elif op_type == "query":
                search_term = random.choice(self.concepts + self.people + self.projects + [""])
                k = random.randint(1, 20)
                self.kg.recall(search_term, k=k)
            
            elif op_type == "semantic_search":
                search_term = random.choice(self.concepts + self.people + self.projects)
                k = random.randint(1, 10)
                self.kg.semantic_search(search_term, k=k)
            
            elif op_type == "infer":
                with self.kg._node_lock:
                    labels = list(self.kg._label_to_node.keys())
                
                if labels:
                    start_concept = random.choice(labels)
                    max_depth = random.randint(1, 4)
                    self.kg.infer(start_concept, max_depth=max_depth)
            
            elif op_type == "recommend":
                with self.kg._node_lock:
                    labels = list(self.kg._label_to_node.keys())
                
                if labels:
                    node_label = random.choice(labels)
                    self.kg.recommend_connections(node_label, k=random.randint(1, 5))
            
            # 进度输出
            if self.operations_count % 1000 == 0:
                print(f"  📊 已执行 {self.operations_count:,} 次操作 (错误: {self.error_count})")
            
        except Exception as e:
            self.record_error(op_type, e)
    
    def run_long_test(self, duration_minutes: int = 15):
        """运行长时间测试"""
        print("="*90)
        print(f"🚀 v7.8 真实应用场景长时间测试 - {duration_minutes}分钟")
        print("="*90)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        print(f"\n⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 计划结束: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*90)
        
        last_update = time.time()
        update_interval = 30  # 每30秒更新一次
        
        while time.time() < end_time:
            # 执行操作
            for _ in range(100):
                if time.time() >= end_time:
                    break
                self.random_operation()
            
            # 检查是否需要更新输出
            if time.time() - last_update > update_interval:
                elapsed = time.time() - start_time
                remaining = max(0, end_time - time.time())
                with self.kg._node_lock:
                    node_count = len(self.kg._nodes)
                    edge_count = len(self.kg._edges)
                
                print(f"  ⏱️  已运行 {elapsed/60:.1f}分钟 / {duration_minutes}分钟 | "
                      f"剩余 {remaining/60:.1f}分钟")
                print(f"  📊 操作数: {self.operations_count:,} | 节点: {node_count:,} | "
                      f"边: {edge_count:,} | 错误: {self.error_count}")
                
                last_update = time.time()
        
        # 最终总结
        total_elapsed = time.time() - start_time
        print("\n" + "="*90)
        print("📊 真实世界长时间测试最终总结")
        print("="*90)
        print(f"总运行时间: {total_elapsed/60:.2f}分钟")
        print(f"总操作数: {self.operations_count:,}")
        
        with self.kg._node_lock:
            node_count = len(self.kg._nodes)
            edge_count = len(self.kg._edges)
        
        print(f"节点数: {node_count:,}")
        print(f"边数: {edge_count:,}")
        
        ops_per_second = self.operations_count / total_elapsed if total_elapsed > 0 else 0
        print(f"平均操作速度: {ops_per_second:.1f} 操作/秒")
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误")
            print("="*90)
            for i, err in enumerate(self.errors[:10], 1):
                print(f"{i:2d}. [#{err['total_ops']}] {err['operation']}: {err['type']}")
                print(f"    {err['error'][:80]}")
            if len(self.errors) > 10:
                print(f"... 还有 {len(self.errors)-10} 个错误")
        else:
            print("\n✅ 太棒了！长时间测试完美通过！0个错误！")
        
        print("="*90)
        
        return len(self.errors) == 0

if __name__ == "__main__":
    test = RealWorldLongRunTest()
    passed = test.run_long_test(duration_minutes=5)  # 为演示缩短到5分钟
    sys.exit(0 if passed else 1)


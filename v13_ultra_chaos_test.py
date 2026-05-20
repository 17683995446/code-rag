#!/usr/bin/env python3
"""
知识图谱记忆系统 - 终极混乱场景测试（v13.0）

超长运行时间，大规模，非常复杂，极其混乱的真实场景测试
"""
import sys
import os
import random
import time
import gc
from datetime import datetime
import uuid
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class UltraChaosTest:
    """终极混乱测试"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.ops_count = 0
        self.threads_running = True
        
        # 真实场景数据
        self.tech_terms = ['Python', 'JavaScript', 'Go', 'Rust', 'React', 'Vue', 'Angular',
                          'Docker', 'Kubernetes', 'PostgreSQL', 'MongoDB', 'Redis',
                          'AI', 'ML', 'DeepLearning', 'LLM', 'GPT', 'TensorFlow',
                          'Pytorch', 'FastAPI', 'Django', 'Flask', 'Web', 'API']
        
        self.domains = ['Tech', 'Business', 'Health', 'Education', 'Finance', 
                       'Entertainment', 'Sports', 'Politics', 'Science', 'Art']
        
        self.people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 
                     'Grace', 'Henry', 'Ivy', 'Jack', 'Kate', 'Leo']
        
        self.projects = ['ProjectAlpha', 'ProjectBeta', 'ProjectGamma',
                        'ProjectDelta', 'ProjectOmega']
        
        self.relations = list(EdgeType)
        
        print("="*120)
        print("🚀 知识图谱记忆系统 - 终极混乱场景测试（v13.0）")
        print(f"⏰  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*120)
    
    def log_error(self, op_name, err, context=""):
        with threading.Lock():
            err_info = {
                'time': datetime.now().isoformat(),
                'op': op_name,
                'error_type': type(err).__name__,
                'msg': str(err),
                'context': context
            }
            self.errors.append(err_info)
            print(f"\n❌ 错误 [{op_name}]: {type(err).__name__}: {err}")
    
    def generate_random_knowledge(self):
        """生成完全随机混乱的知识"""
        choices = [
            lambda: random.choice(self.tech_terms) + str(random.randint(1, 10000)),
            lambda: random.choice(self.domains) + " - " + random.choice(self.people),
            lambda: random.choice(self.projects) + " / " + random.choice(self.tech_terms),
            lambda: str(random.randint(-999999999, 999999999)),
            lambda: "a" * random.randint(1, 5000),
            lambda: random.choice([None, "", 123, 3.14, True, False, [], {}, ()])
        ]
        return random.choice(choices)()
    
    def chaos_remember(self):
        """混乱的记忆操作"""
        try:
            knowledge = self.generate_random_knowledge()
            node_type = random.choice([None, random.choice(list(NodeType)), 
                                      "invalid_type", "RANDOM", random.randint(1, 100)])
            props = random.choice([
                None, {}, {'a': 1, 'b': "test"}, {'x': None, 'y': [], 'z': {}},
                {f'key{i}': f'value{i}' for i in range(random.randint(1, 100))}
            ])
            compute_embedding = random.choice([True, False])
            result = self.kg.remember(knowledge, properties=props, 
                                      node_type=node_type, 
                                      compute_embedding=compute_embedding)
            self.ops_count += 1
            return True
        except Exception as e:
            self.log_error("remember", e, f"input: {repr(knowledge)}")
            return False
    
    def chaos_connect(self):
        """混乱的连接操作"""
        try:
            with self.kg._node_lock:
                node_labels = list(self.kg._label_to_node.keys())
            
            if len(node_labels) < 2:
                return True
            
            source = random.choice(node_labels) if node_labels else None
            target = random.choice(node_labels) if node_labels else None
            
            if random.random() < 0.2:
                source = self.generate_random_knowledge()
                target = self.generate_random_knowledge()
            
            relation = random.choice([
                None, random.choice(self.relations), "invalid_relation",
                random.choice(list(EdgeType)), 3.14, [], {}
            ])
            weight = random.choice([None, random.uniform(-999, 999), float('inf'), 
                                   float('nan'), random.randint(-1000, 1000)])
            
            result = self.kg.connect(source, target, relation=relation, weight=weight)
            self.ops_count += 1
            return True
        except Exception as e:
            self.log_error("connect", e)
            return False
    
    def chaos_recall(self):
        """混乱的召回操作"""
        try:
            query = self.generate_random_knowledge()
            k = random.choice([None, random.randint(-999, 9999), 3.14, 
                             "invalid", float('inf'), float('nan')])
            result = self.kg.recall(query, k=k)
            self.ops_count += 1
            return True
        except Exception as e:
            self.log_error("recall", e)
            return False
    
    def chaos_search(self):
        """混乱的语义搜索"""
        try:
            query = self.generate_random_knowledge()
            k = random.choice([None, random.randint(-999, 9999), 3.14, 
                             "invalid", float('inf'), float('nan')])
            result = self.kg.semantic_search(query, k=k)
            self.ops_count += 1
            return True
        except Exception as e:
            self.log_error("semantic_search", e)
            return False
    
    def chaos_infer(self):
        """混乱的推理操作"""
        try:
            with self.kg._node_lock:
                labels = list(self.kg._label_to_node.keys())
            
            concept = random.choice(labels) if labels else None
            if random.random() < 0.3:
                concept = self.generate_random_knowledge()
            
            max_depth = random.choice([None, random.randint(-999, 9999), 
                                      3.14, "invalid", float('inf'), float('nan')])
            
            result = self.kg.infer(concept, max_depth=max_depth)
            self.ops_count += 1
            return True
        except Exception as e:
            self.log_error("infer", e)
            return False
    
    def chaos_recommend(self):
        """混乱的推荐操作"""
        try:
            with self.kg._node_lock:
                labels = list(self.kg._label_to_node.keys())
            
            label = random.choice(labels) if labels else None
            if random.random() < 0.3:
                label = self.generate_random_knowledge()
            
            k = random.choice([None, random.randint(-999, 9999), 
                             3.14, "invalid", float('inf'), float('nan')])
            
            result = self.kg.recommend_connections(label, k=k)
            self.ops_count += 1
            return True
        except Exception as e:
            self.log_error("recommend", e)
            return False
    
    def chaos_clear(self):
        """偶尔清空系统"""
        try:
            if random.random() < 0.01:
                self.kg.clear()
                self.ops_count +=1
                return True
            return True
        except Exception as e:
            self.log_error("clear", e)
            return False
    
    def chaos_stats(self):
        """获取统计信息"""
        try:
            stats = self.kg.get_statistics()
            self.ops_count +=1
            return True
        except Exception as e:
            self.log_error("stats", e)
            return False
    
    def chaos_visualize(self):
        """可视化操作"""
        try:
            viz = self.kg.get_graph_for_visualization()
            self.ops_count +=1
            return True
        except Exception as e:
            self.log_error("visualize", e)
            return False
    
    def random_operation(self):
        """随机选择操作"""
        ops = [
            (self.chaos_remember, 0.25),
            (self.chaos_connect, 0.2),
            (self.chaos_recall, 0.2),
            (self.chaos_search, 0.15),
            (self.chaos_infer, 0.1),
            (self.chaos_recommend, 0.05),
            (self.chaos_clear, 0.01),
            (self.chaos_stats, 0.02),
            (self.chaos_visualize, 0.02),
        ]
        chosen_op = random.choices([op for op, prob in ops], 
                                 weights=[prob for op, prob in ops])[0]
        return chosen_op()
    
    def run_chaos_test(self, duration_sec=600):
        """运行混乱测试"""
        print(f"\n{'='*120}")
        print("🧪 开始终极混乱测试！")
        print(f"⏰  将运行: {duration_sec} 秒")
        print(f"📊  每30秒将输出进度")
        print(f"{'='*120}")
        
        start_time = time.time()
        last_report = start_time
        
        while (time.time() - start_time) < duration_sec:
            try:
                self.random_operation()
                
                if time.time() - last_report >= 30:
                    elapsed = int(time.time() - start_time)
                    stats = self.kg.get_statistics()
                    print(f"\n⏱️  [{datetime.now().strftime('%H:%M:%S')}] "
                          f"已运行 {elapsed} 秒 | 操作数: {self.ops_count:,} "
                          f"| 节点: {stats['nodes']:,} | 边: {stats['edges']:,} "
                          f"| 错误: {len(self.errors)}")
                    last_report = time.time()
                    gc.collect()
                
                if len(self.errors) > 50:
                    print("\n❌  错误超过50个！停止测试！")
                    break
            except Exception as e:
                print(f"\n❌  测试流程崩溃！: {e}")
                import traceback
                traceback.print_exc()
                break
        
        self.print_final_report(start_time)
    
    def print_final_report(self, start_time):
        total_time = time.time() - start_time
        stats = self.kg.get_statistics()
        
        print(f"\n{'='*120}")
        print("🎊 终极混乱场景测试 - 最终报告")
        print(f"{'='*120}")
        print(f"⏰  总运行时间: {total_time:.2f} 秒")
        print(f"📊  总操作数: {self.ops_count:,}")
        print(f"⚡  平均速度: {self.ops_count / total_time:.1f} ops/秒")
        print(f"🗂️  最终节点数: {stats['nodes']:,}")
        print(f"🔗  最终边数: {stats['edges']:,}")
        print(f"❌  发现错误数: {len(self.errors)}")
        
        if self.errors:
            print(f"\n❌  发现的问题:")
            error_types = {}
            for err in self.errors:
                etype = err['error_type']
                error_types[etype] = error_types.get(etype, 0) + 1
            
            for etype, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {etype}: {count}次")
            
            print(f"\n📝  详细错误（前10个）:")
            for i, err in enumerate(self.errors[:10]):
                print(f"   {i+1:2d}. [{err['op']}] {err['error_type']}: {err['msg']}")
        
        print(f"\n{'='*120}")
        if len(self.errors) == 0:
            print("🎉 恭喜！系统完美通过！0个错误！")
        else:
            print("⚠️  系统存在问题，需要修复！")
        print(f"{'='*120}")
        
        return len(self.errors) == 0

if __name__ == "__main__":
    test = UltraChaosTest()
    success = test.run_chaos_test(duration_sec=300)  # 5分钟快速测试
    sys.exit(0 if success else 1)

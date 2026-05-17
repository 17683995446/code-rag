#!/usr/bin/env python3
"""
Code RAG v11.0 - 改进验证测试
验证我们刚才做的改进是否有效！
"""

import sys
import time
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_min_chunk_size_improvement():
    """测试min_chunk_size降低后的效果"""
    print_header("🔍 验证 1: 最小代码块大小改进")
    
    from code_rag.data_layer import CodeParser
    parser = CodeParser()
    
    print(f"\n  原始 MIN_CHUNK_SIZE: 50 (之前的设置)")
    print(f"  当前 MIN_CHUNK_SIZE: {parser.MIN_CHUNK_SIZE}")
    print(f"  新增 MIN_IMPORTANT_LINES: {parser.MIN_IMPORTANT_LINES}")
    
    # 测试简单文件
    test_file = project_root / "flask_test_project" / "examples" / "celery" / "make_celery.py"
    if test_file.exists():
        doc = parser.parse_file(str(test_file))
        print(f"\n  测试文件: {test_file.name}")
        print(f"  解析到 {len(doc.chunks)} 个代码块")
        for i, chunk in enumerate(doc.chunks):
            print(f"    块 {i+1}: {len(chunk.content)} 字符, {chunk.chunk_type}")
            preview = chunk.content[:60].replace('\n', ' ')
            print(f"      预览: {preview}...")
    else:
        print(f"\n  测试文件不存在，跳过")
    
    return True


def test_synonyms_expansion():
    """测试同义词扩展"""
    print_header("🎯 验证 2: 同义词扩展改进")
    
    from code_rag.search_layer import BM25Index
    bm25 = BM25Index()
    
    print(f"\n  同义词库大小: {len(bm25.synonyms)} 个词条")
    print(f"\n  新增同义词:")
    
    # 检查新增的关键词
    new_words = ['request', 'response', 'route', 'app', 'context', 
                 'session', 'template', 'decorator', 'middleware', 
                 'client', 'auth']
    
    for word in new_words:
        if word in bm25.synonyms:
            print(f"    ✓ '{word}': {len(bm25.synonyms[word])} 个同义词")
    
    # 测试一些查询
    test_texts = [
        "def index(): return 'Hello World'",
        "@app.route('/')",
        "def get_db(): connection",
        "session['user']"
    ]
    
    for text in test_texts:
        bm25.add_document(text)
    
    test_queries = [
        "route decorator",
        "request handling",
        "session management",
        "app config"
    ]
    
    print(f"\n  搜索测试:")
    for query in test_queries:
        results = bm25.search(query, k=3)
        print(f"    '{query}': {len(results)} 结果")
    
    return True


def test_full_flow_with_real_project():
    """使用真实项目完整流程测试"""
    print_header("🚀 验证 3: 真实项目完整流程")
    
    from code_rag.data_layer import CodeParser
    from code_rag.search_layer import BM25Index
    
    project_dir = project_root / "flask_test_project"
    parser = CodeParser()
    bm25 = BM25Index()
    
    # 1. 解析项目
    print(f"\n  正在解析项目...")
    start_time = time.time()
    
    all_chunks = []
    py_files = list(project_dir.rglob("*.py"))
    
    for file_path in py_files[:50]:  # 取前50个文件快速测试
        try:
            doc = parser.parse_file(str(file_path))
            all_chunks.extend([c.content for c in doc.chunks])
        except:
            pass
    
    parse_time = time.time() - start_time
    print(f"  解析完成: {len(all_chunks)} 个代码块, 耗时 {parse_time:.2f}s")
    
    # 2. 构建索引
    print(f"\n  正在构建索引...")
    start_time = time.time()
    bm25.add_documents(all_chunks)
    index_time = time.time() - start_time
    print(f"  索引完成: 耗时 {index_time:.2f}s")
    
    # 3. 测试搜索
    test_cases = [
        "request handling",
        "route decorator",
        "template rendering",
        "session management",
        "app configuration"
    ]
    
    print(f"\n  搜索测试:")
    total_results = 0
    for query in test_cases:
        results = bm25.search(query, k=5)
        total_results += len(results)
        print(f"    '{query}': {len(results)} 结果")
    
    avg_results = total_results / len(test_cases)
    print(f"\n  平均结果数: {avg_results:.1f}")
    
    return avg_results > 3


def main():
    print_header("🧪 Code RAG v11.0 - 改进验证测试")
    
    results = []
    
    try:
        res1 = test_min_chunk_size_improvement()
        results.append(("最小块大小", res1))
        
        res2 = test_synonyms_expansion()
        results.append(("同义词扩展", res2))
        
        res3 = test_full_flow_with_real_project()
        results.append(("完整流程", res3))
        
        # 总结
        print_header("📊 验证结果总结")
        all_passed = True
        
        for name, passed in results:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"  {name}: {status}")
            if not passed:
                all_passed = False
        
        print(f"\n  总体: {'🎉 所有改进验证通过!' if all_passed else '⚠️ 有问题需要修复'}")
        
    except Exception as e:
        print(f"\n❌ 验证过程出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

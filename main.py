"""
产品级Code RAG - 主入口
"""

import sys
from pathlib import Path


def print_help():
    """打印帮助"""
    print("="*60)
    print("  🚀 Code RAG - 产品级RAG系统")
    print("="*60)
    print("\n使用方式:")
    print("  python main.py demo               - 运行快速演示")
    print("  python main.py index <目录>        - 索引目录")
    print("  python main.py search <查询>       - 搜索")
    print("  python main.py ask <问题>          - 问答")
    print("  python main.py api                 - 启动API服务（需要fastapi）")
    print("  python main.py test                - 运行测试")
    print("  python main.py help                - 显示此帮助")


def run_demo():
    """运行演示"""
    from src.core import CodeRAG
    from src.core.rag import demo as run_rag_demo
    run_rag_demo()


def run_index(directory: str):
    """索引"""
    from src.core import CodeRAG
    rag = CodeRAG()
    rag.index(directory)
    print(f"\n✅ 索引完成: {directory}")


def run_search(query: str):
    """搜索"""
    from src.core import CodeRAG
    rag = CodeRAG()
    rag.index("/tmp")  # 使用演示数据
    results = rag.search(query)
    
    print(f"\n搜索: {query}")
    print(f"找到 {len(results)} 个结果:\n")
    
    for i, r in enumerate(results):
        print(f"{i+1}. [{r.score:.3f}] {r.text[:80]}...")
        print(f"   元数据: {r.metadata}\n")


def run_ask(question: str):
    """问答"""
    from src.core import CodeRAG
    rag = CodeRAG()
    rag.index("/tmp")
    answer = rag.ask(question)
    
    print(f"\n问题: {answer.question}")
    print(f"\n回答: {answer.answer}")
    print(f"\n来源: {len(answer.sources)} 个文档")


def run_api():
    """启动API"""
    try:
        from src.api import start_api
        start_api()
    except ImportError:
        print("\n⚠️  需要安装 fastapi 和 uvicorn 才能启动API服务")
        print("请运行: pip install fastapi uvicorn")


def run_tests():
    """运行测试"""
    import subprocess
    result = subprocess.run([sys.executable, "tests/test_core.py"])
    return result.returncode


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    if command == "demo":
        run_demo()
    elif command == "index":
        if len(sys.argv) < 3:
            print("请指定要索引的目录")
            return
        run_index(sys.argv[2])
    elif command == "search":
        if len(sys.argv) < 3:
            print("请指定搜索查询")
            return
        run_search(" ".join(sys.argv[2:]))
    elif command == "ask":
        if len(sys.argv) < 3:
            print("请指定问题")
            return
        run_ask(" ".join(sys.argv[2:]))
    elif command == "api":
        run_api()
    elif command == "test":
        sys.exit(run_tests())
    elif command == "help":
        print_help()
    else:
        print(f"未知命令: {command}")
        print_help()


if __name__ == "__main__":
    main()

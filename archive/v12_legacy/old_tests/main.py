"""
产品级Code RAG - 主入口 (增强版)
支持监控、配置管理、性能分析
"""

import sys
import json
import time
from pathlib import Path


def print_help():
    """打印帮助"""
    print("="*60)
    print("  🚀 Code RAG - 产品级RAG系统 v3.0.0")
    print("="*60)
    print("\n使用方式:")
    print("  python main.py demo               - 运行快速演示")
    print("  python main.py index <目录>        - 索引目录")
    print("  python main.py search <查询>       - 搜索")
    print("  python main.py ask <问题>          - 问答")
    print("  python main.py api                 - 启动API服务")
    print("  python main.py monitor             - 显示系统监控")
    print("  python main.py config [key] [val]  - 查看/设置配置")
    print("  python main.py perf               - 性能分析")
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
    rag.index("/tmp")

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
    except ImportError as e:
        print("\n⚠️  需要安装 fastapi 和 uvicorn 才能启动API服务")
        print("请运行: pip install fastapi uvicorn")


def run_monitor():
    """显示系统监控"""
    from src.core import get_monitor

    monitor = get_monitor()

    print("\n" + "="*60)
    print("  📊 系统监控")
    print("="*60)

    monitor.record_system_metrics()

    info = monitor.get_system_info()

    print("\nCPU:")
    print(f"  核心数: {info['cpu']['count']}")
    print(f"  使用率: {info['cpu']['percent']:.1f}%")

    print("\n内存:")
    mem = info['memory']
    print(f"  总计: {mem['total'] / 1024**3:.2f} GB")
    print(f"  已用: {mem['used'] / 1024**3:.2f} GB ({mem['percent']:.1f}%)")
    print(f"  可用: {mem['available'] / 1024**3:.2f} GB")

    print("\n进程:")
    proc = info['process']
    print(f"  PID: {proc['pid']}")
    print(f"  线程: {proc['threads']}")
    print(f"  内存: {proc['memory_info'].rss / 1024**2:.2f} MB")

    report = monitor.get_performance_report()

    print("\n操作统计:")
    for op_name, stats in report['operations'].items():
        if stats['count'] > 0:
            print(f"  {op_name}:")
            print(f"    调用次数: {stats['count']}")
            print(f"    平均耗时: {stats['avg_time']*1000:.2f}ms")
            print(f"    错误率: {stats['error_rate']:.1%}")


def run_config(key: str = None, value: str = None):
    """查看/设置配置"""
    from src.core import get_config_manager

    manager = get_config_manager()
    manager.initialize()

    if key is None:
        config = manager.get_all()
        print("\n" + "="*60)
        print("  ⚙️  配置信息")
        print("="*60)
        print(json.dumps(config, indent=2, ensure_ascii=False))
    elif value is None:
        val = manager.get(key)
        print(f"\n{key} = {val}")
    else:
        manager.set(key, value)
        print(f"\n✅ 已设置 {key} = {value}")


def run_perf():
    """性能分析"""
    from src.core import CodeRAG, get_monitor

    print("\n" + "="*60)
    print("  ⚡ 性能分析")
    print("="*60)

    monitor = get_monitor()

    rag = CodeRAG()

    operations = [
        ("索引操作", lambda: rag.index("/tmp")),
        ("搜索操作", lambda: rag.search("FAISS", k=3)),
        ("问答操作", lambda: rag.ask("什么是FAISS?")),
    ]

    print("\n执行性能测试...\n")

    for name, op in operations:
        start = time.time()
        try:
            op()
            elapsed = time.time() - start
            print(f"  ✅ {name}: {elapsed*1000:.2f}ms")
        except Exception as e:
            elapsed = time.time() - start
            print(f"  ❌ {name}: 失败 ({elapsed*1000:.2f}ms) - {e}")

    report = monitor.get_performance_report()

    print("\n系统资源:")
    print(f"  CPU: {report['system']['cpu_percent']:.1f}%")
    print(f"  内存: {report['system']['memory_percent']:.1f}%")

    print("\n进程资源:")
    print(f"  内存: {report['process']['memory_rss_mb']:.2f} MB")
    print(f"  线程: {report['process']['threads']}")


def run_tests():
    """运行测试"""
    import subprocess

    print("\n" + "="*60)
    print("  🧪 运行测试套件")
    print("="*60)

    test_files = [
        ("tests/test_core.py", "核心模块测试"),
        ("tests/test_monitor.py", "监控模块测试"),
        ("tests/test_integration.py", "集成测试"),
        ("tests/test_system.py", "系统测试"),
    ]

    all_passed = True

    for test_file, description in test_files:
        print(f"\n运行: {description}")
        print("-" * 60)
        result = subprocess.run([sys.executable, test_file])
        if result.returncode != 0:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("="*60)

    return 0 if all_passed else 1


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
    elif command == "monitor":
        run_monitor()
    elif command == "config":
        key = sys.argv[2] if len(sys.argv) > 2 else None
        value = sys.argv[3] if len(sys.argv) > 3 else None
        run_config(key, value)
    elif command == "perf":
        run_perf()
    elif command == "test":
        sys.exit(run_tests())
    elif command == "help":
        print_help()
    else:
        print(f"未知命令: {command}")
        print_help()


if __name__ == "__main__":
    main()

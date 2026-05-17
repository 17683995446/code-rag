#!/usr/bin/env python3
"""
Code RAG v16.0 - Web应用启动器
启动Web界面服务
"""

import sys
import os
from pathlib import Path


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠  Code RAG v16.0 - Web界面启动器                     ║
║                                                           ║
║   现代化Web界面 · 智能代码检索 · 可视化分析               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """检查依赖"""
    required_packages = ['fastapi', 'uvicorn', 'pydantic']
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️ 缺少依赖: {missing}")
        print(f"正在安装依赖...")
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *missing
        ])
        print(f"✅ 依赖安装完成!")


def start_web_server(host: str = "0.0.0.0", port: int = 8000):
    """启动Web服务器"""
    import uvicorn
    
    # 动态导入
    PROJECT_ROOT = Path(__file__).parent
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    
    print(f"""
🚀 正在启动服务器...

📡 Web界面: http://{host}:{port}
📖 API文档: http://{host}:{port}/docs
📊 交互式文档: http://{host}:{port}/redoc

按 Ctrl+C 停止服务器
    """)
    
    from code_rag.web_app import app
    uvicorn.run(app, host=host, port=port)


def show_help():
    """显示帮助"""
    help_text = """
Code RAG v16.0 - 命令行界面

用法:
    python start_web.py [选项]

选项:
    --host <host>    服务器地址 (默认: 0.0.0.0)
    --port <port>    服务器端口 (默认: 8000)
    --help           显示帮助信息

示例:
    python start_web.py
    python start_web.py --port 3000
    python start_web.py --host 127.0.0.1 --port 8080
    """
    print(help_text)


def main():
    """主函数"""
    print_banner()
    
    # 解析参数
    host = "0.0.0.0"
    port = 8000
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg in ['-h', '--help', 'help']:
            show_help()
            return
        elif arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 1
        elif arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 1
        else:
            print(f"⚠️ 未知选项: {arg}")
        
        i += 1
    
    # 检查依赖
    check_dependencies()
    
    # 启动服务器
    try:
        start_web_server(host, port)
    except KeyboardInterrupt:
        print(f"\n\n👋 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

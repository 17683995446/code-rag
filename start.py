#!/usr/bin/env python3
"""
知识图谱记忆系统 v4.0 - 主启动脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import click
import subprocess


@click.group()
@click.version_option(version="4.0.0")
def main():
    """
    🧠 知识图谱记忆系统 v4.0
    工业化知识图谱记忆系统，基于NetworkX
    """
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8000, type=int, help="监听端口")
def web(host: str, port: int):
    """启动Web服务器"""
    click.secho("\n🧠 启动知识图谱记忆系统 Web服务\n", fg="magenta", bold=True)
    click.secho(f"   主页: http://{host}:{port}/final.html", fg="cyan")
    click.secho(f"   API文档: http://{host}:{port}/docs\n", fg="blue")
    
    try:
        from kg_memory.web import app
        import uvicorn
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        click.secho("⚠️ 缺少依赖，请运行: pip install fastapi uvicorn networkx pydantic rich click", fg="yellow")
        sys.exit(1)


@main.command()
def cli():
    """运行命令行界面"""
    from kg_memory.cli import cli as kg_cli
    sys.argv[0] = "kg-memory"
    kg_cli()


@main.command()
def test():
    """运行完整测试套件"""
    click.secho("\n🧪 运行完整测试套件\n", fg="blue")
    
    test_script = os.path.join(os.path.dirname(__file__), "tests/test_all.py")
    if os.path.exists(test_script):
        subprocess.run([sys.executable, test_script])
    else:
        click.secho("⚠️ 测试文件不存在", fg="yellow")


@main.command()
def score():
    """运行多维度综合评分"""
    click.secho("\n📊 运行多维度综合评分\n", fg="blue")
    
    try:
        from kg_memory.scoring import print_evaluation_report
        print_evaluation_report()
    except Exception as e:
        click.secho(f"❌ 评分失败: {e}", fg="red")


@main.command()
def demo():
    """运行演示"""
    click.secho("\n🎬 运行演示\n", fg="green")
    
    from kg_memory.core import MemorySystem
    ms = MemorySystem("./data_demo")
    ms.clear()
    
    click.echo("添加数据...")
    data = ["Python", "Django", "Flask", "JavaScript", "React", "Vue", "Programming", "Web Development"]
    for item in data:
        ms.remember(item)
    
    click.echo("建立连接...")
    connections = [
        ("Django", "Python", "uses"),
        ("Flask", "Python", "uses"),
        ("React", "JavaScript", "uses"),
        ("Vue", "JavaScript", "uses"),
        ("Python", "Programming", "related_to"),
        ("Web Development", "Django", "related_to"),
    ]
    for s, t, r in connections:
        ms.connect(s, t, r)
    
    ms.save()
    
    click.echo("\n✅ 演示数据已创建！")
    click.echo("💡 尝试:")
    click.echo("   ./start.py web - 启动Web界面")
    click.echo("   ./start.py score - 查看评分")


@main.command()
def init():
    """初始化系统"""
    click.secho("\n🚀 初始化知识图谱记忆系统 v4.0\n", fg="magenta", bold=True)
    
    click.echo("检查依赖...")
    try:
        import networkx
        import pydantic
        import fastapi
        import rich
        click.secho("✅ 依赖检查通过\n", fg="green")
    except ImportError:
        click.secho("⚠️ 部分依赖缺失", fg="yellow")
        click.secho("建议安装: pip install networkx fastapi uvicorn pydantic rich click\n", fg="blue")
    
    click.secho("🎉 初始化完成！", fg="green", bold=True)
    click.echo("\n使用:")
    click.echo("  ./start.py init   - 初始化")
    click.echo("  ./start.py demo   - 演示")
    click.echo("  ./start.py web    - 启动Web")
    click.echo("  ./start.py visualize - 启动架构可视化")
    click.echo("  ./start.py test   - 测试")
    click.echo("  ./start.py score  - 评分\n")


@main.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8080, type=int, help="监听端口")
def visualize(host: str, port: int):
    """启动架构可视化服务"""
    click.secho("\n🎨 启动架构可视化服务\n", fg="cyan", bold=True)
    click.secho(f"   主页: http://{host}:{port}/", fg="cyan")
    click.secho(f"   API文档: http://{host}:{port}/docs", fg="blue")
    click.secho("   📡 文件变化自动监听中...\n", fg="green")
    
    try:
        from visualization_server import start_server
        start_server()
    except ImportError:
        click.secho("⚠️ 缺少依赖，请安装: pip install watchdog", fg="yellow")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 无参数，显示帮助
        main(["--help"])
    else:
        main()

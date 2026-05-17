"""
知识图谱记忆系统 - 命令行界面
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

from kg_memory.core import MemorySystem, Node, Edge, EdgeType


console = Console()


def _get_system(data_dir: str) -> MemorySystem:
    try:
        return MemorySystem(data_dir=data_dir)
    except Exception as e:
        console.print(f"[red]Error initializing system: {e}[/red]")
        sys.exit(1)


@click.group()
@click.version_option(version="4.0.0", prog_name="kg-memory")
def cli() -> None:
    """
    🧠 知识图谱记忆系统 v4.0
    
    基于NetworkX的工业化知识图谱记忆系统
    """
    pass


@cli.command()
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
def info(data_dir: str) -> None:
    """显示系统信息和统计"""
    ms = _get_system(data_dir)
    stats = ms.stats()
    
    table = Table(title="📊 系统统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")
    
    for k, v in stats.items():
        if isinstance(v, float):
            v = f"{v:.4f}"
        table.add_row(str(k), str(v))
    
    console.print(table)


@cli.command()
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
@click.option("--clear", is_flag=True, help="清空现有数据")
def init(data_dir: str, clear: bool) -> None:
    """初始化知识图谱系统"""
    ms = _get_system(data_dir)
    
    if clear:
        ms.clear()
        ms.save()
        console.print("[green]✅ 已清空并初始化数据[/green]")
    else:
        console.print("[blue]ℹ️ 系统已就绪[/blue]")
    
    info.callback(data_dir=data_dir)


@cli.command()
@click.argument("knowledge")
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
@click.option("--property", "-p", multiple=True, help="属性 (key=value)")
def remember(knowledge: str, data_dir: str, property: list[str]) -> None:
    """记住新知识"""
    ms = _get_system(data_dir)
    props = {}
    for p in property:
        if "=" in p:
            k, v = p.split("=", 1)
            props[k.strip()] = v.strip()
    
    node_id = ms.remember(knowledge, properties=props)
    ms.save()
    
    console.print(f"[green]✅ 记住新知识 (ID: {node_id})[/green]")
    console.print(f"   [dim]{knowledge}[/dim]")


@cli.command()
@click.argument("source")
@click.argument("target")
@click.option("--relation", "-r", default="related_to", help="关系类型")
@click.option("--weight", "-w", type=float, default=1.0, help="权重 (0-10)")
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
def connect(source: str, target: str, relation: str, weight: float, data_dir: str) -> None:
    """连接两个知识"""
    ms = _get_system(data_dir)
    edge_id = ms.connect(source, target, relation=relation, weight=weight)
    ms.save()
    
    console.print(f"[green]✅ 连接成功 (ID: {edge_id})[/green]")
    console.print(f"   [blue]{source}[/blue] [yellow]{relation}[/yellow] [blue]{target}[/blue]")


@cli.command()
@click.argument("query")
@click.option("--top", "-k", type=int, default=10, help="返回结果数量")
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
@click.option("--json", is_flag=True, help="以JSON格式输出")
def recall(query: str, top: int, data_dir: str, json: bool) -> None:
    """回忆相关知识"""
    ms = _get_system(data_dir)
    results = ms.recall(query, k=top)
    
    if json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        if not results:
            console.print("[yellow]⚠️ 未找到相关知识[/yellow]")
            return
        
        table = Table(title=f"🔍 搜索: {query}")
        table.add_column("#", style="dim")
        table.add_column("ID", style="cyan")
        table.add_column("标签", style="green")
        table.add_column("类型", style="yellow")
        
        for i, r in enumerate(results, 1):
            table.add_row(str(i), r["id"][:8] + "...", r["label"], r["type"])
        
        console.print(table)


@cli.command()
@click.argument("concept")
@click.option("--depth", "-d", type=int, default=3, help="推理深度")
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
@click.option("--json", is_flag=True, help="以JSON格式输出")
def infer(concept: str, depth: int, data_dir: str, json: bool) -> None:
    """知识推理"""
    ms = _get_system(data_dir)
    results = ms.infer(concept, max_depth=depth)
    
    if json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    else:
        if not results:
            console.print("[yellow]⚠️ 未找到推理结果[/yellow]")
            return
        
        table = Table(title=f"💡 推理: {concept} (深度 {depth})")
        table.add_column("#", style="dim")
        table.add_column("源", style="cyan")
        table.add_column("关系", style="yellow")
        table.add_column("目标", style="green")
        table.add_column("深度", style="blue")
        
        for i, r in enumerate(results, 1):
            table.add_row(str(i), r["source"], str(r["relation"]), r["target"], str(r["depth"]))
        
        console.print(table)


@cli.command()
@click.argument("source")
@click.argument("target")
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
def path(source: str, target: str, data_dir: str) -> None:
    """查找最短路径"""
    ms = _get_system(data_dir)
    path_result = ms.shortest_path(source, target)
    
    if not path_result:
        console.print("[yellow]⚠️ 未找到路径[/yellow]")
        return
    
    console.print(f"[green]🔗 最短路径 (长度: {len(path_result)-1})[/green]")
    tree = Tree(path_result[0])
    current = tree
    for node in path_result[1:]:
        current = current.add(node)
    console.print(tree)


@cli.command()
@click.argument("node-id")
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
def forget(node_id: str, data_dir: str) -> None:
    """遗忘知识"""
    ms = _get_system(data_dir)
    
    if ms.forget(node_id):
        ms.save()
        console.print(f"[green]✅ 已遗忘 (ID: {node_id})[/green]")
    else:
        console.print(f"[red]❌ 未找到该知识 (ID: {node_id})[/red]")


@cli.command()
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
@click.option("--export-path", "-o", default="graph.graphml", help="导出路径")
def export(data_dir: str, export_path: str) -> None:
    """导出为GraphML格式"""
    ms = _get_system(data_dir)
    ms.export_graphml(export_path)
    console.print(f"[green]✅ 已导出到 {export_path}[/green]")


@cli.command()
@click.option("--data-dir", default="./data_v4", help="数据存储目录")
def demo(data_dir: str) -> None:
    """运行演示"""
    ms = _get_system(data_dir)
    ms.clear()
    
    console.print("\n[blue]🧪 开始演示...[/blue]\n")
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        t1 = progress.add_task("添加编程语言...", total=5)
        for lang in ["Python", "JavaScript", "Java", "Go", "Rust"]:
            ms.remember(lang, properties={"category": "programming_language"})
            progress.advance(t1)
        
        t2 = progress.add_task("添加框架...", total=5)
        for framework in ["Django", "Flask", "React", "Vue", "Spring"]:
            ms.remember(framework, properties={"category": "framework"})
            progress.advance(t2)
        
        t3 = progress.add_task("建立连接...", total=10)
        ms.connect("Django", "Python", "uses", weight=2.0)
        ms.connect("Flask", "Python", "uses", weight=1.8)
        ms.connect("React", "JavaScript", "uses", weight=2.0)
        ms.connect("Vue", "JavaScript", "uses", weight=1.8)
        ms.connect("Spring", "Java", "uses", weight=2.0)
        ms.connect("Python", "Django", "used_by", weight=1.0)
        ms.connect("JavaScript", "React", "used_by", weight=1.0)
        ms.connect("Programming", "Python", "related_to", weight=0.5)
        ms.connect("Programming", "Java", "related_to", weight=0.5)
        ms.connect("Web Development", "Django", "related_to", weight=1.0)
        progress.advance(t3, 10)
        
        ms.save()
    
    console.print(f"\n[green]✅ 演示数据已创建[/green]\n")
    
    info.callback(data_dir=data_dir)
    
    console.print("\n[blue]💡 尝试这些命令:[/blue]")
    console.print("  kg-memory recall Python")
    console.print("  kg-memory infer Django")
    console.print("  kg-memory path Django Java")


if __name__ == "__main__":
    cli()

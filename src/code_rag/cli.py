"""Code RAG CLI

命令行接口
"""

import click
import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from code_rag.middleware_layer.unified import UnifiedConfigGenerator
from code_rag.middleware_layer.validators import ValidationError

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("code_rag")


@click.group()
@click.version_option(version="24.0.0")
def main():
    """Code RAG - 云原生配置生成器
    
    一站式生成 Kubernetes、Docker、云服务、CI/CD 配置文件
    """
    pass


@main.command()
@click.option('--app-name', '-n', default='my-app', help='应用名称')
@click.option('--image', '-i', default='my-app:latest', help='容器镜像')
@click.option('--port', '-p', default=8080, type=int, help='应用端口')
@click.option('--replicas', '-r', default=3, type=int, help='副本数')
@click.option('--namespace', '-ns', default='default', help='命名空间')
@click.option('--output', '-o', default='./output', help='输出目录')
@click.option('--format', '-f', type=click.Choice(['yaml', 'dict']), default='yaml', help='输出格式')
def kubernetes(app_name, image, port, replicas, namespace, output, format):
    """生成 Kubernetes 配置文件"""
    console.print(f"\n[bold blue]🚀 生成 Kubernetes 配置[/bold blue]")
    
    try:
        gen = UnifiedConfigGenerator()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("生成配置...", total=None)
            
            result = gen.generate_kubernetes(
                app_name=app_name,
                image=image,
                port=port,
                replicas=replicas,
                namespace=namespace,
                output_format=format
            )
            
            progress.update(task, completed=True)
        
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == 'yaml':
            for filename, content in result.items():
                filepath = output_path / filename
                filepath.write_text(content)
                console.print(f"  ✅ [green]{filename}[/green]")
        else:
            import json
            filepath = output_path / 'kubernetes.json'
            filepath.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            console.print(f"  ✅ [green]kubernetes.json[/green]")
        
        console.print(f"\n[bold green]✨ 配置已保存到 {output}[/bold green]")
        
    except ValidationError as e:
        console.print(f"[bold red]❌ 验证错误: {e}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {e}[/bold red]")
        logger.exception("Kubernetes 配置生成失败")
        sys.exit(1)


@main.command()
@click.option('--app-name', '-n', default='my-app', help='应用名称')
@click.option('--language', '-l', default='python', type=click.Choice(['python', 'node', 'go', 'java']), help='编程语言')
@click.option('--base-image', '-b', default='alpine', type=click.Choice(['alpine', 'debian', 'ubuntu']), help='基础镜像')
@click.option('--output', '-o', default='./output', help='输出目录')
def docker(app_name, language, base_image, output):
    """生成 Docker 配置文件"""
    console.print(f"\n[bold blue]🐳 生成 Docker 配置[/bold blue]")
    
    try:
        gen = UnifiedConfigGenerator()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("生成配置...", total=None)
            result = gen.generate_docker(app_name, language, base_image)
            progress.update(task, completed=True)
        
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for filename in list(result.keys())[:5]:
            console.print(f"  ✅ [green]{filename}[/green]")
        
        console.print(f"\n[bold green]✨ 生成了 {len(result)} 个配置文件[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option('--provider', '-p', required=True, type=click.Choice(['aws', 'gcp', 'azure']), help='云提供商')
@click.option('--app-name', '-n', default='my-app', help='应用名称')
@click.option('--image', '-i', default='my-app:latest', help='容器镜像')
@click.option('--region', '-r', help='区域 (可选)')
@click.option('--output', '-o', default='./output', help='输出目录')
def cloud(provider, app_name, image, region, output):
    """生成云服务配置文件"""
    console.print(f"\n[bold blue]☁️ 生成 {provider.upper()} 配置[/bold blue]")
    
    try:
        gen = UnifiedConfigGenerator()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("生成配置...", total=None)
            result = gen.generate_cloud(provider, app_name, image, region=region)
            progress.update(task, completed=True)
        
        output_path = Path(output) / provider
        output_path.mkdir(parents=True, exist_ok=True)
        
        for filename in result.keys():
            console.print(f"  ✅ [green]{filename}[/green]")
        
        console.print(f"\n[bold green]✨ 生成了 {len(result)} 个配置文件[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option('--platform', '-p', default='github_actions', type=click.Choice(['github_actions', 'gitlab_ci', 'jenkins']), help='CI/CD 平台')
@click.option('--app-name', '-n', default='my-app', help='应用名称')
@click.option('--language', '-l', default='python', help='编程语言')
@click.option('--output', '-o', default='./output', help='输出目录')
def cicd(platform, app_name, language, output):
    """生成 CI/CD 配置文件"""
    console.print(f"\n[bold blue]🔄 生成 CI/CD 配置 ({platform})[/bold blue]")
    
    try:
        gen = UnifiedConfigGenerator()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("生成配置...", total=None)
            result = gen.generate_cicd(app_name, language, platform)
            progress.update(task, completed=True)
        
        console.print(f"\n[bold green]✨ 生成了 {len(result)} 个配置模块[/bold green]")
        
        table = Table(title="配置模块")
        table.add_column("模块", style="cyan")
        table.add_column("描述", style="green")
        
        descriptions = {
            'github-actions': 'GitHub Actions 工作流',
            'gitlab-ci': 'GitLab CI 配置',
            'jenkins': 'Jenkins Pipeline',
            'testing': '自动化测试',
            'security': '安全扫描',
            'deployment-strategy': '部署策略'
        }
        
        for name in result.keys():
            table.add_row(name, descriptions.get(name, ''))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option('--app-name', '-n', default='my-app', help='应用名称')
@click.option('--image', '-i', default='my-app:latest', help='容器镜像')
@click.option('--language', '-l', default='python', help='编程语言')
@click.option('--cloud', '-c', help='云提供商 (可选: aws, gcp, azure)')
@click.option('--cicd', '-p', default='github_actions', help='CI/CD 平台')
@click.option('--output', '-o', default='./output', help='输出目录')
@click.option('--format', '-f', type=click.Choice(['yaml', 'dict']), default='dict', help='输出格式')
def all(app_name, image, language, cloud, cicd, output, format):
    """生成完整云原生配置栈"""
    console.print(f"\n[bold magenta]🚀🚀🚀 生成完整云原生配置栈[/bold magenta]")
    
    try:
        gen = UnifiedConfigGenerator()
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("生成所有配置...", total=None)
            result = gen.generate_all(
                app_name=app_name,
                image=image,
                language=language,
                cloud_provider=cloud,
                cicd_platform=cicd,
                output_format=format
            )
            progress.update(task, completed=True)
        
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        table = Table(title="生成配置概览")
        table.add_column("类别", style="cyan")
        table.add_column("配置文件数", style="green")
        
        total = 0
        for category, configs in result.items():
            count = len(configs) if isinstance(configs, dict) else 1
            table.add_row(category, str(count))
            total += count
        
        table.add_row("[bold]总计[/bold]", f"[bold]{total}[/bold]")
        
        console.print(table)
        
        import json
        filepath = output_path / 'all-configs.json'
        filepath.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        
        console.print(f"\n[bold green]✨✨✨ 配置已保存到 {output}[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ 错误: {e}[/bold red]")
        logger.exception("完整配置生成失败")
        sys.exit(1)


@main.command()
def info():
    """显示系统信息"""
    console.print("\n[bold blue]Code RAG v24.0.0[/bold blue]")
    console.print("云原生配置生成器\n")
    
    table = Table(show_header=False)
    table.add_column("属性", style="cyan")
    table.add_column("值", style="green")
    
    table.add_row("版本", "24.0.0")
    table.add_row("Python", sys.version.split()[0])
    table.add_row("Kubernetes", "✅ 支持")
    table.add_row("Docker", "✅ 支持")
    table.add_row("AWS", "✅ 支持")
    table.add_row("GCP", "✅ 支持")
    table.add_row("Azure", "✅ 支持")
    table.add_row("CI/CD", "✅ 支持")
    
    console.print(table)


if __name__ == '__main__':
    main()

import click
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import os

from parser import CodeParser
from simple_indexer import CodeIndexerSimple, SearchEngineSimple


console = Console()


class CodeRAGSystem:
    def __init__(self, embedding_dim: int = 128):
        self.parser = CodeParser()
        self.indexer: CodeIndexerSimple = None
        self.search_engine: SearchEngineSimple = None
        self.embedding_dim = embedding_dim
        self._loaded = False

    def build_index(self, root_path: str, show_progress: bool = True):
        root = Path(root_path).resolve()

        if not root.exists():
            raise ValueError(f"Path does not exist: {root}")

        if show_progress:
            console.print(f"[cyan]Scanning directory:[/cyan] {root}")

        parsed_files = self.parser.parse_directory(root, max_workers=4)
        all_chunks = self.parser.get_all_chunks(parsed_files)

        if show_progress:
            console.print(f"[green]Found {len(all_chunks)} code chunks in {len(parsed_files)} files[/green]")

        self.indexer = CodeIndexerSimple(embedding_dim=self.embedding_dim)
        self.indexer.build(all_chunks, show_progress=show_progress)

        data_dir = Path("./data")
        data_dir.mkdir(parents=True, exist_ok=True)

        self.indexer.save(
            str(data_dir / "index.npy"),
            str(data_dir / "metadata.json"),
            str(data_dir / "bm25.json")
        )

        if show_progress:
            total_size = sum(f.stat().st_size for f in data_dir.glob("*"))
            console.print(f"[green]Index saved to {data_dir} ({total_size / (1024*1024):.2f} MB)[/green]")

        self.search_engine = SearchEngineSimple(self.indexer)
        self._loaded = True

    def load_index(self):
        data_dir = Path("./data")
        self.indexer = CodeIndexerSimple(embedding_dim=self.embedding_dim)
        self.indexer.load(
            str(data_dir / "index.npy"),
            str(data_dir / "metadata.json"),
            str(data_dir / "bm25.json")
        )
        self.search_engine = SearchEngineSimple(self.indexer)
        self._loaded = True
        console.print(f"[green]Loaded index with {len(self.indexer.metadata)} chunks[/green]")

    def search(self, query: str, top_k: int = None) -> list:
        if not self._loaded:
            raise RuntimeError("Index not loaded. Call load_index() first.")
        return self.search_engine.search(query, top_k)


def display_results(results: list, show_content: bool = True, max_results: int = 5):
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"\n[cyan]Found {len(results)} results:[/cyan]\n")

    for i, result in enumerate(results[:max_results], 1):
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()

        table.add_row("File:", f"{result['file_path']}")
        table.add_row("Lines:", f"{result['start_line']} - {result['end_line']}")

        if result.get('function_name'):
            table.add_row("Function:", result['function_name'])
        if result.get('class_name'):
            table.add_row("Class:", result['class_name'])

        table.add_row("Score:", f"{result['score']:.3f}")

        console.print(Panel(table, title=f"[bold cyan]Result {i}[/bold cyan]", border_style="cyan"))

        if show_content:
            content = result.get('content', '')
            if len(content) > 500:
                content = content[:500] + "..."

            try:
                lexer = result.get('language', 'text')
                syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)
            except Exception:
                syntax = content

            console.print(syntax)
            console.print()

    if len(results) > max_results:
        console.print(f"[dim]... and {len(results) - max_results} more results[/dim]")


@click.group()
def cli():
    """Code RAG System - Fast code search for large codebases"""
    pass


@cli.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--dim', default=128, help='Embedding dimension')
@click.option('--rebuild', is_flag=True, help='Force rebuild index')
def build(source_path, dim, rebuild):
    """Build index from source code directory"""
    system = CodeRAGSystem(embedding_dim=dim)

    index_path = Path("./data/index.npy")
    if index_path.exists() and not rebuild:
        if not Confirm.ask(f"[yellow]Index exists at ./data. Rebuild?[/yellow]"):
            console.print("[cyan]Skipping build[/cyan]")
            return

    try:
        system.build_index(source_path)
        console.print("[bold green]Build complete![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Build failed: {e}[/bold red]")
        raise


@cli.command()
@click.option('--dim', default=128, help='Embedding dimension')
def load(dim):
    """Load existing index"""
    system = CodeRAGSystem(embedding_dim=dim)
    try:
        system.load_index()
        console.print("[bold green]Load complete![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Load failed: {e}[/bold red]")


@cli.command()
@click.argument('query')
@click.option('--top-k', '-k', type=int, default=5, help='Number of results')
@click.option('--no-content', is_flag=True, help='Hide code content')
@click.option('--dim', default=128, help='Embedding dimension')
def search(query, top_k, no_content, dim):
    """Search code with natural language query"""
    system = CodeRAGSystem(embedding_dim=dim)

    try:
        system.load_index()
        results = system.search(query, top_k=top_k)
        display_results(results, show_content=not no_content)
    except FileNotFoundError:
        console.print("[yellow]Index not found. Run 'build' command first.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Search failed: {e}[/bold red]")


@cli.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--dim', default=128, help='Embedding dimension')
def interactive(source_path, dim):
    """Interactive search mode"""
    system = CodeRAGSystem(embedding_dim=dim)
    index_path = Path("./data/index.npy")

    if not index_path.exists():
        console.print(f"[yellow]Index not found. Building from {source_path}...[/yellow]")
        system.build_index(source_path)
    else:
        system.load_index()

    console.print("\n[bold cyan]Code RAG Interactive Mode[/bold cyan]")
    console.print("[dim]Type 'quit' or 'exit' to exit[/dim]\n")

    while True:
        try:
            query = Prompt.ask("[bold green]>[/bold green]")
            if query.lower() in ('quit', 'exit', 'q'):
                break
            if not query.strip():
                continue

            results = system.search(query)
            display_results(results)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    console.print("\n[dim]Goodbye![/dim]")


@cli.command()
@click.option('--dim', default=128, help='Embedding dimension')
def stats(dim):
    """Show index statistics"""
    system = CodeRAGSystem(embedding_dim=dim)

    try:
        system.load_index()

        data_dir = Path("./data")

        table = Table(title="Index Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Chunks", str(len(system.indexer.metadata)))

        if (data_dir / "index.npy").exists():
            index_size = (data_dir / "index.npy").stat().st_size / (1024*1024)
            table.add_row("Index Size", f"{index_size:.2f} MB")

        files = set(m['file_path'] for m in system.indexer.metadata)
        table.add_row("Unique Files", str(len(files)))

        languages = {}
        for m in system.indexer.metadata:
            lang = m.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1

        top_langs = sorted(languages.items(), key=lambda x: -x[1])[:5]
        table.add_row("Top Languages", ", ".join(f"{k}({v})" for k, v in top_langs))

        console.print(table)

    except FileNotFoundError:
        console.print("[yellow]Index not found. Run 'build' command first.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Failed: {e}[/bold red]")


if __name__ == "__main__":
    cli()

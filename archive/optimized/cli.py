import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Code RAG - Intelligent code search and Q&A system"""
    pass


@cli.command()
@click.argument('source_path', type=click.Path(exists=True))
@click.option('--storage', '-s', default='./data', help='Storage path')
@click.option('--chunk-size', default=512, help='Chunk size in lines')
@click.option('--rebuild', is_flag=True, help='Force rebuild index')
@click.option('--embedding', default='all-MiniLM-L6-v2', help='Embedding model')
def build(source_path, storage, chunk_size, rebuild, embedding):
    """Build index from source code directory"""
    from optimized.storage import StorageFacade
    from optimized.chunker import SemanticChunker
    from optimized.embedding import OptimizedIndexer, EmbeddingEngine
    from stage1.parser import DirectoryParser

    start_time = time.time()

    storage_path = Path(storage)
    storage_path.mkdir(parents=True, exist_ok=True)

    if rebuild:
        console.print(f"[yellow]Rebuilding index at {storage}[/yellow]")
        facade = StorageFacade(storage)
        facade.clear()
    else:
        facade = StorageFacade(storage)

    console.print(f"[cyan]Parsing {source_path}...[/cyan]")
    parser = DirectoryParser()
    files, chunks, stats = parser.parse_directory(Path(source_path))

    console.print(f"[green]Found {len(files)} files, {len(chunks)} chunks[/green]")

    console.print(f"[cyan]Chunking code...[/cyan]")
    chunker = SemanticChunker()
    all_chunks = []
    for file in files:
        file_chunks = chunker.chunk(
            file.content,
            str(file.relative_path),
            file.language
        )
        all_chunks.extend(file_chunks)

    console.print(f"[green]Created {len(all_chunks)} chunks[/green]")

    console.print(f"[cyan]Saving to storage...[/cyan]")
    facade.save_chunks(all_chunks)

    console.print(f"[cyan]Building vector index...[/cyan]")
    embed_config = {"model_name": embedding}
    emb = EmbeddingEngine()
    indexer = OptimizedIndexer(embedding_engine=emb)
    indexer.build_index(all_chunks)
    indexer.save(
        str(storage_path / "index.npy"),
        str(storage_path / "metadata.json")
    )

    elapsed = time.time() - start_time
    index_size = sum(f.stat().st_size for f in storage_path.glob("*") if f.is_file())

    console.print()
    console.print(f"[bold green]✓ Build complete![/bold green]")
    console.print(f"  Files: {len(files)}")
    console.print(f"  Chunks: {len(all_chunks)}")
    console.print(f"  Time: {elapsed:.2f}s")
    console.print(f"  Size: {index_size / 1024 / 1024:.2f} MB")


@cli.command()
@click.argument('query')
@click.option('--storage', '-s', default='./data', help='Storage path')
@click.option('--top-k', '-k', default=5, help='Number of results')
@click.option('--lang', help='Filter by language')
def search(query, storage, top_k, lang):
    """Search code with natural language query"""
    from optimized.storage import StorageFacade
    from optimized.embedding import OptimizedIndexer, EmbeddingEngine

    index_path = Path(storage) / "index.npy"
    meta_path = Path(storage) / "metadata.json"

    if not index_path.exists():
        console.print(f"[yellow]Index not found at {storage}. Run 'build' first.[/yellow]")
        return

    emb = EmbeddingEngine()
    indexer = OptimizedIndexer(embedding_engine=emb)
    indexer.load(str(index_path), str(meta_path))

    results = indexer.search(query, top_k=top_k)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"\n[cyan]Found {len(results)} results:[/cyan]\n")

    for i, r in enumerate(results, 1):
        console.print(Panel(
            f"[bold]{r['file_path']}[/bold] (lines {r['start_line']}-{r['end_line']})\n"
            f"[yellow]Score:[/yellow] {r['score']:.3f} | [yellow]Type:[/yellow] {r['chunk_type']}",
            title=f"[bold cyan]Result {i}[/bold cyan]",
            border_style="cyan"
        ))

        content = r['content']
        if len(content) > 300:
            content = content[:300] + "..."

        try:
            syntax = Syntax(content, r['language'] or 'python', theme="monokai", line_numbers=True)
            console.print(syntax)
        except:
            console.print(content)

        console.print()


@cli.command()
@click.option('--storage', '-s', default='./data', help='Storage path')
def stats(storage):
    """Show index statistics"""
    from optimized.storage import StorageFacade

    facade = StorageFacade(storage)
    stats = facade.stats()

    table = Table(title="Index Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Chunks", str(stats.get('total_chunks', 0)))
    table.add_row("Total Files", str(stats.get('total_files', 0)))
    table.add_row("Total Symbols", str(stats.get('total_symbols', 0)))
    table.add_row("DB Size", f"{stats.get('db_size_bytes', 0) / 1024 / 1024:.2f} MB")

    if 'by_language' in stats:
        table.add_row("Languages", ", ".join(
            f"{k}({v})" for k, v in list(stats['by_language'].items())[:5]
        ))

    console.print(table)


@cli.command()
@click.argument('symbol_name')
@click.option('--storage', '-s', default='./data', help='Storage path')
def symbol(symbol_name, storage):
    """Find symbol definitions"""
    from optimized.storage import StorageFacade

    facade = StorageFacade(storage)
    results = facade.get_by_symbol(symbol_name)

    if not results:
        console.print(f"[yellow]Symbol '{symbol_name}' not found[/yellow]")
        return

    console.print(f"\n[green]Found {len(results)} definitions:[/green]\n")

    table = Table()
    table.add_column("File", style="cyan")
    table.add_column("Line", style="magenta")
    table.add_column("Type")

    for r in results:
        table.add_row(
            r['file_path'],
            str(r['start_line']),
            r['chunk_type']
        )

    console.print(table)


@cli.command()
@click.argument('query')
@click.option('--storage', '-s', default='./data', help='Storage path')
@click.option('--top-k', '-k', default=5, help='Number of results')
def ask(query, storage, top_k):
    """Ask questions about the codebase"""
    from optimized.storage import StorageFacade
    from optimized.embedding import OptimizedIndexer, EmbeddingEngine
    from stage4 import CodeQAEngine

    index_path = Path(storage) / "index.npy"
    meta_path = Path(storage) / "metadata.json"

    if not index_path.exists():
        console.print(f"[yellow]Index not found. Run 'build' first.[/yellow]")
        return

    emb = EmbeddingEngine()
    indexer = OptimizedIndexer(embedding_engine=emb)
    indexer.load(str(index_path), str(meta_path))

    results = indexer.search(query, top_k=top_k)

    if not results:
        console.print("[yellow]No relevant code found[/yellow]")
        return

    qa = CodeQAEngine()
    result = qa.ask(question=query, code_chunks=results)

    console.print(Panel(
        f"[bold cyan]{result.answer}[/bold cyan]\n\n"
        f"[dim]Latency: {result.latency_ms:.2f}ms | Model: {result.model}[/dim]",
        title="[bold green]Answer[/bold green]",
        border_style="green"
    ))

    if result.sources:
        console.print("\n[cyan]Sources:[/cyan]")
        for s in result.sources[:3]:
            console.print(f"  - {s['file']} (lines {s['lines']})")


@cli.command()
@click.option('--storage', '-s', default='./data', help='Storage path')
@click.option('--host', default='0.0.0.0', help='Host')
@click.option('--port', default=8000, help='Port')
def serve(storage, host, port):
    """Start API server"""
    try:
        from optimized.api import CodeRAGAPI
        console.print(f"[cyan]Starting server at http://{host}:{port}[/cyan]")
        api = CodeRAGAPI(storage)
        api.run(host=host, port=port)
    except ImportError:
        console.print("[red]FastAPI not installed. Run: pip install fastapi uvicorn[/red]")


@cli.command()
def interactive():
    """Interactive search mode"""
    console.print("[bold cyan]Code RAG Interactive Mode[/bold cyan]")
    console.print("[dim]Commands:[/dim]")
    console.print("  search <query>  - Search code")
    console.print("  ask <question>  - Ask about code")
    console.print("  symbol <name>   - Find symbol")
    console.print("  stats          - Show statistics")
    console.print("  quit           - Exit\n")

    while True:
        try:
            cmd = input("\n> ").strip()
            if cmd.lower() in ('quit', 'exit', 'q'):
                break

            parts = cmd.split(maxsplit=1)
            if not parts:
                continue

            command = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if command == 'search':
                if arg:
                    search.callback(arg, storage='./data', top_k=5)
                else:
                    console.print("[yellow]Usage: search <query>[/yellow]")
            elif command == 'ask':
                if arg:
                    ask.callback(arg, storage='./data', top_k=5)
                else:
                    console.print("[yellow]Usage: ask <question>[/yellow]")
            elif command == 'symbol':
                if arg:
                    symbol.callback(arg, storage='./data')
                else:
                    console.print("[yellow]Usage: symbol <name>[/yellow]")
            elif command == 'stats':
                stats.callback(storage='./data')
            else:
                console.print(f"[red]Unknown command: {command}[/red]")

        except KeyboardInterrupt:
            break
        except EOFError:
            break

    console.print("\n[dim]Goodbye![/dim]")


if __name__ == "__main__":
    cli()

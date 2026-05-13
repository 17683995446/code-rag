import click
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from stage1 import IndexBuilder
from stage2 import (
    MultiRetrieval, Reranker, ContextAugmenter,
    QueryParser, KeywordSearcher, SymbolSearcher, ExactLineSearcher,
    SearchOptions, RetrievalType, create_retriever
)


console = Console()


class CodeSearchSystem:
    def __init__(self, storage_path: str = "./data"):
        self.storage_path = storage_path
        self.builder = None
        self.retriever = None
        self.reranker = Reranker()
        self.context_augmenter = ContextAugmenter()

    def load(self, show_progress: bool = True):
        self.builder = IndexBuilder(storage_path=self.storage_path)
        indexer = self.builder.load(show_progress=show_progress)
        self.retriever = create_retriever(indexer, indexer.metadata)

    def search(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
        retrieval_types: list = None
    ) -> list:
        if not self.retriever:
            self.load(show_progress=False)

        options = SearchOptions(
            top_k=top_k,
            rerank=False,
            retrieval_types=retrieval_types or [RetrievalType.SEMANTIC, RetrievalType.KEYWORD]
        )

        results = self.retriever.retrieve(query, options)

        if rerank:
            results = self.reranker.rerank(results, query, top_k)

        for result in results:
            self.context_augmenter.add_context(result)

        return results

    def search_exact(
        self,
        file_path: str,
        line: int = None,
        range_: tuple = None
    ) -> list:
        if not self.retriever:
            self.load(show_progress=False)

        exact_searcher = ExactLineSearcher(self.retriever.hybrid_engine.metadata)

        return exact_searcher.search_by_file_line(
            file_path, line, range_, top_k=10
        )

    def search_symbol(self, symbol_name: str, exact: bool = False) -> list:
        if not self.retriever:
            self.load(show_progress=False)

        symbol_searcher = SymbolSearcher(self.retriever.hybrid_engine.metadata)

        return symbol_searcher.search_by_name(symbol_name, exact=exact, top_k=10)


def display_results(results: list, show_content: bool = True, max_results: int = 5):
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"\n[cyan]Found {len(results)} results:[/cyan]\n")

    for i, result in enumerate(results[:max_results], 1):
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()

        table.add_row("File:", f"{result.file_path}")
        table.add_row("Lines:", f"{result.start_line} - {result.end_line}")
        table.add_row("Type:", f"{result.chunk_type}")
        table.add_row("Method:", f"[{result.retrieval_type}]")
        table.add_row("Score:", f"{result.score:.3f}")

        if result.symbols:
            sym_names = [s.get('name', '') for s in result.symbols[:3]]
            table.add_row("Symbols:", ", ".join(sym_names))

        console.print(Panel(table, title=f"[bold cyan]Result {i}[/bold cyan]", border_style="cyan"))

        if show_content:
            content = result.content
            if len(content) > 400:
                content = content[:400] + "..."

            if result.context_before:
                console.print(f"[dim]... (context before, {len(result.context_before.split(chr(10)))} lines)[/dim]")

            try:
                syntax = Syntax(content, result.language or 'python', theme="monokai", line_numbers=True)
            except Exception:
                syntax = content

            console.print(syntax)

            if result.context_after:
                console.print(f"[dim]... (context after, {len(result.context_after.split(chr(10)))} lines)[/dim]")

            console.print()

    if len(results) > max_results:
        console.print(f"[dim]... and {len(results) - max_results} more results[/dim]")


def display_exact_results(results: list):
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    console.print(f"\n[green]Found {len(results)} chunks in file:[/green]\n")

    table = Table()
    table.add_column("Line Range", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Symbols")

    for r in results:
        symbols = ", ".join([s.get('name', '') for s in r.get('symbols', [])[:3]])
        table.add_row(
            f"{r.get('start_line', 0)}-{r.get('end_line', 0)}",
            r.get('chunk_type', 'unknown'),
            symbols or "-"
        )

    console.print(table)


def display_symbol_results(results: list, symbol_name: str):
    if not results:
        console.print(f"[yellow]No definitions found for '{symbol_name}'[/yellow]")
        return

    console.print(f"\n[green]Found {len(results)} definitions:[/green]\n")

    table = Table()
    table.add_column("File", style="cyan")
    table.add_column("Line", style="magenta")
    table.add_column("Type")
    table.add_column("Name")

    for r in results:
        symbols = r.get('symbols', [])
        for sym in symbols[:2]:
            if symbol_name.lower() in sym.get('name', '').lower():
                table.add_row(
                    r.get('file_path', ''),
                    str(r.get('start_line', 0)),
                    sym.get('type', ''),
                    sym.get('name', '')
                )
                break

    console.print(table)


@click.group()
def cli():
    """Code Search System - Multi-modal code retrieval"""
    pass


@cli.command()
@click.argument('query')
@click.option('--top-k', '-k', default=5, help='Number of results')
@click.option('--no-rerank', is_flag=True, help='Skip reranking')
@click.option('--semantic/--no-semantic', default=True, help='Enable semantic search')
@click.option('--keyword/--no-keyword', default=True, help='Enable keyword search')
@click.option('--storage', '-s', default='./data', help='Index storage path')
def search(query, top_k, no_rerank, semantic, keyword, storage):
    """Search code with natural language query"""
    system = CodeSearchSystem(storage)

    try:
        system.load(show_progress=True)
    except FileNotFoundError:
        console.print("[yellow]Index not found. Run build command first.[/yellow]")
        return

    retrieval_types = []
    if semantic:
        retrieval_types.append(RetrievalType.SEMANTIC)
    if keyword:
        retrieval_types.append(RetrievalType.KEYWORD)

    results = system.search(
        query,
        top_k=top_k,
        rerank=not no_rerank,
        retrieval_types=retrieval_types
    )

    display_results(results)


@cli.command()
@click.argument('file_path')
@click.option('--line', '-l', type=int, help='Specific line number')
@click.option('--start', type=int, help='Start line')
@click.option('--end', '-e', type=int, help='End line')
@click.option('--storage', '-s', default='./data', help='Index storage path')
def exact(file_path, line, start, end, storage):
    """Search by exact file path and line number"""
    system = CodeSearchSystem(storage)

    try:
        system.load(show_progress=False)
    except FileNotFoundError:
        console.print("[yellow]Index not found.[/yellow]")
        return

    if start and end:
        results = system.search_exact(file_path, range_=(start, end))
    else:
        results = system.search_exact(file_path, line=line)

    display_exact_results(results)


@cli.command()
@click.argument('symbol_name')
@click.option('--exact', is_flag=True, help='Exact match only')
@click.option('--storage', '-s', default='./data', help='Index storage path')
def symbol(symbol_name, exact, storage):
    """Search for symbol (function/class) by name"""
    system = CodeSearchSystem(storage)

    try:
        system.load(show_progress=False)
    except FileNotFoundError:
        console.print("[yellow]Index not found.[/yellow]")
        return

    results = system.search_symbol(symbol_name, exact=exact)
    display_symbol_results(results, symbol_name)


@cli.command()
@click.argument('query')
@click.option('--storage', '-s', default='./data', help='Index storage path')
def explain(query, storage):
    """Explain query intent and show search plan"""
    system = CodeSearchSystem(storage)

    try:
        system.load(show_progress=False)
    except FileNotFoundError:
        console.print("[yellow]Index not found.[/yellow]")
        return

    parser = QueryParser()
    intent = parser.parse(query)

    console.print(f"\n[bold cyan]Query Analysis[/bold cyan]")
    console.print(f"Original: {query}")
    console.print(f"Intent Type: {intent.intent_type}")
    console.print(f"Keywords: {', '.join(intent.keywords)}")
    console.print(f"Entities: {', '.join(intent.entities)}")

    if intent.target_file:
        console.print(f"Target File: {intent.target_file}")
    if intent.target_symbol:
        console.print(f"Target Symbol: {intent.target_symbol}")
    if intent.line_number:
        console.print(f"Line Number: {intent.line_number}")

    console.print(f"\n[bold cyan]Recommended Retrieval Types[/bold cyan]")
    if intent.intent_type == "exact":
        console.print("  - EXACT (high priority)")
    if intent.intent_type in ("semantic", "general"):
        console.print("  - SEMANTIC (high priority)")
        console.print("  - KEYWORD (medium priority)")
    if intent.intent_type in ("structural", "call_graph"):
        console.print("  - STRUCTURAL (high priority)")
        console.print("  - CALL_GRAPH (high priority)")


@cli.command()
@click.option('--storage', '-s', default='./data', help='Index storage path')
def interactive(storage):
    """Interactive search mode"""
    system = CodeSearchSystem(storage)

    try:
        system.load(show_progress=True)
    except FileNotFoundError:
        console.print("[yellow]Index not found.[/yellow]")
        return

    console.print("\n[bold cyan]Code Search Interactive Mode[/bold cyan]")
    console.print("[dim]Commands:[/dim]")
    console.print("  :exact <file>:<line>  - Search exact location")
    console.print("  :symbol <name>        - Search by symbol name")
    console.print("  :explain <query>      - Analyze query intent")
    console.print("  :stats               - Show index statistics")
    console.print("  quit/exit            - Exit\n")

    from rich.prompt import Prompt

    while True:
        try:
            query = Prompt.ask("[bold green]>[/bold green]")
            query = query.strip()

            if query.lower() in ('quit', 'exit', 'q'):
                break

            if not query:
                continue

            if query.startswith(':'):
                parts = query[1:].split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if cmd == 'exact':
                    if ':' in args:
                        file_part, line_part = args.rsplit(':', 1)
                        try:
                            line = int(line_part)
                            results = system.search_exact(file_part, line=line)
                            display_exact_results(results)
                        except ValueError:
                            console.print("[red]Invalid line number[/red]")
                elif cmd == 'symbol':
                    results = system.search_symbol(args)
                    display_symbol_results(results, args)
                elif cmd == 'explain':
                    parser = QueryParser()
                    intent = parser.parse(args)
                    console.print(f"Intent: {intent.intent_type}")
                    console.print(f"Keywords: {intent.keywords}")
                elif cmd == 'stats':
                    from stage1 import StorageManager
                    sm = StorageManager(storage)
                    info = sm.get_file_info()
                    console.print("[cyan]Index files:[/cyan]")
                    for name, size in info.items():
                        console.print(f"  {name}: {size / 1024:.2f} KB")
                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]")
            else:
                results = system.search(query)
                display_results(results)

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    console.print("\n[dim]Goodbye![/dim]")


if __name__ == "__main__":
    cli()

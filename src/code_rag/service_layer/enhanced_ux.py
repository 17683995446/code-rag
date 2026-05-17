"""
Code RAG v18.5 - 用户体验增强模块
包含12个优化点的用户体验改进
"""

import sys
import os
import time
import json
import random
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.markdown import Markdown
    from rich import print as rprint
    from rich.theme import Theme
    from rich.text import Text
    from rich.style import Style
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


@dataclass
class UXConfig:
    """用户体验配置"""
    enable_color: bool = True
    enable_progress: bool = True
    enable_emoji: bool = True
    enable_sound: bool = False
    compact_mode: bool = False
    verbosity: int = 1
    theme: str = "default"
    auto_complete: bool = True


class EmojiPalette:
    """表情符号调色板"""
    SUCCESS = ["✅", "✨", "🎉", "👍", "🚀", "⭐"]
    WARNING = ["⚠️", "⚡", "❓", "❗"]
    ERROR = ["❌", "🚨", "💥", "🔥"]
    INFO = ["ℹ️", "📌", "🔔", "💡", "📚"]
    SEARCH = ["🔍", "🧐", "📖", "💫"]
    CODE = ["💻", "📝", "🔧", "🛠️", "🎯"]
    PROGRESS = ["⏳", "🔄", "⚙️", "📊", "📈"]
    
    @classmethod
    def get_success(cls) -> str:
        return random.choice(cls.SUCCESS)
    
    @classmethod
    def get_warning(cls) -> str:
        return random.choice(cls.WARNING)
    
    @classmethod
    def get_error(cls) -> str:
        return random.choice(cls.ERROR)


class ColorTheme:
    """颜色主题"""
    
    THEMES = {
        "default": {
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "blue",
            "code": "cyan",
            "highlight": "purple"
        },
        "dark": {
            "success": "bright_green",
            "error": "bright_red",
            "warning": "bright_yellow",
            "info": "bright_blue",
            "code": "bright_cyan",
            "highlight": "bright_purple"
        },
        "mono": {
            "success": "white",
            "error": "white",
            "warning": "white",
            "info": "white",
            "code": "white",
            "highlight": "white"
        },
        "ocean": {
            "success": "cyan",
            "error": "magenta",
            "warning": "yellow",
            "info": "blue",
            "code": "cyan",
            "highlight": "magenta"
        }
    }
    
    @classmethod
    def get_theme(cls, name: str) -> Dict[str, str]:
        return cls.THEMES.get(name, cls.THEMES["default"])


class TextFormatter:
    """文本格式化器"""
    
    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def wrap_text(text: str, line_length: int = 80) -> str:
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > line_length:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
            else:
                current_line.append(word)
                current_length += len(word) + 1
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    @staticmethod
    def highlight_keywords(text: str, keywords: List[str]) -> str:
        result = text
        for keyword in keywords:
            if keyword:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                result = pattern.sub(f"[{keyword}]", result)
        return result
    
    @staticmethod
    def format_bytes(size: float) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    @staticmethod
    def format_time(seconds: float) -> str:
        if seconds < 1:
            return f"{seconds * 1000:.2f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.2f}s"


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, console: Optional["EnhancedUX"] = None):
        self.console = console
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.start_times: Dict[str, float] = {}
        
    def start(self, task_id: str, description: str, total: int = 100) -> None:
        self.tasks[task_id] = {
            "description": description,
            "current": 0,
            "total": total,
            "status": "running"
        }
        self.start_times[task_id] = time.time()
        
        if self.console and HAS_RICH:
            self.console.print_progress_start(task_id, description, total)
    
    def update(self, task_id: str, advance: int = 1, extra: str = "") -> None:
        if task_id in self.tasks:
            self.tasks[task_id]["current"] = min(
                self.tasks[task_id]["current"] + advance,
                self.tasks[task_id]["total"]
            )
            
            if self.console and HAS_RICH:
                self.console.print_progress_update(task_id, self.tasks[task_id]["current"], extra)
    
    def finish(self, task_id: str, success: bool = True) -> float:
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "completed" if success else "failed"
            elapsed = time.time() - self.start_times.get(task_id, 0)
            
            if self.console and HAS_RICH:
                self.console.print_progress_end(task_id, success, elapsed)
            
            return elapsed
        return 0
    
    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.tasks.get(task_id)
    
    def get_elapsed(self, task_id: str) -> float:
        if task_id in self.start_times:
            return time.time() - self.start_times[task_id]
        return 0


class InteractivePrompt:
    """交互式提示"""
    
    def __init__(self, console: Optional["EnhancedUX"] = None):
        self.console = console
        self.history: List[str] = []
        self.auto_complete: Dict[str, List[str]] = {}
        
    def prompt(self, question: str, default: str = "", 
                suggestions: Optional[List[str]] = None) -> str:
        if suggestions:
            if self.console:
                self.console.print_suggestions(suggestions)
        
        prompt_text = f"{question} [默认: {default}] " if default else f"{question} "
        
        try:
            response = input(prompt_text)
            response = response.strip()
            
            if not response:
                response = default
            
            if response:
                self.history.append(response)
            
            return response
        except (EOFError, KeyboardInterrupt):
            print("\n")
            return default
    
    def confirm(self, question: str, default: bool = True) -> bool:
        default_str = "Y/n" if default else "y/N"
        response = self.prompt(f"{question} [{default_str}]", default_str).lower()
        
        if response in ["yes", "y", ""] and default:
            return True
        elif response in ["yes", "y"]:
            return True
        return False
    
    def choose(self, question: str, options: List[str], 
              default: Optional[int] = None) -> str:
        self.console.print_options(question, options)
        
        while True:
            try:
                prompt_text = f"请选择 [1-{len(options)}]"
                if default is not None:
                    prompt_text += f" [默认: {default}]"
                
                choice = self.prompt(prompt_text, str(default) if default else "")
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return options[idx]
                
                self.console.print_warning("无效选择，请重新输入")
            except (EOFError, KeyboardInterrupt):
                if default is not None:
                    return options[default - 1]
                raise
    
    def multiline_input(self, question: str, end_marker: str = ".") -> str:
        self.console.print_info(f"{question} (输入 '{end_marker}' 结束输入)")
        
        lines = []
        while True:
            try:
                line = input("> ")
                if line.strip() == end_marker:
                    break
                lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        
        return "\n".join(lines)


class CommandHistory:
    """命令历史记录"""
    
    def __init__(self, max_history: int = 100):
        self.history: List[str] = []
        self.max_history = max_history
        self.index = -1
        self.history_file: Optional[Path] = None
    
    def set_history_file(self, path: str) -> None:
        self.history_file = Path(path)
        if self.history_file.exists():
            self.load()
    
    def add(self, command: str) -> None:
        if command and (not self.history or command != self.history[-1]):
            self.history.append(command)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            self.index = len(self.history)
            self.save()
    
    def get_previous(self) -> Optional[str]:
        if self.history and self.index > 0:
            self.index -= 1
            return self.history[self.index]
        return None
    
    def get_next(self) -> Optional[str]:
        if self.history and self.index < len(self.history) - 1:
            self.index += 1
            return self.history[self.index]
        return None
    
    def save(self) -> None:
        if self.history_file:
            try:
                self.history_file.write_text("\n".join(self.history), encoding="utf-8")
            except Exception:
                pass
    
    def load(self) -> None:
        if self.history_file and self.history_file.exists():
            try:
                self.history = self.history_file.read_text(encoding="utf-8").splitlines()
                self.index = len(self.history)
            except Exception:
                pass
    
    def clear(self) -> None:
        self.history = []
        self.index = -1
        if self.history_file:
            try:
                self.history_file.unlink()
            except Exception:
                pass


class EnhancedUX:
    """增强型用户体验类，包含12个优化点"""
    
    def __init__(self, config: Optional[UXConfig] = None):
        self.config = config or UXConfig()
        self.console = Console() if HAS_RICH else None
        self.color_theme = ColorTheme.get_theme(self.config.theme)
        self.progress_tracker = ProgressTracker(self)
        self.interactive = InteractivePrompt(self)
        self.command_history = CommandHistory()
        self.emoji_palette = EmojiPalette()
        
        # 优化点1: 配置文件支持
        self.load_config()
        
        # 优化点2: 会话开始时间
        self.session_start = datetime.now()
    
    # ============ 优化点1: 配置文件支持 ============
    def load_config(self) -> None:
        config_file = Path.home() / ".code_rag_config.json"
        if config_file.exists():
            try:
                config_data = json.loads(config_file.read_text(encoding="utf-8"))
                self.config = UXConfig(**config_data)
            except Exception:
                pass
    
    def save_config(self) -> None:
        config_file = Path.home() / ".code_rag_config.json"
        config_file.write_text(json.dumps(self.__dict__.get("config", UXConfig()).__dict__, 
                                          indent=2, ensure_ascii=False), encoding="utf-8")
    
    # ============ 优化点2: 增强的颜色输出 ============
    def print(self, text: str, style: Optional[str] = None, end: str = "\n") -> None:
        if HAS_RICH and self.config.enable_color:
            rprint(text, style=style, end=end)
        else:
            print(text, end=end)
    
    def print_success(self, message: str) -> None:
        emoji = EmojiPalette.get_success() if self.config.enable_emoji else ""
        if HAS_RICH and self.config.enable_color:
            self.print(f"{emoji} {message}", style=self.color_theme["success"])
        else:
            print(f"{emoji} {message}")
    
    def print_error(self, message: str) -> None:
        emoji = EmojiPalette.get_error() if self.config.enable_emoji else ""
        if HAS_RICH and self.config.enable_color:
            self.print(f"{emoji} {message}", style=self.color_theme["error"])
        else:
            print(f"{emoji} {message}")
    
    def print_warning(self, message: str) -> None:
        emoji = EmojiPalette.get_warning() if self.config.enable_emoji else ""
        if HAS_RICH and self.config.enable_color:
            self.print(f"{emoji} {message}", style=self.color_theme["warning"])
        else:
            print(f"{emoji} {message}")
    
    def print_info(self, message: str) -> None:
        emoji = random.choice(EmojiPalette.INFO) if self.config.enable_emoji else ""
        if HAS_RICH and self.config.enable_color:
            self.print(f"{emoji} {message}", style=self.color_theme["info"])
        else:
            print(f"{emoji} {message}")
    
    # ============ 优化点3: 高级进度条 ============
    def print_progress_start(self, task_id: str, description: str, total: int) -> None:
        if HAS_RICH and self.config.enable_progress:
            self.print(f"\n⏳ 开始: {description}")
    
    def print_progress_update(self, task_id: str, current: int, extra: str = "") -> None:
        if HAS_RICH and self.config.enable_progress:
            if current % 10 == 0 or extra:
                self.print(f"  进度: {current}% {extra}")
    
    def print_progress_end(self, task_id: str, success: bool, elapsed: float) -> None:
        if HAS_RICH and self.config.enable_progress:
            status = "完成" if success else "失败"
            self.print(f"\n✅ {status} - 耗时: {TextFormatter.format_time(elapsed)}")
    
    # ============ 优化点4: 表格显示 ============
    def print_table(self, data: List[Dict[str, Any]], 
                   title: Optional[str] = None, 
                   columns: Optional[List[str]] = None) -> None:
        if not data:
            self.print_info("没有数据可显示")
            return
        
        if HAS_RICH:
            table = Table(title=title)
            
            if not columns:
                columns = list(data[0].keys())
            
            for col in columns:
                table.add_column(col, overflow="fold")
            
            for item in data:
                row = [str(item.get(col, "")) for col in columns]
                table.add_row(*row)
            
            self.console.print(table)
        else:
            if title:
                self.print(title)
            
            headers = columns or list(data[0].keys())
            print(" | ".join(headers))
            print("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
            
            for item in data:
                row = [str(item.get(col, "")) for col in headers]
                print(" | ".join(row))
    
    # ============ 优化点5: 代码高亮显示 ============
    def print_code(self, code: str, language: str = "python", 
                  line_numbers: bool = True) -> None:
        lines = code.split("\n")
        
        if HAS_RICH:
            max_line_num_len = len(str(len(lines)))
            
            for i, line in enumerate(lines, 1):
                if line_numbers:
                    line_num = f"{i:>{max_line_num_len}}"
                    text = f"{line_num} | {line}"
                    self.print(text, style=self.color_theme["code"])
                else:
                    self.print(line, style=self.color_theme["code"])
        else:
            for i, line in enumerate(lines, 1):
                if line_numbers:
                    print(f"{i:4} | {line}")
                else:
                    print(line)
    
    # ============ 优化点6: Markdown支持 ============
    def print_markdown(self, markdown_text: str) -> None:
        if HAS_RICH:
            md = Markdown(markdown_text)
            self.console.print(md)
        else:
            print(markdown_text)
    
    # ============ 优化点7: 树形结构显示 ============
    def print_tree(self, data: Dict[str, Any], root_label: str = "目录") -> None:
        if HAS_RICH:
            tree = Tree(f"[bold blue]{root_label}[/bold blue]")
            
            def add_nodes(parent_tree: Tree, data_dict: Dict[str, Any]):
                for key, value in data_dict.items():
                    if isinstance(value, dict):
                        branch = parent_tree.add(f"[green]{key}[/green]")
                        add_nodes(branch, value)
                    elif isinstance(value, list):
                        branch = parent_tree.add(f"[cyan]{key}[/cyan] ({len(value)} items)")
                        for item in value[:5]:  # Show max 5 items
                            if isinstance(item, dict):
                                add_nodes(branch, item)
                            else:
                                branch.add(str(item))
                    else:
                        parent_tree.add(f"[yellow]{key}[/yellow]: {value}")
            
            add_nodes(tree, data)
            self.console.print(tree)
        else:
            print(f"{root_label}")
            for key, value in data.items():
                print(f"  - {key}: {value}")
    
    # ============ 优化点8: 面板显示 ============
    def print_panel(self, content: str, title: Optional[str] = None, 
                   border_style: str = "blue") -> None:
        if HAS_RICH:
            panel = Panel(content, title=title, border_style=border_style)
            self.console.print(panel)
        else:
            if title:
                print(f"{'=' * 50}")
                print(f"  {title}")
                print(f"{'=' * 50}")
            print(content)
    
    # ============ 优化点9: 统计信息展示 ============
    def print_stats(self, stats: Dict[str, Any], title: str = "统计信息") -> None:
        if HAS_RICH:
            self.print_panel(
                "\n".join([f"  {key}: {value}" for key, value in stats.items()]),
                title=title
            )
        else:
            print(f"\n{title}")
            print("-" * 40)
            for key, value in stats.items():
                print(f"  {key}: {value}")
    
    # ============ 优化点10: 建议列表 ============
    def print_suggestions(self, suggestions: List[str]) -> None:
        if not suggestions:
            return
        
        self.print("\n💡 建议:")
        for i, suggestion in enumerate(suggestions, 1):
            self.print(f"  {i}. {suggestion}")
    
    # ============ 优化点11: 选项列表 ============
    def print_options(self, question: str, options: List[str]) -> None:
        self.print(f"\n{question}")
        for i, option in enumerate(options, 1):
            self.print(f"  {i}. {option}")
    
    # ============ 优化点12: 会话摘要 ============
    def print_session_summary(self) -> None:
        duration = datetime.now() - self.session_start
        stats = {
            "会话开始": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "会话时长": str(duration),
            "历史命令数": len(self.command_history.history)
        }
        
        self.print_stats(stats, "会话摘要")
    
    # ============ 实用方法 ============
    def clear_screen(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")
    
    def sleep_with_spinner(self, seconds: float, message: str = "等待") -> None:
        if HAS_RICH and self.config.enable_progress:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task(message, total=100)
                for i in range(100):
                    progress.update(task, advance=1)
                    time.sleep(seconds / 100)
        else:
            time.sleep(seconds)


def create_ux(config: Optional[UXConfig] = None) -> EnhancedUX:
    """创建增强型用户体验对象的工厂函数"""
    return EnhancedUX(config)

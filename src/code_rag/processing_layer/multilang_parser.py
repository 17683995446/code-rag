"""
Code RAG v20.0 - 多语言解析基础设施
支持Python + JavaScript + Java + C++ + Go
"""

import ast
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Language(Enum):
    """支持的编程语言"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"


@dataclass
class CodeEntity:
    """统一的代码实体表示"""
    entity_type: str  # function, class, variable, module
    name: str
    location: str = ""
    line_start: int = 1
    line_end: int = 1
    code: str = ""
    language: Language = Language.PYTHON
    documentation: str = ""
    complexity: str = "low"
    dependencies: List[str] = field(default_factory=list)
    children: List["CodeEntity"] = field(default_factory=list)


@dataclass
class CodeModule:
    """代码模块（文件级别）"""
    file_path: str
    language: Language
    entities: List[CodeEntity] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    module_doc: str = ""
    dependencies: List[str] = field(default_factory=list)


class BaseParser:
    """解析器抽象基类"""
    
    def __init__(self):
        self.language: Language
    
    def parse(self, code: str, file_path: str = "") -> CodeModule:
        """解析代码为统一表示"""
        raise NotImplementedError()
    
    def extract_entities(self, code: str) -> List[CodeEntity]:
        """提取代码中的实体"""
        raise NotImplementedError()
    
    def extract_imports(self, code: str) -> List[str]:
        """提取导入/导入语句"""
        raise NotImplementedError()


class PythonParser(BaseParser):
    """Python代码解析器"""
    
    def __init__(self):
        self.language = Language.PYTHON
    
    def parse(self, code: str, file_path: str = "") -> CodeModule:
        """解析Python代码"""
        entities = self.extract_entities(code)
        imports = self.extract_imports(code)
        
        return CodeModule(
            file_path=file_path,
            language=self.language,
            entities=entities,
            imports=imports
        )
    
    def extract_entities(self, code: str) -> List[CodeEntity]:
        """提取Python代码实体"""
        entities = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    entities.append(CodeEntity(
                        entity_type="function",
                        name=node.name,
                        line_start=node.lineno,
                        line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        code=f"def {node.name}(): ...",
                        language=Language.PYTHON,
                        documentation=ast.get_docstring(node) or ""
                    ))
                elif isinstance(node, ast.ClassDef):
                    class_entity = CodeEntity(
                        entity_type="class",
                        name=node.name,
                        line_start=node.lineno,
                        line_end=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        code=f"class {node.name}: ...",
                        language=Language.PYTHON,
                        documentation=ast.get_docstring(node) or ""
                    )
                    entities.append(class_entity)
        except SyntaxError:
            pass
        
        return entities
    
    def extract_imports(self, code: str) -> List[str]:
        """提取Python导入语句"""
        imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(f"Import at line {node.lineno}")
        except SyntaxError:
            pass
        return imports


class JavaScriptParser(BaseParser):
    """JavaScript/TypeScript代码解析器"""
    
    def __init__(self):
        self.language = Language.JAVASCRIPT
    
    def parse(self, code: str, file_path: str = "") -> CodeModule:
        """解析JS/TS代码"""
        entities = self.extract_entities(code)
        imports = self.extract_imports(code)
        
        return CodeModule(
            file_path=file_path,
            language=self.language,
            entities=entities,
            imports=imports
        )
    
    def extract_entities(self, code: str) -> List[CodeEntity]:
        """提取JS代码实体"""
        entities = []
        lines = code.split('\n')
        
        # 类声明
        class_pattern = re.compile(r'class\s+(\w+)')
        for line_num, line in enumerate(lines, 1):
            match = class_pattern.search(line)
            if match:
                entities.append(CodeEntity(
                    entity_type="class",
                    name=match.group(1),
                    line_start=line_num,
                    line_end=line_num,
                    code=line.strip(),
                    language=Language.JAVASCRIPT,
                    documentation=""
                ))
        
        # 函数声明
        func_patterns = [
            re.compile(r'function\s+(\w+)\s*\('),
            re.compile(r'(\w+)\s*[:=]\s*(?:async\s+)?function'),
            re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*\('),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in func_patterns:
                match = pattern.search(line)
                if match:
                    name = match.group(1)
                    existing = [e for e in entities if e.name == name]
                    if not existing:
                        entities.append(CodeEntity(
                            entity_type="function",
                            name=name,
                            line_start=line_num,
                            line_end=line_num,
                            code=line.strip(),
                            language=Language.JAVASCRIPT,
                            documentation=""
                        ))
        
        return entities
    
    def extract_imports(self, code: str) -> List[str]:
        """提取JS导入语句"""
        imports = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if 'import' in line or 'require' in line:
                imports.append(f"Import at line {line_num}")
        return imports


class JavaParser(BaseParser):
    """Java 代码解析器"""
    
    def __init__(self):
        self.language = Language.JAVA
    
    def parse(self, code: str, file_path: str = "") -> CodeModule:
        entities = self.extract_entities(code)
        imports = self.extract_imports(code)
        
        return CodeModule(
            file_path=file_path,
            language=self.language,
            entities=entities,
            imports=imports
        )
    
    def extract_entities(self, code: str) -> List[CodeEntity]:
        entities = []
        lines = code.split('\n')
        
        # 类声明
        class_pattern = re.compile(r'(?:public|private|protected)?\s*(?:static|final)?\s*class\s+(\w+)')
        for line_num, line in enumerate(lines, 1):
            match = class_pattern.search(line)
            if match:
                entities.append(CodeEntity(
                    entity_type="class",
                    name=match.group(1),
                    line_start=line_num,
                    line_end=line_num,
                    code=line.strip(),
                    language=Language.JAVA,
                    documentation=""
                ))
        
        # 方法声明
        method_patterns = [
            re.compile(r'(?:public|private|protected)?\s*(?:static|final)?\s*(?:\w+)\s+(\w+)\s*\('),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in method_patterns:
                match = pattern.search(line)
                if match and 'class' not in line.lower() and 'interface' not in line.lower():
                    name = match.group(1)
                    existing = [e for e in entities if e.name == name]
                    if not existing:
                        entities.append(CodeEntity(
                            entity_type="function",
                            name=name,
                            line_start=line_num,
                            line_end=line_num,
                            code=line.strip(),
                            language=Language.JAVA,
                            documentation=""
                        ))
        
        return entities
    
    def extract_imports(self, code: str) -> List[str]:
        imports = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('import'):
                imports.append(f"Import at line {line_num}")
        return imports


class CppParser(BaseParser):
    """C++ 代码解析器"""
    
    def __init__(self):
        self.language = Language.CPP
    
    def parse(self, code: str, file_path: str = "") -> CodeModule:
        entities = self.extract_entities(code)
        imports = self.extract_imports(code)
        
        return CodeModule(
            file_path=file_path,
            language=self.language,
            entities=entities,
            imports=imports
        )
    
    def extract_entities(self, code: str) -> List[CodeEntity]:
        entities = []
        lines = code.split('\n')
        
        # 类声明
        class_pattern = re.compile(r'(?:class|struct)\s+(\w+)')
        for line_num, line in enumerate(lines, 1):
            match = class_pattern.search(line)
            if match:
                entities.append(CodeEntity(
                    entity_type="class",
                    name=match.group(1),
                    line_start=line_num,
                    line_end=line_num,
                    code=line.strip(),
                    language=Language.CPP,
                    documentation=""
                ))
        
        # 函数声明
        func_pattern = re.compile(r'(?:\w+(?:\s*<.*?>)?\s+)+(\w+)\s*\([^)]*\)\s*(?:const)?\s*{?')
        
        for line_num, line in enumerate(lines, 1):
            if '(' in line and ')' in line and not line.strip().startswith('//'):
                match = func_pattern.search(line)
                if match:
                    name = match.group(1)
                    if len(name) > 1 and not any(c in name for c in ['<', '>', ':', '#']):
                        existing = [e for e in entities if e.name == name]
                        if not existing and name not in ['if', 'for', 'while', 'do', 'switch', 'return']:
                            entities.append(CodeEntity(
                                entity_type="function",
                                name=name,
                                line_start=line_num,
                                line_end=line_num,
                                code=line.strip(),
                                language=Language.CPP,
                                documentation=""
                            ))
        
        return entities
    
    def extract_imports(self, code: str) -> List[str]:
        imports = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('#include'):
                imports.append(f"Include at line {line_num}")
        return imports


class GoParser(BaseParser):
    """Go 代码解析器"""
    
    def __init__(self):
        self.language = Language.GO
    
    def parse(self, code: str, file_path: str = "") -> CodeModule:
        entities = self.extract_entities(code)
        imports = self.extract_imports(code)
        
        return CodeModule(
            file_path=file_path,
            language=self.language,
            entities=entities,
            imports=imports
        )
    
    def extract_entities(self, code: str) -> List[CodeEntity]:
        entities = []
        lines = code.split('\n')
        
        # 结构体声明
        struct_pattern = re.compile(r'type\s+(\w+)\s+struct')
        for line_num, line in enumerate(lines, 1):
            match = struct_pattern.search(line)
            if match:
                entities.append(CodeEntity(
                    entity_type="class",
                    name=match.group(1),
                    line_start=line_num,
                    line_end=line_num,
                    code=line.strip(),
                    language=Language.GO,
                    documentation=""
                ))
        
        # 接口声明
        interface_pattern = re.compile(r'type\s+(\w+)\s+interface')
        for line_num, line in enumerate(lines, 1):
            match = interface_pattern.search(line)
            if match:
                entities.append(CodeEntity(
                    entity_type="interface",
                    name=match.group(1),
                    line_start=line_num,
                    line_end=line_num,
                    code=line.strip(),
                    language=Language.GO,
                    documentation=""
                ))
        
        # 函数声明
        func_pattern = re.compile(r'func\s+(?:\(\s*\w+\s+\*?\w+\s*\)\s+)?(\w+)\s*\(')
        for line_num, line in enumerate(lines, 1):
            match = func_pattern.search(line)
            if match:
                name = match.group(1)
                existing = [e for e in entities if e.name == name]
                if not existing:
                    entities.append(CodeEntity(
                        entity_type="function",
                        name=name,
                        line_start=line_num,
                        line_end=line_num,
                        code=line.strip(),
                        language=Language.GO,
                        documentation=""
                    ))
        
        return entities
    
    def extract_imports(self, code: str) -> List[str]:
        imports = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('import'):
                imports.append(f"Import at line {line_num}")
        return imports


class ParserRegistry:
    """解析器注册表和工厂"""
    
    _parsers: Dict[Language, BaseParser] = {}
    
    @classmethod
    def register_parser(cls, language: Language, parser: BaseParser):
        """注册解析器"""
        cls._parsers[language] = parser
    
    @classmethod
    def get_parser(cls, language: Language) -> Optional[BaseParser]:
        """获取语言解析器"""
        if language not in cls._parsers:
            if language == Language.PYTHON:
                cls.register_parser(language, PythonParser())
            elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
                cls.register_parser(language, JavaScriptParser())
            elif language == Language.JAVA:
                cls.register_parser(language, JavaParser())
            elif language == Language.CPP:
                cls.register_parser(language, CppParser())
            elif language == Language.GO:
                cls.register_parser(language, GoParser())
        
        return cls._parsers.get(language)
    
    @classmethod
    def get_parser_for_file(cls, file_path: str) -> Optional[BaseParser]:
        """根据文件扩展名获取解析器"""
        ext = file_path.split('.')[-1].lower()
        if ext in ['py']:
            return cls.get_parser(Language.PYTHON)
        elif ext in ['js', 'jsx']:
            return cls.get_parser(Language.JAVASCRIPT)
        elif ext in ['ts', 'tsx']:
            return cls.get_parser(Language.TYPESCRIPT)
        elif ext in ['java']:
            return cls.get_parser(Language.JAVA)
        elif ext in ['cpp', 'cc', 'cxx', 'hpp', 'hxx', 'h']:
            return cls.get_parser(Language.CPP)
        elif ext in ['go']:
            return cls.get_parser(Language.GO)
        return None


# 初始化默认解析器
ParserRegistry.register_parser(Language.PYTHON, PythonParser())
ParserRegistry.register_parser(Language.JAVASCRIPT, JavaScriptParser())
ParserRegistry.register_parser(Language.TYPESCRIPT, JavaScriptParser())
ParserRegistry.register_parser(Language.JAVA, JavaParser())
ParserRegistry.register_parser(Language.CPP, CppParser())
ParserRegistry.register_parser(Language.GO, GoParser())


def parse_code(code: str, language: Optional[Language] = None, 
              file_path: str = "") -> Optional[CodeModule]:
    """解析代码统一入口"""
    if language is None and file_path:
        parser = ParserRegistry.get_parser_for_file(file_path)
    else:
        parser = ParserRegistry.get_parser(language or Language.PYTHON)
    
    if parser:
        return parser.parse(code, file_path)
    return None

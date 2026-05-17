"""
Code RAG v23.0 - AI 辅助代码库迁移器
自动将代码从一种语言迁移到另一种
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class MigrationRule:
    """迁移规则"""
    source_pattern: str
    target_pattern: str
    source_lang: str
    target_lang: str
    description: str = ""
    confidence: float = 0.8


@dataclass
class MigrationResult:
    """迁移结果"""
    source_code: str
    target_code: str
    source_lang: str
    target_lang: str
    rules_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    migration_percentage: float = 0.0


@dataclass
class MappingEntry:
    """映射条目"""
    source: str
    target: str
    description: str = ""


class LanguageMapper:
    """语言映射器"""
    
    def __init__(self):
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[Tuple[str, str], List[MappingEntry]]:
        """加载语言映射"""
        return {
            ("python", "javascript"): [
                MappingEntry("def ", "function ", "函数定义"),
                MappingEntry("self.", "this.", "实例引用"),
                MappingEntry("None", "null", "空值"),
                MappingEntry("True", "true", "布尔真"),
                MappingEntry("False", "false", "布尔假"),
                MappingEntry("print(", "console.log(", "打印语句"),
                MappingEntry("elif ", "else if ", "条件语句"),
                MappingEntry("def __init__(self,", "constructor(", "构造函数"),
            ],
            ("javascript", "python"): [
                MappingEntry("function ", "def ", "函数定义"),
                MappingEntry("this.", "self.", "实例引用"),
                MappingEntry("null", "None", "空值"),
                MappingEntry("true", "True", "布尔真"),
                MappingEntry("false", "False", "布尔假"),
                MappingEntry("console.log(", "print(", "打印语句"),
                MappingEntry("else if ", "elif ", "条件语句"),
            ],
            ("python", "java"): [
                MappingEntry("def ", "public void ", "方法定义"),
                MappingEntry("self.", "this.", "实例引用"),
                MappingEntry("None", "null", "空值"),
                MappingEntry("True", "true", "布尔真"),
                MappingEntry("False", "false", "布尔假"),
                MappingEntry("print(", "System.out.println(", "打印语句"),
                MappingEntry("list", "ArrayList", "列表类型"),
                MappingEntry("dict", "HashMap", "字典类型"),
            ],
            ("java", "python"): [
                MappingEntry("public void ", "def ", "方法定义"),
                MappingEntry("this.", "self.", "实例引用"),
                MappingEntry("null", "None", "空值"),
                MappingEntry("System.out.println(", "print(", "打印语句"),
                MappingEntry("ArrayList", "list", "列表类型"),
                MappingEntry("HashMap", "dict", "字典类型"),
            ],
        }
    
    def get_mappings(self, source_lang: str, target_lang: str) -> List[MappingEntry]:
        """获取映射"""
        key = (source_lang, target_lang)
        return self.mappings.get(key, [])


class SyntaxTransformer:
    """语法转换器"""
    
    def __init__(self):
        self.transformers = {
            ("python", "javascript"): self._py_to_js,
            ("javascript", "python"): self._js_to_py,
            ("python", "java"): self._py_to_java,
            ("java", "python"): self._java_to_py,
        }
    
    def transform(self, code: str, source_lang: str, 
                  target_lang: str) -> str:
        """转换语法"""
        key = (source_lang, target_lang)
        
        if key in self.transformers:
            return self.transformers[key](code)
        
        return code
    
    def _py_to_js(self, code: str) -> str:
        """Python 转 JavaScript"""
        result = code
        
        result = re.sub(r'def (\w+)\(([^)]*)\):', r'function \1(\2) {', result)
        
        result = re.sub(r'(\s+)return ([^;\n]+)', r'\1return \2;', result)
        
        indent_changes = result.count('    ') - result.count('    ')
        result = re.sub(r'    ', '\t', result)
        
        return result
    
    def _js_to_py(self, code: str) -> str:
        """JavaScript 转 Python"""
        result = code
        
        result = re.sub(r'function (\w+)\(([^)]*)\)\s*\{', r'def \1(\2):', result)
        
        result = re.sub(r'\t', '    ', result)
        
        result = re.sub(r'(\w+)\.push\(([^)]+)\)', r'\1.append(\2)', result)
        
        return result
    
    def _py_to_java(self, code: str) -> str:
        """Python 转 Java"""
        result = code
        
        result = re.sub(r'def (\w+)\(([^)]*)\):', r'public void \1(\2) {', result)
        
        result = re.sub(r'print\(([^)]+)\)', r'System.out.println(\1);', result)
        
        result = re.sub(r'    ', '        ', result)
        
        return result
    
    def _java_to_py(self, code: str) -> str:
        """Java 转 Python"""
        result = code
        
        result = re.sub(r'public void (\w+)\(([^)]*)\)\s*\{', r'def \1(\2):', result)
        
        result = re.sub(r'System\.out\.println\(([^)]+)\);', r'print(\1)', result)
        
        result = re.sub(r'        ', '    ', result)
        
        return result


class DependencyMapper:
    """依赖映射器"""
    
    def __init__(self):
        self.dependency_mappings = {
            ("python", "javascript"): {
                "flask": "express",
                "django": "express",
                "requests": "axios",
                "sqlalchemy": "mongoose",
            },
            ("javascript", "python"): {
                "express": "flask",
                "axios": "requests",
                "mongoose": "sqlalchemy",
            },
            ("python", "java"): {
                "flask": "Spring Boot",
                "django": "Spring Boot",
                "requests": "RestTemplate",
                "sqlalchemy": "JPA/Hibernate",
            },
            ("java", "python"): {
                "Spring Boot": "Flask/Django",
                "RestTemplate": "requests",
                "JPA/Hibernate": "SQLAlchemy",
            },
        }
    
    def map_dependency(self, dependency: str, source_lang: str, 
                      target_lang: str) -> Optional[str]:
        """映射依赖"""
        key = (source_lang, target_lang)
        
        if key in self.dependency_mappings:
            return self.dependency_mappings[key].get(dependency.lower())
        
        return None


class CodeMigrator:
    """代码迁移器"""
    
    def __init__(self):
        self.language_mapper = LanguageMapper()
        self.syntax_transformer = SyntaxTransformer()
        self.dependency_mapper = DependencyMapper()
        self.migration_history: List[MigrationResult] = []
    
    def migrate(self, code: str, source_lang: str, 
                target_lang: str) -> MigrationResult:
        """迁移代码"""
        result = MigrationResult(
            source_code=code,
            target_code="",
            source_lang=source_lang,
            target_lang=target_lang
        )
        
        migrated = code
        
        mappings = self.language_mapper.get_mappings(source_lang, target_lang)
        for mapping in mappings:
            if mapping.source in migrated:
                migrated = migrated.replace(mapping.source, mapping.target)
                result.rules_applied.append(mapping.description)
        
        migrated = self.syntax_transformer.transform(
            migrated, source_lang, target_lang
        )
        
        result.target_code = migrated
        
        original_lines = len(code.split('\n'))
        migrated_lines = len(migrated.split('\n'))
        
        if original_lines > 0:
            result.migration_percentage = min(100.0, (migrated_lines / original_lines) * 100)
        
        self.migration_history.append(result)
        
        return result
    
    def migrate_project(self, files: Dict[str, str], 
                       source_lang: str, target_lang: str) -> Dict[str, MigrationResult]:
        """迁移整个项目"""
        results = {}
        
        for file_path, content in files.items():
            result = self.migrate(content, source_lang, target_lang)
            results[file_path] = result
        
        return results
    
    def get_migration_report(self) -> Dict:
        """获取迁移报告"""
        if not self.migration_history:
            return {"status": "no_migrations"}
        
        total = len(self.migration_history)
        avg_percentage = sum(
            r.migration_percentage for r in self.migration_history
        ) / total
        
        return {
            "total_migrations": total,
            "average_migration_percentage": avg_percentage,
            "source_languages": list(set(r.source_lang for r in self.migration_history)),
            "target_languages": list(set(r.target_lang for r in self.migration_history)),
        }


def create_code_migrator() -> CodeMigrator:
    """创建代码迁移器"""
    return CodeMigrator()

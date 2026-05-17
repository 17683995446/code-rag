"""
Code RAG v23.0 - 自然语言架构设计器
将自然语言描述转换为代码结构
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ArchitectureComponent:
    """架构组件"""
    name: str
    component_type: str
    description: str = ""
    methods: List[str] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ArchitectureDesign:
    """架构设计"""
    name: str
    description: str
    language: str
    components: List[ArchitectureComponent] = field(default_factory=list)
    file_structure: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class NLParser:
    """自然语言解析器"""
    
    def __init__(self):
        self.patterns = {
            "service": r"(?:service|backend|api)\s+(\w+)",
            "model": r"(?:model|entity|class|data)\s+(\w+)",
            "controller": r"(?:controller|endpoint|route)\s+(\w+)",
            "database": r"(?:database|db|storage)\s+(\w+)",
        }
    
    def parse(self, description: str) -> Dict:
        """解析自然语言描述"""
        components = []
        
        words = description.lower().split()
        
        if any(w in words for w in ['service', 'backend', 'api', 'server']):
            components.append({"type": "service", "confidence": 0.8})
        
        if any(w in words for w in ['model', 'entity', 'class', 'data']):
            components.append({"type": "model", "confidence": 0.8})
        
        if any(w in words for w in ['controller', 'endpoint', 'api']):
            components.append({"type": "controller", "confidence": 0.7})
        
        if any(w in words for w in ['database', 'db', 'storage', 'table']):
            components.append({"type": "database", "confidence": 0.9})
        
        if any(w in words for w in ['user', 'auth', 'login', 'authenticate']):
            components.append({"type": "user_service", "confidence": 0.9})
        
        if any(w in words for w in ['file', 'upload', 'storage', 'document']):
            components.append({"type": "file_service", "confidence": 0.8})
        
        return {
            "components": components,
            "keywords": words,
            "complexity": self._estimate_complexity(description)
        }
    
    def _estimate_complexity(self, description: str) -> str:
        """估算复杂度"""
        words = description.lower().split()
        
        if len(words) < 10:
            return "simple"
        elif len(words) < 30:
            return "medium"
        else:
            return "complex"


class CodeStructureGenerator:
    """代码结构生成器"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """加载代码模板"""
        return {
            "python": {
                "service": """class {name}Service:
    def __init__(self):
        self.data = []
    
    def create(self, data):
        pass
    
    def read(self, id):
        pass
    
    def update(self, id, data):
        pass
    
    def delete(self, id):
        pass
""",
                "model": """class {name}:
    def __init__(self, data):
        self.id = data.get('id')
        self.name = data.get('name')
        self.created_at = data.get('created_at')
    
    def to_dict(self):
        return self.__dict__
""",
                "controller": """from flask import Blueprint, jsonify, request

{name}_bp = Blueprint('{name}', __name__)

@{name}_bp.route('/{name}', methods=['GET'])
def get_{name}s():
    return jsonify([])

@{name}_bp.route('/{name}', methods=['POST'])
def create_{name}():
    data = request.json
    return jsonify(data), 201
""",
                "api": """from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'API is running'

if __name__ == '__main__':
    app.run(debug=True)
"""
            },
            "javascript": {
                "service": """class {name}Service {{
    constructor() {{
        this.data = [];
    }}
    
    create(data) {{
        return data;
    }}
    
    read(id) {{
        return this.data.find(item => item.id === id);
    }}
}}
""",
                "model": """class {name} {{
    constructor(data) {{
        this.id = data.id;
        this.name = data.name;
    }}
    
    toJSON() {{
        return JSON.stringify(this);
    }}
}}
""",
            }
        }
    
    def generate_component(self, component_type: str, name: str, 
                          language: str = "python") -> str:
        """生成组件代码"""
        templates = self.templates.get(language, self.templates["python"])
        
        if component_type in templates:
            return templates[component_type].format(name=name.title())
        else:
            return f"# {name} component"
    
    def generate_file_structure(self, components: List[Dict], 
                               language: str = "python") -> List[str]:
        """生成文件结构"""
        files = []
        
        for comp in components:
            comp_type = comp.get("type", "service")
            name = comp_type.replace("_", "_")
            
            if language == "python":
                if comp_type in ["service", "model"]:
                    files.append(f"src/{name}.py")
                elif comp_type == "controller":
                    files.append(f"src/controllers/{name}_controller.py")
            elif language in ["javascript", "typescript"]:
                files.append(f"src/{name}.js")
        
        return files


class DependencyAnalyzer:
    """依赖分析器"""
    
    def __init__(self):
        self.common_dependencies = {
            "python": ["flask", "django", "fastapi", "sqlalchemy", "requests"],
            "javascript": ["express", "react", "mongoose", "axios"],
            "java": ["spring-boot", "hibernate", "jpa"],
        }
    
    def analyze(self, components: List[Dict], 
                language: str = "python") -> List[str]:
        """分析依赖"""
        dependencies = []
        
        for comp in components:
            comp_type = comp.get("type", "")
            
            if comp_type in ["service", "controller", "api"]:
                if language == "python":
                    dependencies.append("flask")
                elif language == "javascript":
                    dependencies.append("express")
            
            if comp_type in ["model", "database"]:
                if language == "python":
                    dependencies.append("sqlalchemy")
                elif language == "javascript":
                    dependencies.append("mongoose")
        
        return list(set(dependencies))


class ArchitectureDesigner:
    """架构设计器"""
    
    def __init__(self):
        self.parser = NLParser()
        self.generator = CodeStructureGenerator()
        self.dependency_analyzer = DependencyAnalyzer()
    
    def design(self, description: str, language: str = "python") -> ArchitectureDesign:
        """从描述生成架构设计"""
        parsed = self.parser.parse(description)
        
        components = []
        for comp_data in parsed["components"]:
            comp_name = comp_data["type"]
            
            component = ArchitectureComponent(
                name=comp_name.title(),
                component_type=comp_data["type"],
                description=f"Auto-generated {comp_data['type']} component",
                methods=["create", "read", "update", "delete"],
                properties=["id", "name", "created_at"],
                dependencies=[]
            )
            components.append(component)
        
        file_structure = self.generator.generate_file_structure(
            parsed["components"], 
            language
        )
        
        dependencies = self.dependency_analyzer.analyze(
            parsed["components"], 
            language
        )
        
        return ArchitectureDesign(
            name="Generated Architecture",
            description=description,
            language=language,
            components=components,
            file_structure=file_structure,
            dependencies=dependencies
        )
    
    def generate_code(self, design: ArchitectureDesign) -> Dict[str, str]:
        """为设计生成代码"""
        generated_code = {}
        
        for component in design.components:
            code = self.generator.generate_component(
                component.component_type,
                component.name,
                design.language
            )
            generated_code[component.name] = code
        
        return generated_code
    
    def generate_full_project(self, design: ArchitectureDesign) -> Dict:
        """生成完整项目结构"""
        project = {
            "files": {},
            "structure": [],
            "dependencies": {}
        }
        
        generated_code = self.generate_code(design)
        
        for name, code in generated_code.items():
            file_name = f"src/{name.lower()}.py"
            project["files"][file_name] = code
            project["structure"].append(file_name)
        
        if design.dependencies:
            if design.language == "python":
                req_content = "\n".join(design.dependencies)
                project["files"]["requirements.txt"] = req_content
            elif design.language == "javascript":
                deps = {d: "*" for d in design.dependencies}
                import json
                project["files"]["package.json"] = json.dumps({
                    "dependencies": deps
                }, indent=2)
        
        return project


def create_architecture_designer() -> ArchitectureDesigner:
    """创建架构设计器"""
    return ArchitectureDesigner()

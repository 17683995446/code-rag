#!/usr/bin/env python3
"""
批量修复导入问题
"""
import os
import sys
from pathlib import Path

# 导入替换映射
import_replacements = [
    (r"from \.logger import get_logger", '''try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)'''),
    
    (r"from \.settings import get_settings", '''try:
    from ..base_layer import get_settings
except ImportError:
    class SimpleSettings:
        pass
    def get_settings():
        return SimpleSettings()'''),
    
    (r"from src\.core\.logger import get_logger", '''try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)'''),
    
    (r"from src\.core\.config import get_settings", '''try:
    from ..base_layer import get_settings
except ImportError:
    class SimpleSettings:
        pass
    def get_settings():
        return SimpleSettings()'''),
    
    (r"from src\.core import logger", '''try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)
logger = get_logger(__name__)'''),
]

# 需要处理的目录
layers = [
    "processing_layer",
    "rag_engine",
    "service_layer",
    "middleware_layer",
    "observability_layer",
    "api_layer",
]

def fix_imports_in_file(file_path: Path):
    """修复单个文件的导入问题"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        for old_pattern, new_code in import_replacements:
            import re
            content = re.sub(old_pattern, new_code, content)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"✅ 已修复: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"❌ 修复失败 {file_path}: {e}")
        return False

def main():
    project_root = Path(__file__).parent
    src_dir = project_root / "src" / "code_rag"
    
    print("=" * 80)
    print("  批量修复导入问题")
    print("=" * 80)
    
    total_fixed = 0
    
    for layer in layers:
        layer_dir = src_dir / layer
        if not layer_dir.exists():
            continue
        
        print(f"\n处理 {layer} ...")
        
        for py_file in layer_dir.glob("*.py"):
            if fix_imports_in_file(py_file):
                total_fixed += 1
    
    print(f"\n{'=' * 80}")
    print(f"  修复完成，共修复 {total_fixed} 个文件")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()

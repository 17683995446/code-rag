LANGUAGE_MODES = {
    'python': {
        'name': 'Python',
        'extensions': ['.py', '.pyw', '.pyi'],
        'comment': '#',
        'multiline_comment': ['"""', "'''"],
        'symbol_patterns': {
            'class': r'^class\s+(\w+)',
            'function': r'^def\s+(\w+)\s*\(',
            'method': r'^    def\s+(\w+)\s*\(',
            'decorator': r'@(\w+)',
        },
        'import_pattern': r'^import\s+(.+)',
        'from_import_pattern': r'^from\s+([\w.]+)\s+import',
    },
    'javascript': {
        'name': 'JavaScript',
        'extensions': ['.js', '.mjs', '.cjs', '.jsx'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'function': r'function\s+(\w+)\s*\(',
            'method': r'    (\w+)\s*\([^)]*\)\s*\{',
            'arrow': r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
        },
        'import_pattern': r"import\s+.+\s+from\s+['\"]([^'\"]+)['\"]",
    },
    'typescript': {
        'name': 'TypeScript',
        'extensions': ['.ts', '.tsx', '.mts', '.cts'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'function': r'function\s+(\w+)\s*\(',
            'method': r'    (\w+)\s*\([^)]*\)\s*[:{]',
        },
        'import_pattern': r"import\s+.+\s+from\s+['\"]([^'\"]+)['\"]",
    },
    'java': {
        'name': 'Java',
        'extensions': ['.java'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'method': r'    \w+\s+(\w+)\s*\(',
        },
        'import_pattern': r'^import\s+([\w.]+);',
    },
    'go': {
        'name': 'Go',
        'extensions': ['.go'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'function': r'func\s+(\w+)\s*\(',
            'method': r'func\s+\([^)]+\)\s+(\w+)\s*\(',
            'type': r'type\s+(\w+)\s+',
        },
        'import_pattern': r'^import\s+',
    },
    'rust': {
        'name': 'Rust',
        'extensions': ['.rs'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'struct': r'struct\s+(\w+)',
            'enum': r'enum\s+(\w+)',
            'function': r'fn\s+(\w+)\s*\(',
            'impl': r'impl\s+(?:<[^>]+>\s*)?(\w+)',
        },
        'import_pattern': r'^use\s+',
    },
    'c': {
        'name': 'C',
        'extensions': ['.c', '.h'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'struct': r'struct\s+(\w+)',
            'function': r'\w+\s+(\w+)\s*\([^)]*\)\s*\{',
            'typedef': r'typedef\s+[\w\s]+\s+(\w+);',
        },
        'include_pattern': r'#include\s*[<"]([^>"]+)[>"]',
    },
    'cpp': {
        'name': 'C++',
        'extensions': ['.cpp', '.hpp', '.cc', '.hh', '.cxx', '.hxx'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'struct': r'struct\s+(\w+)',
            'function': r'\w+\s+(\w+)\s*\([^)]*\)(?:\s*const)?\s*\{',
        },
        'include_pattern': r'#include\s*[<"]([^>"]+)[>"]',
    },
    'csharp': {
        'name': 'C#',
        'extensions': ['.cs'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'method': r'    \w+\s+(\w+)\s*\(',
        },
        'import_pattern': r'^using\s+([\w.]+);',
    },
    'ruby': {
        'name': 'Ruby',
        'extensions': ['.rb'],
        'comment': '#',
        'multiline_comment': ['=begin', '=end'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'module': r'module\s+(\w+)',
            'method': r'def\s+(\w+)',
        },
        'import_pattern': r'^require[_relative]?\s+',
    },
    'php': {
        'name': 'PHP',
        'extensions': ['.php'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'interface': r'interface\s+(\w+)',
            'function': r'function\s+(\w+)\s*\(',
            'method': r'    function\s+(\w+)\s*\(',
        },
        'import_pattern': r'^(use|require)',
    },
    'swift': {
        'name': 'Swift',
        'extensions': ['.swift'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'struct': r'struct\s+(\w+)',
            'func': r'func\s+(\w+)\s*\(',
        },
        'import_pattern': r'^import\s+(\w+)',
    },
    'kotlin': {
        'name': 'Kotlin',
        'extensions': ['.kt', '.kts'],
        'comment': '//',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'class': r'class\s+(\w+)',
            'fun': r'fun\s+(\w+)\s*\(',
        },
        'import_pattern': r'^import\s+(.+)',
    },
    'sql': {
        'name': 'SQL',
        'extensions': ['.sql'],
        'comment': '--',
        'multiline_comment': ['/*', '*/'],
        'symbol_patterns': {
            'table': r'CREATE\s+TABLE\s+(\w+)',
            'view': r'CREATE\s+VIEW\s+(\w+)',
            'procedure': r'CREATE\s+PROCEDURE\s+(\w+)',
            'function': r'CREATE\s+FUNCTION\s+(\w+)',
        },
    },
    'yaml': {
        'name': 'YAML',
        'extensions': ['.yaml', '.yml'],
        'comment': '#',
        'symbol_patterns': {},
    },
    'json': {
        'name': 'JSON',
        'extensions': ['.json', '.jsonc'],
        'symbol_patterns': {},
    },
}


def get_language_from_extension(ext: str) -> str:
    ext = ext.lower()
    for lang, mode in LANGUAGE_MODES.items():
        if ext in mode['extensions']:
            return lang
    return None


def get_language_mode(language: str) -> dict:
    return LANGUAGE_MODES.get(language.lower())

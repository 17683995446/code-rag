import os
import re
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import threading


class PromptStrategy(Enum):
    CODE_SEARCH = "code_search"
    CODE_EXPLANATION = "code_explanation"
    BUG_ANALYSIS = "bug_analysis"
    REFACTORING = "refactoring"
    IMPLEMENTATION = "implementation"
    CODE_COMPLETION = "code_completion"
    DOCUMENTATION = "documentation"
    SECURITY_SCAN = "security_scan"
    TEST_GENERATION = "test_generation"
    ARCHITECTURE = "architecture"


@dataclass
class PromptTemplate:
    name: str
    strategy: PromptStrategy
    system_prompt: str
    user_template: str
    few_shot_examples: List[Dict] = field(default_factory=list)
    max_context_length: int = 4000
    temperature: float = 0.7
    metadata: Dict = field(default_factory=dict)


@dataclass
class LLMRequest:
    prompt: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    stop: List[str] = field(default_factory=list)
    stream: bool = False


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict = field(default_factory=dict)
    latency_ms: float = 0
    finish_reason: str = "stop"


class AdvancedPromptBuilder:
    def __init__(self):
        self.templates: Dict[PromptStrategy, PromptTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        self.templates[PromptStrategy.CODE_SEARCH] = PromptTemplate(
            name="Code Search",
            strategy=PromptStrategy.CODE_SEARCH,
            system_prompt="""You are an expert code search assistant. Your task is to find the most relevant code snippets based on the user's query.

Guidelines:
- Focus on exact matches first, then semantic similarity
- Consider function signatures, variable names, and comments
- Return results with file paths and line numbers
- Prioritize code that directly answers the query""",
            user_template="""Based on the following code context from {file_count} files:

{context}

Question: {question}

Instructions:
- Find the most relevant code sections
- Include file paths and line numbers
- Explain how each result relates to the question

Answer:""",
            max_context_length=4000
        )

        self.templates[PromptStrategy.CODE_EXPLANATION] = PromptTemplate(
            name="Code Explanation",
            strategy=PromptStrategy.CODE_EXPLANATION,
            system_prompt="""You are an expert code analyst. Your task is to explain code in a clear, educational manner.

Guidelines:
- Break down complex logic into understandable parts
- Explain the purpose of each function/class
- Highlight important patterns and conventions
- Provide examples when helpful""",
            user_template="""Explain the following code in detail:

```{language}
{code}
```

Question: {question}

Please provide:
1. Overview of what the code does
2. Key components and their purposes
3. Any notable patterns or best practices
4. Potential improvements or concerns

Explanation:""",
            few_shot_examples=[
                {
                    "input": "Explain this function: def add(a, b): return a + b",
                    "output": "This is a simple addition function that takes two parameters and returns their sum."
                }
            ],
            max_context_length=3000
        )

        self.templates[PromptStrategy.BUG_ANALYSIS] = PromptTemplate(
            name="Bug Analysis",
            strategy=PromptStrategy.BUG_ANALYSIS,
            system_prompt="""You are an expert bug hunter and code reviewer. Your task is to identify and analyze bugs in code.

Guidelines:
- Look for common bug patterns (null pointer, off-by-one, race conditions)
- Check for error handling issues
- Consider edge cases and boundary conditions
- Provide specific line numbers and suggestions""",
            user_template="""Analyze the following code for bugs and issues:

```{language}
{code}
```

Error message (if any): {error_message}

Please identify:
1. Potential bugs with line numbers
2. Error handling issues
3. Edge cases not handled
4. Suggested fixes for each issue

Analysis:""",
            temperature=0.3,
            max_context_length=3500
        )

        self.templates[PromptStrategy.REFACTORING] = PromptTemplate(
            name="Refactoring",
            strategy=PromptStrategy.REFACTORING,
            system_prompt="""You are an expert software architect. Your task is to suggest code refactoring improvements.

Guidelines:
- Focus on code readability and maintainability
- Suggest patterns that improve design
- Consider performance implications
- Provide before/after comparisons""",
            user_template="""Suggest improvements for the following code:

```{language}
{code}
```

Current concerns: {concerns}

Please provide:
1. Specific refactoring suggestions
2. Improved code snippets
3. Design patterns that could help
4. Trade-offs of each change

Suggestions:""",
            max_context_length=4000
        )

        self.templates[PromptStrategy.IMPLEMENTATION] = PromptTemplate(
            name="Implementation",
            strategy=PromptStrategy.IMPLEMENTATION,
            system_prompt="""You are an expert programmer. Your task is to implement solutions based on requirements.

Guidelines:
- Write clean, well-documented code
- Follow language best practices
- Include proper error handling
- Consider edge cases""",
            user_template="""Implement a solution for the following requirement:

Requirement: {requirement}

Existing code context:
```{language}
{context}
```

Please provide:
1. Implementation approach
2. Complete code solution
3. Usage examples
4. Edge cases to consider

Implementation:""",
            max_context_length=4000
        )

        self.templates[PromptStrategy.TEST_GENERATION] = PromptTemplate(
            name="Test Generation",
            strategy=PromptStrategy.TEST_GENERATION,
            system_prompt="""You are an expert test engineer. Your task is to generate comprehensive test cases.

Guidelines:
- Cover happy path and edge cases
- Use appropriate testing frameworks
- Include both positive and negative tests
- Write clear test names""",
            user_template="""Generate test cases for the following code:

```{language}
{code}
```

Testing framework: {framework}

Please provide:
1. Unit tests for main functions
2. Edge case tests
3. Mock setups if needed
4. Expected outputs

Tests:""",
            max_context_length=3500
        )

    def get_template(self, strategy: PromptStrategy) -> PromptTemplate:
        return self.templates.get(strategy, self.templates[PromptStrategy.CODE_SEARCH])

    def build_prompt(
        self,
        strategy: PromptStrategy,
        context: str,
        question: str,
        **kwargs
    ) -> str:
        template = self.get_template(strategy)

        file_count = kwargs.get('file_count', 1)
        language = kwargs.get('language', 'python')
        error_message = kwargs.get('error_message', '')
        concerns = kwargs.get('concerns', '')
        requirement = kwargs.get('requirement', question)
        framework = kwargs.get('framework', 'pytest')

        user_prompt = template.user_template.format(
            context=context,
            question=question,
            file_count=file_count,
            language=language,
            error_message=error_message,
            concerns=concerns,
            requirement=requirement,
            framework=framework,
            code=context
        )

        return f"{template.system_prompt}\n\n{user_prompt}"

    def add_template(self, template: PromptTemplate):
        self.templates[template.strategy] = template


class DynamicPromptOptimizer:
    def __init__(self):
        self.history: List[Dict] = []
        self._lock = threading.Lock()

    def optimize_prompt(
        self,
        base_prompt: str,
        context: str,
        response_quality: float = None
    ) -> str:
        with self._lock:
            self.history.append({
                'prompt': base_prompt,
                'context_length': len(context),
                'quality': response_quality,
                'timestamp': time.time()
            })

        if len(self.history) < 3:
            return base_prompt

        avg_length = sum(h['context_length'] for h in self.history[-5:]) / 5
        if len(context) > avg_length * 1.5:
            base_prompt = self._condense_prompt(base_prompt)

        return base_prompt

    def _condense_prompt(self, prompt: str) -> str:
        condensing_phrases = [
            "Provide a concise summary.",
            "Focus on key points.",
            "Be brief but comprehensive."
        ]

        if condensing_phrases[0] not in prompt:
            prompt = f"{prompt}\n\n{condensing_phrases[0]}"

        return prompt


class LLMChain:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.prompt_builder = AdvancedPromptBuilder()

    def execute(
        self,
        strategy: PromptStrategy,
        context: str,
        question: str,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()

        prompt = self.prompt_builder.build_prompt(
            strategy=strategy,
            context=context,
            question=question,
            **kwargs
        )

        template = self.prompt_builder.get_template(strategy)

        messages = [
            {"role": "system", "content": template.system_prompt},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_client.chat(messages)

        latency = (time.time() - start_time) * 1000

        return LLMResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
            latency_ms=latency,
            finish_reason=response.finish_reason
        )

    def stream_execute(
        self,
        strategy: PromptStrategy,
        context: str,
        question: str,
        **kwargs
    ) -> Generator[str, None, None]:
        prompt = self.prompt_builder.build_prompt(
            strategy=strategy,
            context=context,
            question=question,
            **kwargs
        )

        template = self.prompt_builder.get_template(strategy)

        messages = [
            {"role": "system", "content": template.system_prompt},
            {"role": "user", "content": prompt}
        ]

        for chunk in self.llm_client.chat_stream(messages):
            yield chunk


class PromptCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, str] = {}
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self.cache:
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None

    def put(self, key: str, prompt: str):
        with self._lock:
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = prompt

    def stats(self) -> Dict:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0
            return {
                'size': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate
            }


class ResponseValidator:
    def __init__(self):
        self.validation_rules = []

    def add_rule(self, name: str, validator: Callable[[str], bool]):
        self.validation_rules.append({'name': name, 'validator': validator})

    def validate(self, response: str) -> Dict:
        results = {
            'valid': True,
            'issues': []
        }

        for rule in self.validation_rules:
            try:
                if not rule['validator'](response):
                    results['valid'] = False
                    results['issues'].append(rule['name'])
            except Exception:
                pass

        return results


class CodeSpecificValidator:
    @staticmethod
    def has_code_blocks(text: str) -> bool:
        return '```' in text or '`' in text

    @staticmethod
    def has_file_references(text: str) -> bool:
        return bool(re.search(r'\.(py|js|ts|java|cpp|go|rs)\b', text))

    @staticmethod
    def has_line_numbers(text: str) -> bool:
        return bool(re.search(r'line\s+\d+', text, re.IGNORECASE))

    @staticmethod
    def is_too_short(text: str, min_length: int = 50) -> bool:
        return len(text) < min_length


class ResponseFormatter:
    @staticmethod
    def format_markdown(text: str) -> str:
        lines = text.split('\n')
        formatted = []

        in_code_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block

            if not in_code_block:
                if line.strip().startswith('- '):
                    line = f"- {line.strip()[2:]}"
                elif re.match(r'^\d+\.', line.strip()):
                    line = line

            formatted.append(line)

        return '\n'.join(formatted)

    @staticmethod
    def extract_code_blocks(text: str) -> List[str]:
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        return [code for _, code in matches]

    @staticmethod
    def extract_sources(text: str) -> List[str]:
        pattern = r'([\w/\\]+\.(?:py|js|ts|java|cpp|go|rs))'
        return list(set(re.findall(pattern, text)))


class FewShotExampleSelector:
    def __init__(self):
        self.examples: Dict[PromptStrategy, List[Dict]] = {}

    def add_example(self, strategy: PromptStrategy, input_text: str, output_text: str):
        if strategy not in self.examples:
            self.examples[strategy] = []
        self.examples[strategy].append({
            'input': input_text,
            'output': output_text
        })

    def get_examples(self, strategy: PromptStrategy, limit: int = 3) -> List[Dict]:
        return self.examples.get(strategy, [])[:limit]

    def build_few_shot_prompt(self, strategy: PromptStrategy, question: str) -> str:
        examples = self.get_examples(strategy)
        if not examples:
            return question

        few_shot = "\n\nExamples:\n"
        for ex in examples:
            few_shot += f"\nInput: {ex['input']}\nOutput: {ex['output']}\n"

        return f"{question}\n{few_shot}"


class LLMOptimizer:
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.chain = LLMChain(llm_client)
        self.prompt_cache = PromptCache()
        self.validator = ResponseValidator()
        self.example_selector = FewShotExampleSelector()

        self._setup_validators()

    def _setup_validators(self):
        self.validator.add_rule(
            "has_content",
            lambda x: len(x.strip()) > 0
        )
        self.validator.add_rule(
            "not_too_short",
            lambda x: not CodeSpecificValidator.is_too_short(x, 50)
        )

    def execute(
        self,
        strategy: PromptStrategy,
        context: str,
        question: str,
        use_cache: bool = True,
        validate: bool = True,
        **kwargs
    ) -> Dict:
        cache_key = f"{strategy.value}:{hash(context)}:{hash(question)}"

        if use_cache:
            cached = self.prompt_cache.get(cache_key)
            if cached:
                return {'prompt': cached, 'cached': True}

        response = self.chain.execute(
            strategy=strategy,
            context=context,
            question=question,
            **kwargs
        )

        if validate:
            validation = self.validator.validate(response.content)
            if not validation['valid']:
                response.content = f"[Note: Some validations failed: {', '.join(validation['issues'])}]\n\n{response.content}"

        prompt = self.chain.prompt_builder.build_prompt(
            strategy=strategy,
            context=context,
            question=question,
            **kwargs
        )

        if use_cache:
            self.prompt_cache.put(cache_key, prompt)

        return {
            'content': response.content,
            'model': response.model,
            'usage': response.usage,
            'latency_ms': response.latency_ms,
            'prompt': prompt,
            'cached': False
        }

    def stream_execute(
        self,
        strategy: PromptStrategy,
        context: str,
        question: str,
        **kwargs
    ) -> Generator[str, None, None]:
        for chunk in self.chain.stream_execute(
            strategy=strategy,
            context=context,
            question=question,
            **kwargs
        ):
            yield chunk


class CostEstimator:
    def __init__(self):
        self.rates = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "claude-3": {"input": 0.015, "output": 0.075},
        }

    def estimate(self, model: str, input_tokens: int, output_tokens: int) -> Dict:
        rates = self.rates.get(model, {"input": 0.001, "output": 0.002})

        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }

    def estimate_from_text(self, model: str, input_text: str, output_text: str) -> Dict:
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4

        return self.estimate(model, input_tokens, output_tokens)

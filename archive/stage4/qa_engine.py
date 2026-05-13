import time
from typing import List, Dict, Optional, Any, Iterator

from stage4.types import (
    LLMConfig, LLMProvider, Message, ChatRequest, ChatResponse,
    CodeContext, QAResult
)
from stage4.llm_client import create_llm_client, LLMClient
from stage4.prompts import PromptBuilder, DEFAULT_TEMPLATES


class CodeQAEngine:
    def __init__(
        self,
        llm_config: LLMConfig = None,
        prompt_builder: PromptBuilder = None
    ):
        self.llm_config = llm_config or LLMConfig(provider=LLMProvider.MOCK)
        self.llm_client = create_llm_client(self.llm_config)
        self.prompt_builder = prompt_builder or PromptBuilder(DEFAULT_TEMPLATES)
        self.default_template = "code_search"

    def ask(
        self,
        question: str,
        code_chunks: List[Dict],
        template_name: str = None,
        stream: bool = False
    ) -> QAResult:
        start_time = time.time()

        template = template_name or self.default_template

        messages, context = self.prompt_builder.build_messages(
            template_name=template,
            code_chunks=code_chunks,
            question=question
        )

        try:
            if stream:
                response_text = self._stream_response(messages)
            else:
                response = self.llm_client.chat(messages)
                response_text = response.content

            latency = (time.time() - start_time) * 1000

            return QAResult(
                question=question,
                answer=response_text,
                sources=self._format_sources(code_chunks),
                context_used=context[:500] + "..." if len(context) > 500 else context,
                model=self.llm_config.model,
                latency_ms=latency
            )

        except Exception as e:
            return QAResult(
                question=question,
                answer=f"Error generating response: {str(e)}",
                sources=[],
                latency_ms=(time.time() - start_time) * 1000
            )

    def ask_stream(
        self,
        question: str,
        code_chunks: List[Dict],
        template_name: str = None
    ) -> Iterator[tuple[str, QAResult]]:
        template = template_name or self.default_template

        messages, context = self.prompt_builder.build_messages(
            template_name=template,
            code_chunks=code_chunks,
            question=question
        )

        response_text = ""
        start_time = time.time()

        try:
            for chunk in self.llm_client.chat_stream(messages):
                response_text += chunk
                yield chunk, None

            latency = (time.time() - start_time) * 1000

            result = QAResult(
                question=question,
                answer=response_text,
                sources=self._format_sources(code_chunks),
                context_used=context[:500] + "..." if len(context) > 500 else context,
                model=self.llm_config.model,
                latency_ms=latency
            )

            yield "", result

        except Exception as e:
            yield "", QAResult(
                question=question,
                answer=f"Error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000
            )

    def _stream_response(self, messages: List[Message]) -> str:
        response_text = ""
        for chunk in self.llm_client.chat_stream(messages):
            response_text += chunk
        return response_text

    def _format_sources(self, code_chunks: List[Dict]) -> List[Dict]:
        sources = []
        for chunk in code_chunks[:5]:
            sources.append({
                'file': chunk.get('file_path', 'unknown'),
                'lines': f"{chunk.get('start_line', 0)}-{chunk.get('end_line', 0)}",
                'type': chunk.get('chunk_type', 'unknown'),
                'preview': chunk.get('content', '')[:100]
            })
        return sources

    def explain_code(
        self,
        code_chunk: Dict,
        question: str = None
    ) -> QAResult:
        return self.ask(
            question=question or "Explain this code",
            code_chunks=[code_chunk],
            template_name="code_explanation"
        )

    def find_related_code(
        self,
        code_chunk: Dict,
        question: str = None
    ) -> QAResult:
        return self.ask(
            question=question or "Find related code and explain relationships",
            code_chunks=[code_chunk],
            template_name="code_search"
        )

    def suggest_fixes(
        self,
        code_chunk: Dict,
        problem_description: str
    ) -> QAResult:
        return self.ask(
            question=problem_description,
            code_chunks=[code_chunk],
            template_name="code_fix"
        )

    def generate_code(
        self,
        code_chunks: List[Dict],
        requirement: str
    ) -> QAResult:
        return self.ask(
            question=requirement,
            code_chunks=code_chunks,
            template_name="code_generation"
        )

    def review_code(
        self,
        code_chunks: List[Dict],
        focus_areas: str = None
    ) -> QAResult:
        return self.ask(
            question=focus_areas or "General code review",
            code_chunks=code_chunks,
            template_name="code_review"
        )


class RAGPipeline:
    def __init__(
        self,
        search_func: callable,
        qa_engine: CodeQAEngine = None,
        enhance_func: callable = None
    ):
        self.search_func = search_func
        self.qa_engine = qa_engine or CodeQAEngine()
        self.enhance_func = enhance_func

    def query(
        self,
        question: str,
        top_k: int = 5,
        enhance: bool = True,
        template: str = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        search_results = self.search_func(question, top_k=top_k)
        code_chunks = [r.original_result if hasattr(r, 'original_result') else r 
                       for r in search_results]

        if enhance and self.enhance_func:
            enhanced = self.enhance_func(search_results)
            code_chunks = [e.original_result for e in enhanced]

        qa_result = self.qa_engine.ask(
            question=question,
            code_chunks=code_chunks,
            template_name=template
        )

        return {
            'question': question,
            'answer': qa_result.answer,
            'sources': qa_result.sources,
            'search_results': code_chunks,
            'latency_ms': (time.time() - start_time) * 1000,
            'model': qa_result.model
        }

    def query_stream(
        self,
        question: str,
        top_k: int = 5
    ) -> Iterator[tuple[str, Dict]]:
        search_results = self.search_func(question, top_k=top_k)
        code_chunks = [r.original_result if hasattr(r, 'original_result') else r 
                       for r in search_results]

        for chunk, result in self.qa_engine.ask_stream(
            question=question,
            code_chunks=code_chunks
        ):
            if chunk:
                yield chunk, None
            else:
                yield None, {
                    'question': question,
                    'answer': result.answer,
                    'sources': result.sources,
                    'latency_ms': result.latency_ms
                }

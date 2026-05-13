from typing import Dict, List, Optional
from stage4.types import PromptTemplate, Message


DEFAULT_TEMPLATES = {
    "code_explanation": PromptTemplate(
        name="code_explanation",
        system_prompt="""You are an expert software developer explaining code. 
Provide clear, concise explanations focusing on:
1. What the code does
2. How it works
3. Key patterns and design decisions
Be technical but accessible. Use code references when explaining.""",
        user_template="""Explain the following code:

{code_context}

Question: {question}

Provide a detailed explanation with references to specific parts of the code."""
    ),

    "code_search": PromptTemplate(
        name="code_search",
        system_prompt="""You are an expert at understanding codebases. 
Based on the provided code context, answer the user's question.
Cite specific file names and line numbers when referencing code.
If you're unsure about something, say so rather than guessing.""",
        user_template="""Based on the following code from the codebase:

{code_context}

Answer this question:
{question}

If relevant, point to specific files and functions."""
    ),

    "code_fix": PromptTemplate(
        name="code_fix",
        system_prompt="""You are a code debugging expert.
Analyze the code and identify issues.
Provide specific, actionable fixes with explanations.
Consider edge cases and error handling.""",
        user_template="""Analyze this code for bugs or issues:

{code_context}

Problem description: {question}

Identify issues and provide fixes."""
    ),

    "code_generation": PromptTemplate(
        name="code_generation",
        system_prompt="""You are an expert programmer.
Generate clean, well-documented code following best practices.
Consider the existing codebase style and patterns.""",
        user_template="""Based on this code context:

{code_context}

Generate code to: {question}

Follow the existing code style and patterns."""
    ),

    "code_review": PromptTemplate(
        name="code_review",
        system_prompt="""You are a code reviewer.
Provide constructive feedback on:
1. Correctness
2. Performance
3. Security
4. Readability
5. Best practices
Be specific and actionable.""",
        user_template="""Review this code:

{code_context}

Focus areas: {focus_areas}

Provide specific suggestions for improvement."""
    ),

    "call_chain": PromptTemplate(
        name="call_chain",
        system_prompt="""You are a code analyst specializing in understanding code flow.
Trace through the code and explain the execution path.""",
        user_template="""Analyze the call chain for this code:

{code_context}

Question: {question}

Explain the flow of execution and data."""
    ),

    "summary": PromptTemplate(
        name="summary",
        system_prompt="""You are a code summarizer.
Provide concise summaries of code functionality.
Focus on the main purpose, inputs, outputs, and key behaviors.""",
        user_template="""Summarize this code:

{code_context}

Provide a brief overview including:
- What it does
- Key functions/methods
- Main data structures used"""
    ),
}


class PromptBuilder:
    def __init__(self, templates: Dict[str, PromptTemplate] = None):
        self.templates = templates or DEFAULT_TEMPLATES

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        return list(self.templates.keys())

    def format_context(
        self,
        code_chunks: List[Dict],
        max_context_length: int = 8000
    ) -> str:
        context_parts = []
        total_length = 0

        for chunk in code_chunks:
            file_path = chunk.get('file_path', 'unknown')
            start_line = chunk.get('start_line', 0)
            end_line = chunk.get('end_line', 0)
            content = chunk.get('content', '')

            chunk_text = f"// File: {file_path} (lines {start_line}-{end_line})\n{content}"

            if total_length + len(chunk_text) > max_context_length:
                break

            context_parts.append(chunk_text)
            total_length += len(chunk_text)

        return "\n\n---\n\n".join(context_parts)

    def build_messages(
        self,
        template_name: str,
        code_chunks: List[Dict],
        question: str,
        max_context_length: int = 8000
    ) -> tuple[List[Message], str]:
        template = self.get_template(template_name)
        if not template:
            template = self.templates["code_search"]

        context = self.format_context(code_chunks, max_context_length)

        kwargs = {
            'code_context': context,
            'question': question,
            'focus_areas': question if question else "General review"
        }

        system_prompt, user_prompt = template.format(**kwargs)

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt)
        ]

        return messages, context

    def build_qa_messages(
        self,
        code_chunks: List[Dict],
        question: str,
        template_name: str = "code_search",
        conversation_history: List[Dict] = None,
        max_context_length: int = 8000
    ) -> List[Message]:
        messages = []
        template = self.get_template(template_name) or self.templates["code_search"]

        context = self.format_context(code_chunks, max_context_length)

        system_prompt = template.system_prompt
        messages.append(Message(role="system", content=system_prompt))

        if conversation_history:
            for msg in conversation_history[-5:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append(Message(role=role, content=content))

        user_prompt = template.user_template.format(
            code_context=context,
            question=question
        )
        messages.append(Message(role="user", content=user_prompt))

        return messages

    def add_template(self, template: PromptTemplate):
        self.templates[template.name] = template

    def remove_template(self, name: str):
        if name in self.templates:
            del self.templates[name]

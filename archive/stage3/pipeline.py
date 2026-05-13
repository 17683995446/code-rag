import time
from typing import List, Dict, Optional, Any

from stage3.types import EnhancementConfig, EnhancementStats, EnhancedResult, EnhancementType
from stage3.call_graph import CallGraphAnalyzer
from stage3.enhancers import CodeSummarizer, SimilarCodeFinder, UsageExampleFinder


class EnhancementPipeline:
    def __init__(
        self,
        metadata: List[Dict],
        config: EnhancementConfig = None
    ):
        self.metadata = metadata
        self.config = config or EnhancementConfig()

        self.call_graph_analyzer = None
        self.summarizer = None
        self.similar_finder = None
        self.usage_finder = None

        if self.config.enable_call_graph:
            self.call_graph_analyzer = CallGraphAnalyzer(metadata)

        if self.config.enable_summary:
            self.summarizer = CodeSummarizer(metadata)

        if self.config.enable_similar_code:
            self.similar_finder = SimilarCodeFinder(metadata)

        if self.config.enable_usage_examples:
            self.usage_finder = UsageExampleFinder(metadata)

    def enhance_results(self, results: List[Dict]) -> List[EnhancedResult]:
        enhanced_results = []
        start_time = time.time()

        for result in results:
            enhanced = self._enhance_single(result)
            enhanced_results.append(enhanced)

        stats = EnhancementStats(
            total_enhanced=len(enhanced_results),
            total_time_ms=(time.time() - start_time) * 1000
        )

        return enhanced_results

    def _enhance_single(self, result: Dict) -> EnhancedResult:
        enhanced = EnhancedResult(original_result=result)

        if self.config.enable_summary and self.summarizer:
            enhanced.summary = self.summarizer.summarize(result)

        if self.config.enable_call_graph and self.call_graph_analyzer:
            enhanced.call_graph = self._build_call_graph_for_result(result)

        if self.config.enable_similar_code and self.similar_finder:
            similar = self.similar_finder.find_similar(
                result,
                top_k=self.config.max_similar_results
            )
            enhanced.similar_codes = similar

        if self.config.enable_usage_examples and self.usage_finder:
            symbol_name = result.get('metadata', {}).get('symbol_name', '')
            if symbol_name:
                enhanced.usage_examples = self.usage_finder.find_usages(symbol_name)

        return enhanced

    def _build_call_graph_for_result(self, result: Dict) -> Dict:
        symbols = result.get('symbols', [])
        if not symbols:
            return {}

        main_symbol = symbols[0]
        symbol_name = main_symbol.get('name', '')
        file_path = result.get('file_path', '')

        call_graph_data = {
            'main_symbol': symbol_name,
            'file': file_path,
            'callers': [],
            'callees': [],
            'chain': []
        }

        if self.call_graph_analyzer:
            callers = self.call_graph_analyzer.get_callers(
                symbol_name, file_path, self.config.max_call_depth
            )
            call_graph_data['callers'] = callers[:10]

            callees = self.call_graph_analyzer.get_callees(
                symbol_name, file_path, self.config.max_call_depth
            )
            call_graph_data['callees'] = callees[:10]

            context = self.call_graph_analyzer.get_symbol_context(symbol_name, file_path)
            if context:
                call_graph_data['context'] = context

        return call_graph_data

    def enhance_with_call_chain(
        self,
        start_symbol: str,
        end_symbol: str
    ) -> Dict:
        if not self.call_graph_analyzer:
            return {}

        chains = self.call_graph_analyzer.build_call_chain(
            start_symbol, end_symbol
        )

        return {
            'start': start_symbol,
            'end': end_symbol,
            'chains': chains,
            'chain_count': len(chains)
        }


def quick_enhance(results: List[Dict], metadata: List[Dict]) -> List[EnhancedResult]:
    config = EnhancementConfig()
    pipeline = EnhancementPipeline(metadata, config)
    return pipeline.enhance_results(results)

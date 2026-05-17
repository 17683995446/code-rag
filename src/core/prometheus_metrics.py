"""
Prometheus监控模块 - 产品级
支持标准Prometheus指标
站在巨人的肩膀上 - 使用prometheus-client
"""

from typing import Optional
from contextlib import contextmanager
import time

from .logger import get_logger

logger = get_logger(__name__)


class PrometheusMetrics:
    """
    Prometheus指标收集器
    可选择是否启用真实Prometheus
    """

    def __init__(self):
        self._initialized = False
        self._prometheus_available = False
        self._fallback = True

        # 尝试初始化Prometheus
        self._try_init_prometheus()

    def _try_init_prometheus(self):
        """尝试初始化Prometheus"""
        try:
            import prometheus_client
            from prometheus_client import (
                Counter, Histogram, Gauge, Summary
            )

            self._prometheus = prometheus_client
            self._Counter = Counter
            self._Histogram = Histogram
            self._Gauge = Gauge
            self._Summary = Summary

            # 创建指标
            self._metrics = {
                'search_total': Counter(
                    'code_rag_search_total',
                    'Total number of search requests'
                ),
                'search_duration': Histogram(
                    'code_rag_search_duration_seconds',
                    'Search duration in seconds'
                ),
                'ask_total': Counter(
                    'code_rag_ask_total',
                    'Total number of ask requests'
                ),
                'ask_duration': Histogram(
                    'code_rag_ask_duration_seconds',
                    'Ask duration in seconds'
                ),
                'index_total': Counter(
                    'code_rag_index_total',
                    'Total number of index operations'
                ),
                'index_duration': Histogram(
                    'code_rag_index_duration_seconds',
                    'Index duration in seconds'
                ),
                'documents_indexed': Gauge(
                    'code_rag_documents_indexed',
                    'Number of documents currently indexed'
                ),
                'vector_dimension': Gauge(
                    'code_rag_vector_dimension',
                    'Dimension of vector embeddings'
                ),
                'api_requests_total': Counter(
                    'code_rag_api_requests_total',
                    'Total API requests',
                    ['endpoint']
                ),
                'api_errors_total': Counter(
                    'code_rag_api_errors_total',
                    'Total API errors',
                    ['endpoint']
                )
            }

            self._prometheus_available = True
            self._fallback = False
            logger.info("Prometheus metrics initialized successfully")

        except ImportError:
            self._prometheus_available = False
            self._fallback = True
            self._metrics = {}
            logger.warning("Prometheus not available, using fallback")

    def is_available(self) -> bool:
        """检查Prometheus是否可用"""
        return self._prometheus_available

    def inc_search(self):
        """增加搜索计数"""
        if self._fallback:
            return
        try:
            self._metrics['search_total'].inc()
        except Exception as e:
            logger.debug(f"Prometheus inc failed: {e}")

    def observe_search_duration(self, duration: float):
        """记录搜索耗时"""
        if self._fallback:
            return
        try:
            self._metrics['search_duration'].observe(duration)
        except Exception as e:
            logger.debug(f"Prometheus observe failed: {e}")

    def inc_ask(self):
        """增加问答计数"""
        if self._fallback:
            return
        try:
            self._metrics['ask_total'].inc()
        except Exception as e:
            logger.debug(f"Prometheus inc failed: {e}")

    def observe_ask_duration(self, duration: float):
        """记录问答耗时"""
        if self._fallback:
            return
        try:
            self._metrics['ask_duration'].observe(duration)
        except Exception as e:
            logger.debug(f"Prometheus observe failed: {e}")

    def inc_index(self):
        """增加索引计数"""
        if self._fallback:
            return
        try:
            self._metrics['index_total'].inc()
        except Exception as e:
            logger.debug(f"Prometheus inc failed: {e}")

    def observe_index_duration(self, duration: float):
        """记录索引耗时"""
        if self._fallback:
            return
        try:
            self._metrics['index_duration'].observe(duration)
        except Exception as e:
            logger.debug(f"Prometheus observe failed: {e}")

    def set_documents_indexed(self, count: int):
        """设置索引文档数"""
        if self._fallback:
            return
        try:
            self._metrics['documents_indexed'].set(count)
        except Exception as e:
            logger.debug(f"Prometheus set failed: {e}")

    def set_vector_dimension(self, dimension: int):
        """设置向量维度"""
        if self._fallback:
            return
        try:
            self._metrics['vector_dimension'].set(dimension)
        except Exception as e:
            logger.debug(f"Prometheus set failed: {e}")

    def inc_api_request(self, endpoint: str):
        """增加API请求计数"""
        if self._fallback:
            return
        try:
            self._metrics['api_requests_total'].labels(endpoint=endpoint).inc()
        except Exception as e:
            logger.debug(f"Prometheus inc failed: {e}")

    def inc_api_error(self, endpoint: str):
        """增加API错误计数"""
        if self._fallback:
            return
        try:
            self._metrics['api_errors_total'].labels(endpoint=endpoint).inc()
        except Exception as e:
            logger.debug(f"Prometheus inc failed: {e}")

    def get_metrics_text(self) -> str:
        """获取Prometheus格式的指标文本"""
        if self._fallback:
            # Fallback metrics
            return """# HELP code_rag_fallback Fallback metrics mode active
# TYPE code_rag_fallback gauge
code_rag_fallback 1
"""

        try:
            from prometheus_client import generate_latest
            return generate_latest().decode('utf-8')
        except Exception as e:
            logger.debug(f"Generate metrics failed: {e}")
            return f"# Error generating metrics: {e}\n"

    @contextmanager
    def measure_operation(self, operation_type: str):
        """测量操作耗时"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if operation_type == 'search':
                self.inc_search()
                self.observe_search_duration(duration)
            elif operation_type == 'ask':
                self.inc_ask()
                self.observe_ask_duration(duration)
            elif operation_type == 'index':
                self.inc_index()
                self.observe_index_duration(duration)


# 全局实例
_prometheus: Optional[PrometheusMetrics] = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """获取Prometheus指标收集器"""
    global _prometheus
    if _prometheus is None:
        _prometheus = PrometheusMetrics()
    return _prometheus

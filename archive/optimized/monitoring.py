import time
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import threading
from collections import defaultdict


@dataclass
class Metric:
    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    def __init__(self, namespace: str = "code_rag"):
        self.namespace = namespace
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def counter(self, name: str, value: float = 1, labels: Dict = None):
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value

    def gauge(self, name: str, value: float, labels: Dict = None):
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value

    def histogram(self, name: str, value: float, labels: Dict = None):
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-500:]

    def _make_key(self, name: str, labels: Dict = None) -> str:
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{self.namespace}_{name}{{{label_str}}}"
        return f"{self.namespace}_{name}"

    def get_metrics(self) -> Dict:
        with self._lock:
            metrics = {}

            for key, value in self._counters.items():
                metrics[key] = {"type": "counter", "value": value}

            for key, value in self._gauges.items():
                metrics[key] = {"type": "gauge", "value": value}

            for key, values in self._histograms.items():
                if values:
                    sorted_vals = sorted(values)
                    metrics[key] = {
                        "type": "histogram",
                        "count": len(values),
                        "sum": sum(values),
                        "min": sorted_vals[0],
                        "max": sorted_vals[-1],
                        "p50": sorted_vals[len(sorted_vals) // 2],
                        "p95": sorted_vals[int(len(sorted_vals) * 0.95)] if len(sorted_vals) > 20 else sorted_vals[-1],
                        "p99": sorted_vals[int(len(sorted_vals) * 0.99)] if len(sorted_vals) > 100 else sorted_vals[-1]
                    }

            return metrics

    def export_prometheus(self) -> str:
        lines = []

        with self._lock:
            for key, value in self._counters.items():
                lines.append(f"{key} {value}")

            for key, value in self._gauges.items():
                lines.append(f"{key} {value}")

            for key, values in self._histograms.items():
                if values:
                    base_key = key.split('{')[0]
                    labels = key.split('{')[1].rstrip('}') if '{' in key else ''
                    sorted_vals = sorted(values)

                    lines.append(f"{base_key}_count{{{labels}}} {len(values)}")
                    lines.append(f"{base_key}_sum{{{labels}}} {sum(values)}")
                    lines.append(f"{base_key}_bucket{{{labels},le=\"0.01\"}} {len([v for v in values if v <= 0.01])}")
                    lines.append(f"{base_key}_bucket{{{labels},le=\"0.1\"}} {len([v for v in values if v <= 0.1])}")
                    lines.append(f"{base_key}_bucket{{{labels},le=\"0.5\"}} {len([v for v in values if v <= 0.5])}")
                    lines.append(f"{base_key}_bucket{{{labels},le=\"1\"}} {len([v for v in values if v <= 1])}")
                    lines.append(f"{base_key}_bucket{{{labels},le=\"+Inf\"}} {len(values)}")

        return "\n".join(lines)


class StructuredLogger:
    def __init__(self, name: str, log_file: str = None):
        self.name = name
        self.log_file = Path(log_file) if log_file else None

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, message: str, **kwargs):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            **kwargs
        }

        output = json.dumps(entry)

        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(output + "\n")
        else:
            print(output)

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)


class PerformanceMonitor:
    def __init__(self, metrics: MetricsCollector = None):
        self.metrics = metrics or MetricsCollector()
        self.logger = StructuredLogger("performance")

    def track_time(self, operation: str):
        return TimeTracker(self.metrics, operation, self.logger)

    def record_operation(self, operation: str, duration: float, success: bool = True):
        self.metrics.histogram(f"{operation}_duration_seconds", duration)
        self.metrics.counter(f"{operation}_total", labels={"success": str(success).lower()})

        self.logger.info(
            f"Operation completed",
            operation=operation,
            duration_ms=duration * 1000,
            success=success
        )


class TimeTracker:
    def __init__(self, metrics: MetricsCollector, operation: str, logger: StructuredLogger):
        self.metrics = metrics
        self.operation = operation
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None

        self.metrics.histogram(f"{self.operation}_duration_seconds", duration)
        self.metrics.counter(f"{self.operation}_total", labels={"success": str(success).lower()})

        self.logger.debug(
            f"Operation: {self.operation}",
            duration_ms=duration * 1000,
            success=success
        )


class HealthChecker:
    def __init__(self, index_manager=None):
        self.index_manager = index_manager
        self.checks = {}

    def register_check(self, name: str, check_func):
        self.checks[name] = check_func

    def run_checks(self) -> Dict:
        results = {}
        all_healthy = True

        for name, check_func in self.checks.items():
            try:
                healthy, message = check_func()
                results[name] = {"status": "healthy" if healthy else "unhealthy", "message": message}
                if not healthy:
                    all_healthy = False
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
                all_healthy = False

        results["overall"] = "healthy" if all_healthy else "unhealthy"
        return results

    def check_storage(self) -> tuple:
        try:
            if self.index_manager:
                stats = self.index_manager.storage.stats()
                return True, f"{stats.get('total_chunks', 0)} chunks indexed"
            return False, "Index manager not initialized"
        except Exception as e:
            return False, str(e)

    def check_memory(self) -> tuple:
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return False, f"Memory usage high: {memory.percent}%"
            return True, f"Memory usage: {memory.percent}%"
        except ImportError:
            return True, "psutil not available"

    def check_disk(self) -> tuple:
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            percent = (used / total) * 100
            if percent > 90:
                return False, f"Disk usage high: {percent:.1f}%"
            return True, f"Disk usage: {percent:.1f}%"
        except Exception as e:
            return True, f"Disk check skipped: {e}"


class Tracer:
    def __init__(self, service_name: str = "code-rag"):
        self.service_name = service_name
        self.spans: List[Dict] = []
        self._current_span: Optional[Dict] = None

    def start_span(self, operation: str, parent_id: str = None) -> str:
        import uuid
        span_id = str(uuid.uuid4())[:16]

        span = {
            "trace_id": self._current_span.get("trace_id", str(uuid.uuid4())[:32]) if self._current_span else str(uuid.uuid4())[:32],
            "span_id": span_id,
            "parent_id": parent_id or (self._current_span.get("span_id") if self._current_span else None),
            "operation": operation,
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": None,
            "tags": {}
        }

        self.spans.append(span)
        self._current_span = span

        return span_id

    def end_span(self, span_id: str = None):
        if span_id:
            for span in self.spans:
                if span["span_id"] == span_id:
                    span["end_time"] = time.time()
                    span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
                    break
        elif self._current_span:
            self._current_span["end_time"] = time.time()
            self._current_span["duration_ms"] = (self._current_span["end_time"] - self._current_span["start_time"]) * 1000
            self._current_span = None

    def add_tag(self, key: str, value: Any):
        if self._current_span:
            self._current_span["tags"][key] = value

    def get_trace(self) -> List[Dict]:
        return self.spans

    def clear(self):
        self.spans = []
        self._current_span = None


metrics = MetricsCollector()
logger = StructuredLogger("code_rag")
monitor = PerformanceMonitor(metrics)

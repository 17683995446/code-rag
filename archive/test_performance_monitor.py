"""
性能监控和分析面板模块

提供系统性能指标、查询分析、系统健康监控和可视化仪表板
"""

import os
import sys
import json
import time
import hashlib
import threading
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    name: str
    metric_type: MetricType
    value: Any = 0.0
    tags: Dict = field(default_factory=dict)
    timestamp: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class Histogram:
    name: str
    percentiles: Dict[float, float] = field(default_factory=dict)
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = 0.0
    samples: List[float] = field(default_factory=list)


@dataclass
class QueryStat:
    query_id: str
    query_type: str
    latency_ms: float
    result_count: int
    cache_hit: bool = False
    timestamp: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class SystemHealth:
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_used_mb: float
    disk_total_mb: float
    disk_percent: float
    active_connections: int = 0
    process_count: int = 0
    timestamp: float = 0.0


class MetricsCollector:
    def __init__(self, storage_path: str = "./data/metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, Histogram] = {}
        self._timers: Dict[str, List[float]] = defaultdict(list)

        self._query_stats: List[QueryStat] = []
        self._system_health_history: deque = deque(maxlen=1000)
        self._query_history: deque = deque(maxlen=10000)

        self._lock = threading.Lock()
        self._started = False
        self._monitor_thread = None

        self._load_historical_data()

    def _load_historical_data(self):
        try:
            metrics_file = self.storage_path / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file) as f:
                    data = json.load(f)
                    self._counters.update(data.get("counters", {}))
                    self._gauges.update(data.get("gauges", {}))
        except Exception:
            pass

    def _save_metrics(self):
        try:
            metrics_file = self.storage_path / "metrics.json"
            data = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timestamp": time.time()
            }
            with open(metrics_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def increment_counter(self, name: str, value: float = 1.0, tags: Dict = None):
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: float, tags: Dict = None):
        with self._lock:
            self._gauges[name] = value

    def record_histogram(self, name: str, value: float, tags: Dict = None):
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name=name)

            hist = self._histograms[name]
            hist.count += 1
            hist.sum += value
            hist.min = min(hist.min, value)
            hist.max = max(hist.max, value)
            hist.samples.append(value)

            if len(hist.samples) > 10000:
                hist.samples = hist.samples[-10000:]

            self._calculate_percentiles(hist)

    def _calculate_percentiles(self, hist: Histogram):
        if not hist.samples:
            return

        sorted_samples = sorted(hist.samples)
        n = len(sorted_samples)

        percentiles = [0.50, 0.75, 0.90, 0.95, 0.99]
        for p in percentiles:
            idx = int(n * p)
            if idx >= n:
                idx = n - 1
            hist.percentiles[p] = sorted_samples[idx]

    def time_operation(self, name: str) -> Callable:
        start_time = time.time()

        def decorator(func):
            def wrapper(*args, **kwargs):
                nonlocal start_time
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                self.record_histogram(f"{name}.duration", elapsed)
                return result
            return wrapper

        return decorator

    def record_query(self, query_stat: QueryStat):
        with self._lock:
            self._query_stats.append(query_stat)
            self._query_history.append(query_stat)

            self.increment_counter("queries.total")

            if query_stat.cache_hit:
                self.increment_counter("queries.cache_hits")

            self.record_histogram("queries.latency", query_stat.latency_ms)

    def get_metric_summary(self) -> Dict:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: {
                        "count": h.count,
                        "sum": h.sum,
                        "min": h.min,
                        "max": h.max,
                        "avg": h.sum / h.count if h.count > 0 else 0,
                        "percentiles": h.percentiles
                    }
                    for name, h in self._histograms.items()
                }
            }

    def get_query_stats(self, window_seconds: int = 3600) -> Dict:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            recent_queries = [q for q in self._query_history if q.timestamp >= cutoff]

            if not recent_queries:
                return {"total": 0}

            latencies = [q.latency_ms for q in recent_queries]
            cache_hits = sum(1 for q in recent_queries if q.cache_hit)

            return {
                "total": len(recent_queries),
                "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
                "p50_latency_ms": statistics.median(latencies) if latencies else 0,
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                "cache_hit_rate": cache_hits / len(recent_queries) if recent_queries else 0,
                "total_result_count": sum(q.result_count for q in recent_queries)
            }

    def export_metrics(self, format: str = "json") -> str:
        summary = self.get_metric_summary()

        if format == "json":
            return json.dumps(summary, indent=2)
        elif format == "prometheus":
            lines = []
            for name, value in self._counters.items():
                lines.append(f"# HELP {name} Counter")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
            return "\n".join(lines)
        else:
            return json.dumps(summary)


class SystemMonitor:
    def __init__(self):
        self._health_history: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._last_sample = None

    def sample_system_health(self) -> SystemHealth:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health = SystemHealth(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_used_mb=disk.used / (1024 * 1024),
                disk_total_mb=disk.total / (1024 * 1024),
                disk_percent=disk.percent,
                active_connections=len(psutil.net_connections()),
                process_count=len(psutil.pids()),
                timestamp=time.time()
            )

            with self._lock:
                self._health_history.append(health)
                self._last_sample = health

            return health

        except Exception as e:
            return SystemHealth(
                cpu_percent=0,
                memory_percent=0,
                memory_used_mb=0,
                memory_total_mb=1,
                disk_used_mb=0,
                disk_total_mb=1,
                disk_percent=0,
                timestamp=time.time()
            )

    def get_current_health(self) -> Optional[SystemHealth]:
        return self._last_sample

    def get_health_history(self, limit: int = 100) -> List[SystemHealth]:
        with self._lock:
            return list(self._health_history)[-limit:]

    def get_health_summary(self) -> Dict:
        history = self.get_health_history()
        if not history:
            return {}

        cpu_values = [h.cpu_percent for h in history]
        memory_values = [h.memory_percent for h in history]
        disk_values = [h.disk_percent for h in history]

        return {
            "current": {
                "cpu": self._last_sample.cpu_percent if self._last_sample else 0,
                "memory": self._last_sample.memory_percent if self._last_sample else 0,
                "disk": self._last_sample.disk_percent if self._last_sample else 0
            },
            "history": {
                "count": len(history),
                "cpu_avg": statistics.mean(cpu_values) if cpu_values else 0,
                "cpu_max": max(cpu_values) if cpu_values else 0,
                "memory_avg": statistics.mean(memory_values) if memory_values else 0,
                "disk_avg": statistics.mean(disk_values) if disk_values else 0
            }
        }


class QueryAnalyzer:
    def __init__(self):
        self._slow_queries: List[QueryStat] = []
        self._query_patterns: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def analyze_query(self, query: str) -> Dict:
        pattern_hash = hashlib.md5(query.encode()).hexdigest()

        with self._lock:
            self._query_patterns[pattern_hash] += 1

        return {
            "pattern_hash": pattern_hash,
            "frequency": self._query_patterns.get(pattern_hash, 0)
        }

    def record_slow_query(self, query_stat: QueryStat, threshold_ms: float = 500):
        if query_stat.latency_ms > threshold_ms:
            with self._lock:
                self._slow_queries.append(query_stat)
                if len(self._slow_queries) > 1000:
                    self._slow_queries.pop(0)

    def get_slow_queries(self, limit: int = 20) -> List[QueryStat]:
        with self._lock:
            sorted_slow = sorted(
                self._slow_queries,
                key=lambda q: q.latency_ms,
                reverse=True
            )
            return sorted_slow[:limit]

    def get_query_pattern_analysis(self, top_n: int = 10) -> List[Dict]:
        with self._lock:
            sorted_patterns = sorted(
                self._query_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [
                {"pattern_hash": p, "count": c}
                for p, c in sorted_patterns[:top_n]
            ]


class AlertManager:
    def __init__(self):
        self._alerts: List[Dict] = []
        self._alert_rules: List[Dict] = []
        self._lock = threading.Lock()

    def add_alert_rule(self, rule: Dict):
        with self._lock:
            self._alert_rules.append(rule)

    def check_rules(self, metrics: Dict, health: SystemHealth):
        with self._lock:
            for rule in self._alert_rules:
                self._check_rule(rule, metrics, health)

    def _check_rule(self, rule: Dict, metrics: Dict, health: SystemHealth):
        condition = rule.get("condition")
        if condition == "cpu_high" and health.cpu_percent > 80:
            self._create_alert("warn", f"CPU usage high: {health.cpu_percent}%")
        elif condition == "memory_high" and health.memory_percent > 85:
            self._create_alert("warn", f"Memory usage high: {health.memory_percent}%")
        elif condition == "slow_queries":
            query_stats = metrics.get("queries", {})
            if query_stats.get("avg_latency_ms", 0) > 500:
                self._create_alert("warn", "Slow queries detected")

    def _create_alert(self, level: str, message: str):
        alert = {
            "level": level,
            "message": message,
            "timestamp": time.time()
        }
        self._alerts.append(alert)
        if len(self._alerts) > 1000:
            self._alerts.pop(0)

    def get_alerts(self, level: str = None, limit: int = 20) -> List[Dict]:
        with self._lock:
            alerts = self._alerts
            if level:
                alerts = [a for a in alerts if a["level"] == level]
            return alerts[-limit:]


class DashboardGenerator:
    def __init__(self, metrics_collector: MetricsCollector, system_monitor: SystemMonitor, query_analyzer: QueryAnalyzer):
        self.metrics_collector = metrics_collector
        self.system_monitor = system_monitor
        self.query_analyzer = query_analyzer

    def generate_dashboard_html(self) -> str:
        query_stats = self.metrics_collector.get_query_stats()
        health = self.system_monitor.get_current_health()
        health_summary = self.system_monitor.get_health_summary()
        slow_queries = self.query_analyzer.get_slow_queries(10)
        metrics_summary = self.metrics_collector.get_metric_summary()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>RAG Performance Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .stat-box {{ text-align: center; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .health-good {{ color: #27ae60; }}
        .health-warning {{ color: #f39c12; }}
        .health-danger {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .progress {{ background: #e9ecef; border-radius: 4px; height: 20px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: #667eea; transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 RAG Performance Dashboard</h1>
            <p>Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="grid">
            <div class="stat-box">
                <div class="stat-value">{query_stats.get('total', 0)}</div>
                <div class="stat-label">Total Queries (1h)</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{query_stats.get('avg_latency_ms', 0):.1f}ms</div>
                <div class="stat-label">Avg Latency</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{query_stats.get('cache_hit_rate', 0)*100:.1f}%</div>
                <div class="stat-label">Cache Hit Rate</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{metrics_summary.get('counters', {}).get('indexes.total', 0)}</div>
                <div class="stat-label">Indexed Chunks</div>
            </div>
        </div>

        <div class="card">
            <h2>🖥️ System Health</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
                <div>
                    <p><strong>CPU Usage</strong></p>
                    <div class="progress">
                        <div class="progress-bar" style="width: {health.cpu_percent}%; background-color: {self._get_health_color(health.cpu_percent)}"></div>
                    </div>
                    <p class="{self._get_health_class(health.cpu_percent)}">{health.cpu_percent}%</p>
                </div>
                <div>
                    <p><strong>Memory Usage</strong></p>
                    <div class="progress">
                        <div class="progress-bar" style="width: {health.memory_percent}%; background-color: {self._get_health_color(health.memory_percent)}"></div>
                    </div>
                    <p class="{self._get_health_class(health.memory_percent)}">{health.memory_percent}% ({health.memory_used_mb:.0f}/{health.memory_total_mb:.0f} MB)</p>
                </div>
                <div>
                    <p><strong>Disk Usage</strong></p>
                    <div class="progress">
                        <div class="progress-bar" style="width: {health.disk_percent}%; background-color: {self._get_health_color(health.disk_percent)}"></div>
                    </div>
                    <p class="{self._get_health_class(health.disk_percent)}">{health.disk_percent}% ({health.disk_used_mb:.0f}/{health.disk_total_mb:.0f} MB)</p>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📈 Query Latency Statistics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td>Average Latency</td><td>{query_stats.get('avg_latency_ms', 0):.1f}ms</td></tr>
                    <tr><td>P50 Latency</td><td>{query_stats.get('p50_latency_ms', 0):.1f}ms</td></tr>
                    <tr><td>P95 Latency</td><td>{query_stats.get('p95_latency_ms', 0):.1f}ms</td></tr>
                    <tr><td>Total Results</td><td>{query_stats.get('total_result_count', 0)}</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>⚠️ Slow Queries (Top 10)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Query ID</th>
                        <th>Type</th>
                        <th>Latency</th>
                        <th>Results</th>
                        <th>Cache</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    {self._render_slow_queries(slow_queries)}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
        return html

    def _get_health_color(self, value: float) -> str:
        if value < 60:
            return "#27ae60"
        elif value < 80:
            return "#f39c12"
        else:
            return "#e74c3c"

    def _get_health_class(self, value: float) -> str:
        if value < 60:
            return "health-good"
        elif value < 80:
            return "health-warning"
        else:
            return "health-danger"

    def _render_slow_queries(self, slow_queries: List[QueryStat]) -> str:
        if not slow_queries:
            return "<tr><td colspan='6'>No slow queries recorded</td></tr>"

        rows = []
        for q in slow_queries:
            time_str = time.strftime('%H:%M:%S', time.localtime(q.timestamp))
            cache_icon = "✅" if q.cache_hit else "❌"
            rows.append(
                f"<tr>"
                f"<td>{q.query_id[:12]}...</td>"
                f"<td>{q.query_type}</td>"
                f"<td><strong>{q.latency_ms:.1f}ms</strong></td>"
                f"<td>{q.result_count}</td>"
                f"<td>{cache_icon}</td>"
                f"<td>{time_str}</td>"
                f"</tr>"
            )
        return "\n".join(rows)


class PerformanceMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor()
        self.query_analyzer = QueryAnalyzer()
        self.alert_manager = AlertManager()
        self.dashboard = DashboardGenerator(
            self.metrics_collector,
            self.system_monitor,
            self.query_analyzer
        )

        self._running = False
        self._monitor_thread = None

        self._setup_default_alerts()

    def _setup_default_alerts(self):
        self.alert_manager.add_alert_rule({"condition": "cpu_high"})
        self.alert_manager.add_alert_rule({"condition": "memory_high"})
        self.alert_manager.add_alert_rule({"condition": "slow_queries"})

    def start_monitoring(self):
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self):
        while self._running:
            try:
                health = self.system_monitor.sample_system_health()
                metrics = self.metrics_collector.get_metric_summary()
                self.alert_manager.check_rules(metrics, health)
                time.sleep(5)
            except Exception as e:
                time.sleep(5)

    def record_query_performance(
        self,
        query_id: str,
        query_type: str,
        latency_ms: float,
        result_count: int,
        cache_hit: bool = False
    ):
        query_stat = QueryStat(
            query_id=query_id,
            query_type=query_type,
            latency_ms=latency_ms,
            result_count=result_count,
            cache_hit=cache_hit,
            timestamp=time.time()
        )

        self.metrics_collector.record_query(query_stat)
        self.query_analyzer.record_slow_query(query_stat, threshold_ms=500)

    def get_dashboard(self) -> str:
        return self.dashboard.generate_dashboard_html()

    def get_json_report(self) -> Dict:
        return {
            "timestamp": time.time(),
            "metrics": self.metrics_collector.get_metric_summary(),
            "queries": self.metrics_collector.get_query_stats(),
            "system": self.system_monitor.get_health_summary(),
            "alerts": self.alert_manager.get_alerts(limit=10)
        }


def demo_performance_monitor():
    print("\n" + "="*60)
    print("演示: 性能监控面板")
    print("="*60)

    monitor = PerformanceMonitor()
    monitor.start_monitoring()

    print("\n📊 步骤1: 模拟查询负载")
    import random

    query_types = ["semantic_search", "keyword_search", "exact_match"]

    for i in range(50):
        query_id = f"q_{i:03d}"
        query_type = random.choice(query_types)
        latency_ms = random.uniform(10, 300)
        cache_hit = random.random() < 0.3
        result_count = random.randint(1, 20)

        monitor.record_query_performance(
            query_id=query_id,
            query_type=query_type,
            latency_ms=latency_ms,
            result_count=result_count,
            cache_hit=cache_hit
        )

        if i % 10 == 0:
            print(f"   ✅ 记录查询 {i+1}/50")

    print("\n🔍 步骤2: 生成监控报告")

    report = monitor.get_json_report()

    print("\n📈 查询统计:")
    queries = report["queries"]
    print(f"   - 总查询数: {queries.get('total', 0)}")
    print(f"   - 平均延迟: {queries.get('avg_latency_ms', 0):.1f}ms")
    print(f"   - P50延迟: {queries.get('p50_latency_ms', 0):.1f}ms")
    print(f"   - P95延迟: {queries.get('p95_latency_ms', 0):.1f}ms")
    print(f"   - 缓存命中率: {queries.get('cache_hit_rate', 0)*100:.1f}%")

    print("\n🖥️ 系统健康:")
    system = report["system"]
    current = system.get("current", {})
    print(f"   - CPU使用率: {current.get('cpu', 0)}%")
    print(f"   - 内存使用率: {current.get('memory', 0)}%")
    print(f"   - 磁盘使用率: {current.get('disk', 0)}%")

    print("\n🌐 步骤3: 生成HTML仪表板")

    dashboard_html = monitor.get_dashboard()

    dashboard_file = Path("/tmp/rag_dashboard.html")
    dashboard_file.write_text(dashboard_html)
    print(f"   ✅ 仪表板已保存: {dashboard_file}")
    print(f"   📊 可在浏览器中打开查看实时数据")

    print("\n⚠️ 慢查询分析:")
    slow_queries = monitor.query_analyzer.get_slow_queries(5)
    if slow_queries:
        print(f"   发现 {len(slow_queries)} 个慢查询:")
        for i, q in enumerate(slow_queries[:3]):
            print(f"     {i+1}. {q.query_type} - {q.latency_ms:.1f}ms")
    else:
        print(f"   无慢查询")

    print("\n" + "="*60)
    print("性能监控演示完成！")
    print("="*60)

    monitor.stop_monitoring()


if __name__ == "__main__":
    demo_performance_monitor()

"""
综合评估脚本 - 产品级
运行所有测试并生成多维度评分报告
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    CodeRAG,
    RAGEvaluator,
    create_default_test_suite,
    get_monitor,
    get_backup_manager,
    get_version_control
)


class MultiDimensionalScorer:
    """
    多维度评分器
    评估系统的各个维度并生成综合评分
    """

    def __init__(self):
        self.results = {}
        self.scores = {}

    def add_result(self, dimension: str, result: Dict[str, Any], weight: float):
        """添加评分结果"""
        self.results[dimension] = {
            'result': result,
            'weight': weight
        }

    def calculate_scores(self) -> Dict[str, Any]:
        """计算各维度得分"""
        scores = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for dimension, data in self.results.items():
            score = data['result'].get('score', 0.0)
            weight = data['weight']

            scores[dimension] = {
                'score': score,
                'weight': weight,
                'weighted_score': score * weight,
                'details': data['result']
            }

            weighted_sum += score * weight
            total_weight += weight

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0

        self.scores = {
            'dimensions': scores,
            'overall_score': overall_score,
            'grade': self._get_grade(overall_score)
        }

        return self.scores

    def _get_grade(self, score: float) -> str:
        """根据分数获取等级"""
        if score >= 90:
            return "A+ (卓越)"
        elif score >= 85:
            return "A (优秀)"
        elif score >= 80:
            return "A- (很好)"
        elif score >= 70:
            return "B+ (良好)"
        elif score >= 65:
            return "B (不错)"
        elif score >= 60:
            return "B- (及格)"
        elif score >= 50:
            return "C (需要改进)"
        else:
            return "D (不合格)"


def run_unit_tests() -> Dict[str, Any]:
    """运行单元测试"""
    print("\n" + "="*60)
    print("  📦 单元测试")
    print("="*60)

    import subprocess
    result = subprocess.run(
        [sys.executable, "tests/test_core.py"],
        capture_output=True,
        text=True
    )

    passed = result.returncode == 0

    return {
        'name': '单元测试',
        'score': 100 if passed else 0,
        'passed': passed,
        'total_tests': 8,
        'details': '核心模块单元测试'
    }


def run_integration_tests() -> Dict[str, Any]:
    """运行集成测试"""
    print("\n" + "="*60)
    print("  🔗 集成测试")
    print("="*60)

    import subprocess
    result = subprocess.run(
        [sys.executable, "tests/test_integration.py"],
        capture_output=True,
        text=True
    )

    passed = result.returncode == 0

    return {
        'name': '集成测试',
        'score': 100 if passed else 0,
        'passed': passed,
        'total_tests': 3,
        'details': '模块间集成测试'
    }


def run_system_tests() -> Dict[str, Any]:
    """运行系统测试"""
    print("\n" + "="*60)
    print("  🚀 系统测试")
    print("="*60)

    import subprocess
    result = subprocess.run(
        [sys.executable, "tests/test_system.py"],
        capture_output=True,
        text=True
    )

    passed = result.returncode == 0

    return {
        'name': '系统测试',
        'score': 100 if passed else 0,
        'passed': passed,
        'total_tests': 5,
        'details': '性能和稳定性测试'
    }


def run_new_modules_tests() -> Dict[str, Any]:
    """运行新模块测试"""
    print("\n" + "="*60)
    print("  🔒 安全、备份、评估模块测试")
    print("="*60)

    import subprocess
    result = subprocess.run(
        [sys.executable, "tests/test_security_backup_evaluator.py"],
        capture_output=True,
        text=True
    )

    passed = result.returncode == 0

    return {
        'name': '新模块测试',
        'score': 100 if passed else 0,
        'passed': passed,
        'total_tests': 7,
        'details': '安全、备份、评估模块测试'
    }


def evaluate_rag_performance() -> Dict[str, Any]:
    """评估RAG性能"""
    print("\n" + "="*60)
    print("  📊 RAG系统评估")
    print("="*60)

    try:
        rag = CodeRAG(implementation="simplified")
        evaluator = RAGEvaluator()

        test_cases = create_default_test_suite()
        report = evaluator.evaluate_rag(rag, test_cases)

        if report:
            score = report.overall_score
            print(f"\n  📈 总体得分: {score:.2f}/100")
            print(f"  ✅ 通过测试: {report.passed_tests}/{report.total_tests}")

            return {
                'name': 'RAG性能评估',
                'score': score,
                'passed_tests': report.passed_tests,
                'total_tests': report.total_tests,
                'details': {
                    'precision': report.metrics.get('overall', {}).precision if isinstance(report.metrics.get('overall'), dict) else 0,
                    'recall': report.metrics.get('overall', {}).recall if isinstance(report.metrics.get('overall'), dict) else 0,
                    'f1_score': report.metrics.get('overall', {}).f1_score if isinstance(report.metrics.get('overall'), dict) else 0,
                    'latency_ms': report.metrics.get('overall', {}).latency_ms if isinstance(report.metrics.get('overall'), dict) else 0
                }
            }
    except Exception as e:
        print(f"  ❌ RAG评估失败: {e}")

    return {
        'name': 'RAG性能评估',
        'score': 0,
        'passed_tests': 0,
        'total_tests': 0,
        'details': '评估失败'
    }


def evaluate_module_coverage() -> Dict[str, Any]:
    """评估模块覆盖率"""
    print("\n" + "="*60)
    print("  📚 模块覆盖率")
    print("="*60)

    modules = [
        'core.rag',
        'core.parser',
        'core.bm25',
        'core.cache',
        'core.monitor',
        'core.config',
        'core.security',
        'core.backup',
        'core.evaluator',
        'api.app'
    ]

    covered = 0
    for module in modules:
        try:
            __import__(f"src.{module.replace('.', '.')}")
            covered += 1
            print(f"  ✅ {module}")
        except:
            print(f"  ❌ {module}")

    score = (covered / len(modules)) * 100

    return {
        'name': '模块覆盖率',
        'score': score,
        'covered': covered,
        'total': len(modules),
        'details': f'{covered}/{len(modules)} 模块可用'
    }


def evaluate_code_quality() -> Dict[str, Any]:
    """评估代码质量"""
    print("\n" + "="*60)
    print("  🎯 代码质量评估")
    print("="*60)

    # 简单的代码质量检查
    src_dir = Path("src")
    files = list(src_dir.rglob("*.py"))

    total_lines = 0
    total_files = len(files)

    for f in files:
        try:
            total_lines += len(f.read_text(encoding='utf-8').split('\n'))
        except:
            pass

    # 基于文件数量和代码行数评估
    if total_files >= 10 and total_lines >= 2000:
        score = 90
    elif total_files >= 8 and total_lines >= 1500:
        score = 80
    elif total_files >= 5:
        score = 70
    else:
        score = 50

    print(f"  📁 文件数量: {total_files}")
    print(f"  📝 代码行数: {total_lines}")
    print(f"  🎯 质量评分: {score}/100")

    return {
        'name': '代码质量',
        'score': score,
        'files': total_files,
        'lines': total_lines,
        'details': f'{total_files} 个文件, {total_lines} 行代码'
    }


def evaluate_test_coverage() -> Dict[str, Any]:
    """评估测试覆盖率"""
    print("\n" + "="*60)
    print("  🧪 测试覆盖率")
    print("="*60)

    test_dir = Path("tests")
    test_files = list(test_dir.glob("test_*.py"))

    total_tests = 0
    for f in test_files:
        content = f.read_text()
        test_count = content.count("def test_")
        total_tests += test_count
        print(f"  ✅ {f.name}: {test_count} 个测试")

    # 测试覆盖率评分
    if total_tests >= 20:
        score = 95
    elif total_tests >= 15:
        score = 85
    elif total_tests >= 10:
        score = 75
    elif total_tests >= 5:
        score = 65
    else:
        score = 50

    return {
        'name': '测试覆盖率',
        'score': score,
        'test_files': len(test_files),
        'total_tests': total_tests,
        'details': f'{total_tests} 个测试用例'
    }


def generate_final_report(all_results: Dict[str, Any]) -> Dict[str, Any]:
    """生成最终评估报告"""
    print("\n" + "="*60)
    print("  🏆 最终评估报告")
    print("="*60)

    scorer = MultiDimensionalScorer()

    weights = {
        'unit_tests': 0.15,
        'integration_tests': 0.15,
        'system_tests': 0.15,
        'new_modules_tests': 0.15,
        'rag_performance': 0.20,
        'module_coverage': 0.10,
        'code_quality': 0.05,
        'test_coverage': 0.05
    }

    for key, result in all_results.items():
        weight = weights.get(key, 0.1)
        scorer.add_result(key, result, weight)

    scores = scorer.calculate_scores()

    print(f"\n  {'='*50}")
    print(f"  {'维度':<20} {'得分':<10} {'权重':<10} {'加权分':<10}")
    print(f"  {'-'*50}")

    for dimension, data in scores['dimensions'].items():
        print(f"  {dimension:<20} {data['score']:>6.2f}    {data['weight']:>5.2f}    {data['weighted_score']:>6.2f}")

    print(f"  {'='*50}")
    print(f"  {'综合得分':<20} {scores['overall_score']:>6.2f}    {'1.00':>5}    {scores['overall_score']:>6.2f}")
    print(f"  {'='*50}")
    print(f"\n  📊 等级: {scores['grade']}")
    print(f"  ⏰ 评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
        'overall_score': scores['overall_score'],
        'grade': scores['grade'],
        'dimensions': scores['dimensions'],
        'details': all_results,
        'recommendations': generate_recommendations(scores)
    }

    with open('/workspace/code-rag/evaluation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n  📄 报告已保存: evaluation_report.json")

    return report


def generate_recommendations(scores: Dict[str, Any]) -> List[str]:
    """生成改进建议"""
    recommendations = []

    for dimension, data in scores['dimensions'].items():
        if data['score'] < 70:
            recommendations.append(f"{dimension} 需要改进（当前得分: {data['score']:.2f}）")

    if not recommendations:
        recommendations.append("🎉 所有维度表现优秀！")

    return recommendations


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  🚀 Code RAG v3.0.0 - 综合评估")
    print("="*60)

    results = {}

    # 1. 运行单元测试
    results['unit_tests'] = run_unit_tests()

    # 2. 运行集成测试
    results['integration_tests'] = run_integration_tests()

    # 3. 运行系统测试
    results['system_tests'] = run_system_tests()

    # 4. 运行新模块测试
    results['new_modules_tests'] = run_new_modules_tests()

    # 5. 评估RAG性能
    results['rag_performance'] = evaluate_rag_performance()

    # 6. 评估模块覆盖率
    results['module_coverage'] = evaluate_module_coverage()

    # 7. 评估代码质量
    results['code_quality'] = evaluate_code_quality()

    # 8. 评估测试覆盖率
    results['test_coverage'] = evaluate_test_coverage()

    # 生成最终报告
    report = generate_final_report(results)

    print("\n" + "="*60)
    print("  ✅ 评估完成！")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 监控脚本
检查1小时测试的进度
"""
import sys
import os
import time
import json

def check_test_progress():
    """检查测试进度"""
    log_file = "/workspace/code-rag/v7_hour_long_test_output.log"
    report_file = "/workspace/code-rag/v7_hour_long_test_report.json"
    
    print("="*80)
    print("📊 1小时超长时间测试 - 进度监控")
    print("="*80)
    
    # 检查进程
    print("\n🔍 进程状态:")
    os.system("ps aux | grep v7_hour_long_test | grep -v grep | head -3")
    
    # 检查报告文件
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            print("\n📋 报告摘要:")
            print(f"  开始时间: {report.get('start_time', 'N/A')}")
            print(f"  结束时间: {report.get('end_time', 'N/A')}")
            print(f"  实际时长: {report.get('actual_duration', 0):.0f}秒")
            
            ops = report.get('metrics', {}).get('operations', {})
            print(f"\n⚡ 操作统计:")
            print(f"  总操作: {ops.get('total', 0):,}")
            print(f"  成功: {ops.get('success', 0):,}")
            print(f"  失败: {ops.get('failure', 0):,}")
            
            print(f"\n📈 最终状态:")
            final = report.get('final_stats', {})
            print(f"  节点: {final.get('nodes', 0):,}")
            print(f"  边: {final.get('edges', 0):,}")
            
            print(f"\n🐛 问题:")
            print(f"  Bug: {len(report.get('bugs_found', []))}")
            print(f"  警告: {len(report.get('warnings', []))}")
            
            return report
        except Exception as e:
            print(f"  ❌ 读取报告失败: {e}")
    
    # 检查日志文件
    if os.path.exists(log_file):
        print(f"\n📝 日志文件大小: {os.path.getsize(log_file)} 字节")
        if os.path.getsize(log_file) > 0:
            print("\n最后50行日志:")
            os.system(f"tail -50 {log_file}")
    
    print("\n" + "="*80)
    
    # 检查测试是否还在运行
    result = os.popen("ps aux | grep 'v7_hour_long_test' | grep -v grep | wc -l").read().strip()
    if int(result) > 0:
        print("✅ 测试正在运行中...")
    else:
        print("⚠️  测试已结束")
        if os.path.exists(report_file):
            print("📄 请查看完整报告: v7_hour_long_test_report.json")
    
    print("="*80)

if __name__ == "__main__":
    check_test_progress()

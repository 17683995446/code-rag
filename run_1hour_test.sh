#!/bin/bash
# 1小时测试运行脚本

echo "=========================================="
echo "启动1小时超长时间压力测试"
echo "=========================================="
echo "开始时间: $(date)"
echo ""

cd /workspace/code-rag

# 运行1小时测试
python3 -u v7_hour_long_unbuffered.py

# 保存结果
if [ -f v7_hour_long_test_report.json ]; then
    echo ""
    echo "=========================================="
    echo "1小时测试完成！"
    echo "结束时间: $(date)"
    echo "报告文件: v7_hour_long_test_report.json"
    echo "=========================================="
    
    # 显示关键统计
    echo ""
    echo "关键统计信息:"
    cat v7_hour_long_test_report.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('  总操作数:', data['operations']['total'])
print('  成功率:', '{:.2f}%'.format(100 * data['operations']['success'] / max(data['operations']['total'], 1)))
print('  失败数:', data['operations']['failure'])
print('  最终节点数:', data['final_stats']['nodes'])
print('  最终边数:', data['final_stats']['edges'])
print('  测试时长:', '{:.2f}分钟'.format(data['duration'] / 60))
print('  测试状态:', '成功' if data['success'] else '有问题')
"
else
    echo "警告：报告文件未生成"
fi

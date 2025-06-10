#!/usr/bin/env python3
"""
交易记录详情验证脚本

展示如何查看指定币种的所有交易记录详情，便于用户核对数据
"""

import subprocess
import sys

def run_command(cmd):
    """运行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"执行命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ 命令执行失败: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 命令执行异常: {e}")
        return False

def main():
    print("🔍 交易记录详情验证工具")
    print("="*60)
    print("使用 --details 选项查看币种的所有交易记录详情")
    print("这对于核对数据和验证计算结果非常有用")
    
    # 演示查看不同币种的详细记录
    commands = [
        "python main.py currency XRP --details",
        "python main.py currency BTC --details", 
        "python main.py currency DOGE --details"
    ]
    
    for cmd in commands:
        success = run_command(cmd)
        if not success:
            print(f"⚠️  命令失败: {cmd}")
    
    print("\n" + "="*60)
    print("📋 功能说明:")
    print("✅ 使用 'python main.py currency <币种>' 查看汇总分析")
    print("✅ 使用 'python main.py currency <币种> --details' 查看所有交易记录")
    print("✅ 详情包括：时间、交易对、买卖方向、数量、价格、金额、手续费、盈亏")
    print("✅ 底部显示汇总统计：买卖次数、总量、当前持仓、已实现盈亏")
    print("="*60)

if __name__ == "__main__":
    main() 
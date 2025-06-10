#!/usr/bin/env python3
"""
演示所有新功能的脚本
包括稳定币标准化、币种分析等
"""

import subprocess
import sys

def run_command(cmd):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"执行命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"执行命令时发生错误: {e}")
        return False

def main():
    """演示所有功能"""
    print("🎯 交易日志CLI工具 - 完整功能演示")
    print("=" * 60)
    
    # 1. 查看帮助
    run_command("python main.py --help")
    
    # 2. 查看所有币种列表
    run_command("python main.py list-currencies")
    
    # 3. 查看整体报告
    run_command("python main.py report")
    
    # 4. 查看XRP详细分析
    run_command("python main.py currency XRP")
    
    # 5. 查看BTC详细分析
    run_command("python main.py currency BTC")
    
    # 6. 查看特定交易对报告
    run_command("python main.py report --symbol BTCUSDT")
    
    # 7. 查看最近交易报告
    run_command("python main.py report --days 30")
    
    print("\n" + "🎉" * 20)
    print("功能演示完成！")
    print("🎉" * 20)
    
    print("\n📋 功能总结:")
    print("✅ 稳定币自动标准化 (FDUSD→USDT, USDC→USDT等)")
    print("✅ 中英文Excel文件支持")
    print("✅ 按币种查看净盈亏分析")
    print("✅ 币种列表展示")
    print("✅ 加权平均成本法计算PnL")
    print("✅ 灵活的报告筛选功能")
    print("✅ 自动重复交易检测")
    
    print("\n💡 主要解决的问题:")
    print("• 跨稳定币交易计算错误 (用FDUSD买入→USDT卖出)")
    print("• 手动计算PnL的繁琐性")
    print("• 缺乏币种维度的分析视角")
    print("• Excel文件语言兼容性问题")

if __name__ == "__main__":
    main() 
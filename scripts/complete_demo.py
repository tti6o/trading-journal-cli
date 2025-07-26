#!/usr/bin/env python3
"""
完整的技术分析演示脚本

展示RSI和斐波那契分析的完整功能，包括：
1. 单个交易对分析
2. 市场批量分析
3. 图表生成
4. 综合报告
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.technical_analysis import MarketAnalyzer, FibonacciAnalyzer, RsiAnalyzer
from services.chart_generator import ChartGenerator
from common.utilities import setup_logging

def generate_comprehensive_test_data(symbol: str = "BTCUSDT", days: int = 100) -> pd.DataFrame:
    """
    生成包含明显技术模式的综合测试数据
    
    Args:
        symbol: 交易对符号
        days: 数据天数
        
    Returns:
        测试数据DataFrame
    """
    print(f"🔧 生成 {symbol} 综合测试数据，{days} 天...")
    
    # 生成时间序列
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days, freq='4H')
    
    # 创建一个有明显趋势和回调的价格序列
    base_price = 45000
    
    # 主要趋势：分段上升
    trend_phases = []
    phase_length = days // 4
    
    # 第一段：上升趋势
    trend_phases.extend(np.linspace(0, 8000, phase_length))
    # 第二段：回调
    trend_phases.extend(np.linspace(8000, 5000, phase_length))
    # 第三段：强势上升
    trend_phases.extend(np.linspace(5000, 15000, phase_length))
    # 第四段：整理
    trend_phases.extend(np.linspace(15000, 12000, days - 3 * phase_length))
    
    # 添加噪音和波动
    noise = np.random.normal(0, 300, days)
    
    # 添加明显的摆动高低点
    swing_adjustments = np.zeros(days)
    
    # 在关键位置添加明显的高低点
    key_points = [days//6, days//3, days//2, 2*days//3, 5*days//6]
    adjustments = [2000, -1500, 3000, -1000, 1500]
    
    for point, adj in zip(key_points, adjustments):
        if point < days:
            swing_adjustments[point] = adj
    
    # 生成收盘价
    close_prices = base_price + np.array(trend_phases) + noise + swing_adjustments
    
    # 生成OHLCV数据
    data = []
    for i in range(days):
        close = close_prices[i]
        
        # 生成开盘、最高、最低价格
        daily_range = abs(np.random.normal(0, 200))
        open_price = close + np.random.normal(0, 100)
        high = max(open_price, close) + daily_range * np.random.random()
        low = min(open_price, close) - daily_range * np.random.random()
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'date': dates[i],
            'open': max(1000, open_price),  # 确保价格为正
            'high': max(1000, high),
            'low': max(500, low),
            'close': max(1000, close),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    
    print(f"✅ 综合测试数据生成完成")
    print(f"   价格范围: {df['low'].min():.2f} - {df['high'].max():.2f}")
    print(f"   最新收盘价: {df['close'].iloc[-1]:.2f}")
    print(f"   总波动率: {(df['high'].max() - df['low'].min()) / df['close'].mean() * 100:.1f}%")
    
    return df

def demo_single_symbol_analysis():
    """演示单个交易对的完整技术分析"""
    print("\n🔍 单个交易对完整技术分析演示")
    print("=" * 60)
    
    # 生成测试数据
    test_data = generate_comprehensive_test_data("BTCUSDT", days=120)
    
    # 1. RSI分析
    print("\n📊 RSI分析:")
    rsi_analyzer = RsiAnalyzer(rsi_period=14, oversold=30, overbought=70)
    rsi_signal = rsi_analyzer.analyze("BTCUSDT", test_data)
    
    if rsi_signal:
        print(f"  信号类型: {rsi_signal.signal_type}")
        print(f"  RSI值: {rsi_signal.rsi_value:.1f}")
        print(f"  置信度: {rsi_signal.confidence:.2f}")
        print(f"  分析: {rsi_signal.message}")
    else:
        print("  未生成RSI信号")
    
    # 2. 斐波那契分析
    print("\n📈 斐波那契分析:")
    fib_analyzer = FibonacciAnalyzer(
        lookback_period=15,
        min_price_change_pct=0.03,
        proximity_threshold_pct=0.02
    )
    fib_signals = fib_analyzer.analyze("BTCUSDT", test_data)
    
    if fib_signals:
        print(f"  发现 {len(fib_signals)} 个斐波那契信号:")
        for i, signal in enumerate(fib_signals, 1):
            print(f"    信号 {i}:")
            print(f"      类型: {signal.fib_type}")
            print(f"      水平: {signal.fib_level:.3f} ({signal.fib_level*100:.1f}%)")
            print(f"      目标价: {signal.fib_price:.2f}")
            print(f"      信号: {signal.signal_type}")
            print(f"      置信度: {signal.confidence:.2f}")
            print(f"      分析: {signal.message}")
    else:
        print("  未生成斐波那契信号")
    
    # 3. 生成图表
    print("\n🎨 生成技术分析图表:")
    chart_gen = ChartGenerator()
    output_file = os.path.join(os.path.dirname(__file__), '..', 'user_data', 'complete_analysis_demo.png')
    
    chart_gen.generate_fibonacci_chart(
        df=test_data,
        symbol="BTCUSDT",
        timeframe="4h",
        fib_analyzer=fib_analyzer,
        output_path=output_file
    )
    
    return test_data, rsi_signal, fib_signals

def demo_market_analysis():
    """演示市场批量分析功能"""
    print("\n🌍 市场批量分析演示")
    print("=" * 60)
    
    # 准备多个交易对的测试数据
    market_data = {}
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
    
    for symbol in symbols:
        print(f"生成 {symbol} 数据...")
        market_data[symbol] = generate_comprehensive_test_data(symbol, days=80)
    
    # 配置市场分析器
    config = {
        'rsi': {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        },
        'fibonacci': {
            'lookback_period': 12,
            'min_price_change_pct': 0.04,
            'proximity_threshold_pct': 0.025
        }
    }
    
    # 执行市场分析
    market_analyzer = MarketAnalyzer(config)
    all_signals = market_analyzer.analyze_market(market_data)
    
    # 生成市场摘要
    market_summary = market_analyzer.get_market_summary(all_signals)
    
    # 显示结果
    print(f"\n📊 市场分析结果:")
    print(f"  分析交易对数: {market_summary['total_symbols']}")
    print(f"  总信号数: {market_summary['total_signals']}")
    print(f"  买入信号: {market_summary['buy_signals']}")
    print(f"  卖出信号: {market_summary['sell_signals']}")
    print(f"  中性信号: {market_summary['neutral_signals']}")
    print(f"  高置信度信号: {market_summary['high_confidence_signals']}")
    print(f"  市场情绪: {market_summary['market_sentiment']}")
    
    print(f"\n📈 RSI分析统计:")
    print(f"  RSI信号数: {market_summary['rsi_analysis']['count']}")
    print(f"  平均RSI: {market_summary['rsi_analysis']['avg_rsi']:.1f}")
    
    print(f"\n🌊 斐波那契分析统计:")
    print(f"  斐波那契信号数: {market_summary['fibonacci_analysis']['count']}")
    print(f"  回调信号: {market_summary['fibonacci_analysis']['retracement_count']}")
    print(f"  扩展信号: {market_summary['fibonacci_analysis']['extension_count']}")
    
    # 详细信号列表
    print(f"\n📋 各交易对详细信号:")
    for symbol, signals in all_signals.items():
        print(f"\n{symbol} ({len(signals)} 个信号):")
        for signal in signals:
            indicator_info = f"RSI({signal.rsi_value:.1f})" if signal.indicator_type == 'RSI' else f"FIB({signal.fib_level:.1%})"
            print(f"  └ {signal.signal_type} - {indicator_info} - 置信度:{signal.confidence:.2f}")
            print(f"    {signal.message}")
    
    return all_signals, market_summary

def demo_advanced_features():
    """演示高级功能"""
    print("\n🚀 高级功能演示")
    print("=" * 60)
    
    # 生成复杂的测试数据
    complex_data = generate_comprehensive_test_data("COMPLEXUSDT", days=150)
    
    # 高级斐波那契分析（更敏感的参数）
    advanced_fib = FibonacciAnalyzer(
        lookback_period=10,
        min_price_change_pct=0.02,
        proximity_threshold_pct=0.03
    )
    
    signals = advanced_fib.analyze("COMPLEXUSDT", complex_data)
    
    if signals:
        print(f"🎯 高级分析发现 {len(signals)} 个信号:")
        
        # 按置信度分组
        high_conf = [s for s in signals if s.confidence >= 0.7]
        medium_conf = [s for s in signals if 0.4 <= s.confidence < 0.7]
        low_conf = [s for s in signals if s.confidence < 0.4]
        
        print(f"  高置信度信号 (≥70%): {len(high_conf)}")
        print(f"  中等置信度信号 (40%-70%): {len(medium_conf)}")
        print(f"  低置信度信号 (<40%): {len(low_conf)}")
        
        # 显示最高置信度的信号
        if high_conf:
            best_signal = max(high_conf, key=lambda s: s.confidence)
            print(f"\n🏆 最佳信号:")
            print(f"    类型: {best_signal.fib_type}")
            print(f"    水平: {best_signal.fib_level:.1%}")
            print(f"    信号: {best_signal.signal_type}")
            print(f"    置信度: {best_signal.confidence:.2%}")
            print(f"    分析: {best_signal.message}")
    else:
        print("⚠️ 高级分析未发现信号")

def main():
    """主演示函数"""
    print("🚀 完整技术分析系统演示")
    print("=" * 80)
    
    setup_logging()
    
    try:
        # 1. 单个交易对分析
        single_data, rsi_sig, fib_sigs = demo_single_symbol_analysis()
        
        # 2. 市场批量分析
        market_signals, market_sum = demo_market_analysis()
        
        # 3. 高级功能演示
        demo_advanced_features()
        
        # 4. 总结
        print(f"\n🎉 演示完成总结:")
        print(f"  单个分析 - RSI信号: {'✅' if rsi_sig else '❌'}")
        print(f"  单个分析 - 斐波那契信号: {'✅' if fib_sigs else '❌'} ({len(fib_sigs) if fib_sigs else 0}个)")
        print(f"  市场分析 - 总信号数: {market_sum.get('total_signals', 0)}")
        print(f"  市场情绪: {market_sum.get('market_sentiment', 'UNKNOWN')}")
        print(f"  图表生成: ✅")
        
        print(f"\n📁 生成的文件:")
        print(f"  完整分析图表: user_data/complete_analysis_demo.png")
        print(f"  原始演示图表: user_data/fib_chart_final_demo.png")
        
        print(f"\n✨ 技术分析系统完整实现成功！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
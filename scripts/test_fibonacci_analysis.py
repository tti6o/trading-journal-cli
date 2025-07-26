#!/usr/bin/env python3
"""
斐波那契技术分析测试脚本

测试新实现的斐波那契回调和扩展线分析功能
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.technical_analysis import FibonacciAnalyzer, MarketAnalyzer, TechnicalSignal
from common.utilities import setup_logging

def generate_test_data(symbol: str = "BTCUSDT", days: int = 100) -> pd.DataFrame:
    """
    生成测试用的OHLCV数据，包含明显的趋势和回调
    
    Args:
        symbol: 交易对符号
        days: 数据天数
        
    Returns:
        测试数据DataFrame
    """
    print(f"🔧 生成 {symbol} 测试数据，{days} 天...")
    
    # 生成时间序列
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days, freq='1H')
    
    # 创建一个有趋势的价格序列
    base_price = 45000
    trend = np.linspace(0, 10000, days)  # 上升趋势
    noise = np.random.normal(0, 500, days)  # 随机噪音
    
    # 添加一些明显的高低点
    swing_points = np.zeros(days)
    swing_points[days//4] = 3000      # 早期高点
    swing_points[days//2] = -2000     # 中期低点  
    swing_points[3*days//4] = 4000    # 后期高点
    
    # 生成收盘价
    close_prices = base_price + trend + noise + swing_points
    
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
            'timestamp': dates[i],
            'open': max(100, open_price),  # 确保价格为正
            'high': max(100, high),
            'low': max(50, low),
            'close': max(100, close),
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    print(f"✅ 测试数据生成完成")
    print(f"   价格范围: {df['low'].min():.2f} - {df['high'].max():.2f}")
    print(f"   最新收盘价: {df['close'].iloc[-1]:.2f}")
    
    return df

def test_fibonacci_analyzer():
    """测试斐波那契分析器的基本功能"""
    print("\n🧪 测试斐波那契分析器...")
    print("=" * 50)
    
    # 1. 初始化分析器
    fib_analyzer = FibonacciAnalyzer(
        lookback_period=15,  # 较小的周期便于测试
        min_price_change_pct=0.03,  # 3%的价格变化
        proximity_threshold_pct=0.015  # 1.5%的接近阈值
    )
    
    # 2. 生成测试数据
    test_data = generate_test_data("TESTUSDT", days=80)
    
    # 3. 执行分析
    signals = fib_analyzer.analyze("TESTUSDT", test_data)
    
    # 4. 显示结果
    if signals:
        print(f"🎯 发现 {len(signals)} 个斐波那契信号:")
        for i, signal in enumerate(signals, 1):
            print(f"\n信号 {i}:")
            print(f"  类型: {signal.signal_type}")
            print(f"  指标: {signal.indicator_type}")
            print(f"  斐波那契类型: {signal.fib_type}")
            print(f"  水平: {signal.fib_level:.3f} ({signal.fib_level*100:.1f}%)")
            print(f"  目标价格: {signal.fib_price:.2f}")
            print(f"  当前价格: {signal.price:.2f}")
            print(f"  趋势方向: {signal.trend_direction}")
            print(f"  置信度: {signal.confidence:.2f}")
            print(f"  消息: {signal.message}")
    else:
        print("⚠️ 未发现斐波那契信号")
    
    return signals

def test_market_analyzer_integration():
    """测试MarketAnalyzer的集成功能"""
    print("\n🔄 测试MarketAnalyzer集成...")
    print("=" * 50)
    
    # 1. 初始化市场分析器
    config = {
        'rsi': {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        },
        'fibonacci': {
            'lookback_period': 20,
            'min_price_change_pct': 0.04,
            'proximity_threshold_pct': 0.02
        }
    }
    
    market_analyzer = MarketAnalyzer(config)
    
    # 2. 准备多个交易对的测试数据
    market_data = {
        'BTCUSDT': generate_test_data('BTCUSDT', days=90),
        'ETHUSDT': generate_test_data('ETHUSDT', days=85),
        'ADAUSDT': generate_test_data('ADAUSDT', days=95),
    }
    
    # 3. 执行市场分析
    all_signals = market_analyzer.analyze_market(market_data)
    
    # 4. 生成市场摘要
    market_summary = market_analyzer.get_market_summary(all_signals)
    
    # 5. 显示结果
    print(f"📊 市场分析结果:")
    print(f"  总交易对数: {market_summary['total_symbols']}")
    print(f"  总信号数: {market_summary['total_signals']}")
    print(f"  买入信号: {market_summary['buy_signals']}")
    print(f"  卖出信号: {market_summary['sell_signals']}")
    print(f"  中性信号: {market_summary['neutral_signals']}")
    print(f"  RSI分析: {market_summary['rsi_analysis']['count']} 个信号")
    print(f"  平均RSI: {market_summary['rsi_analysis']['avg_rsi']:.1f}")
    print(f"  斐波那契分析: {market_summary['fibonacci_analysis']['count']} 个信号")
    print(f"    回调信号: {market_summary['fibonacci_analysis']['retracement_count']}")
    print(f"    扩展信号: {market_summary['fibonacci_analysis']['extension_count']}")
    print(f"  高置信度信号: {market_summary['high_confidence_signals']}")
    print(f"  市场情绪: {market_summary['market_sentiment']}")
    
    # 6. 详细信号列表
    if all_signals:
        print(f"\n📋 详细信号列表:")
        for symbol, signals in all_signals.items():
            print(f"\n{symbol} ({len(signals)} 个信号):")
            for signal in signals:
                indicator_info = f"RSI({signal.rsi_value:.1f})" if signal.indicator_type == 'RSI' else f"FIB({signal.fib_level:.1f}%)"
                print(f"  └ {signal.signal_type} - {indicator_info} - 置信度:{signal.confidence:.2f}")
                print(f"    {signal.message}")
    else:
        print("\n⚠️ 未发现任何信号")
    
    return all_signals, market_summary

def test_signal_quality():
    """测试信号质量和准确性"""
    print("\n🎯 测试信号质量...")
    print("=" * 50)
    
    # 创建一个有明显斐波那契模式的数据
    prices = [100, 120, 115, 140, 125, 160, 135, 180, 150, 200]  # 明显的锯齿上升
    
    # 构造DataFrame
    dates = pd.date_range(start='2024-01-01', periods=len(prices), freq='1H')
    
    test_df = pd.DataFrame({
        'open': prices,
        'high': [p * 1.02 for p in prices],  # 高点稍高
        'low': [p * 0.98 for p in prices],   # 低点稍低
        'close': prices,
        'volume': [1000] * len(prices)
    }, index=dates)
    
    # 测试分析
    fib_analyzer = FibonacciAnalyzer(
        lookback_period=2,  # 很小的窗口期
        min_price_change_pct=0.05,
        proximity_threshold_pct=0.05  # 较宽的阈值
    )
    
    signals = fib_analyzer.analyze("QUALITYTEST", test_df)
    
    if signals:
        print(f"✅ 从构造数据中发现 {len(signals)} 个信号")
        for signal in signals:
            print(f"  {signal.signal_type} - {signal.fib_type} {signal.fib_level:.1%} at {signal.fib_price:.2f}")
    else:
        print("⚠️ 从构造数据中未发现信号")
    
    return signals

def main():
    """主测试函数"""
    print("🚀 斐波那契技术分析测试开始")
    print("=" * 60)
    
    setup_logging()
    
    try:
        # 1. 测试基础斐波那契分析器
        fib_signals = test_fibonacci_analyzer()
        
        # 2. 测试MarketAnalyzer集成
        market_signals, summary = test_market_analyzer_integration()
        
        # 3. 测试信号质量
        quality_signals = test_signal_quality()
        
        # 4. 总结
        print(f"\n🎉 测试完成总结:")
        print(f"  基础斐波那契信号: {len(fib_signals) if fib_signals else 0}")
        print(f"  市场分析总信号数: {summary.get('total_signals', 0)}")
        print(f"  信号质量测试: {'通过' if quality_signals else '需要调优'}")
        
        if summary.get('total_signals', 0) > 0:
            print(f"✅ 斐波那契分析功能基本正常!")
        else:
            print(f"⚠️ 可能需要调整参数或测试数据")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 
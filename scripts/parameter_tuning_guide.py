#!/usr/bin/env python3
"""
斐波那契参数调优指南

根据不同交易风格提供最佳参数配置建议
"""

def display_trading_styles():
    """展示不同交易风格的参数配置"""
    
    print("🎯 斐波那契分析 - 交易风格参数指南")
    print("=" * 60)
    
    configs = {
        "🔥 激进短线 (1-4小时)": {
            "lookback_period": 12,
            "min_price_change_pct": 0.02,
            "proximity_threshold_pct": 0.025,
            "analysis_interval_minutes": 15,
            "kline_interval": "15m",
            "特点": ["高灵敏度", "信号频繁", "需要快速响应"],
            "适合": ["职业交易员", "24小时监控", "小资金高频"]
        },
        
        "⚖️  稳健中线 (1-7天)": {
            "lookback_period": 20,
            "min_price_change_pct": 0.05,
            "proximity_threshold_pct": 0.02,
            "analysis_interval_minutes": 60,
            "kline_interval": "1h",
            "特点": ["平衡准确性与频率", "经典配置", "适中风险"],
            "适合": ["大多数交易者", "业余交易", "中等资金"]
        },
        
        "🏛️ 保守长线 (1-4周)": {
            "lookback_period": 30,
            "min_price_change_pct": 0.08,
            "proximity_threshold_pct": 0.015,
            "analysis_interval_minutes": 240,
            "kline_interval": "4h",
            "特点": ["高准确性", "信号稀少", "长期持有"],
            "适合": ["价值投资者", "大资金", "低频交易"]
        },
        
        "🧪 实验配置 (测试用)": {
            "lookback_period": 15,
            "min_price_change_pct": 0.03,
            "proximity_threshold_pct": 0.03,
            "analysis_interval_minutes": 30,
            "kline_interval": "1h",
            "特点": ["高信号频率", "用于测试", "学习观察"],
            "适合": ["新手练习", "策略回测", "参数测试"]
        }
    }
    
    for style, config in configs.items():
        print(f"\n{style}")
        print("-" * 40)
        print(f"📐 回看周期: {config['lookback_period']}")
        print(f"🎚️  价格变化阈值: {config['min_price_change_pct']*100:.1f}%")
        print(f"🎯 接近度阈值: {config['proximity_threshold_pct']*100:.1f}%")
        print(f"⏰ 分析间隔: {config['analysis_interval_minutes']}分钟")
        print(f"📊 K线周期: {config['kline_interval']}")
        print(f"✨ 特点: {', '.join(config['特点'])}")
        print(f"👥 适合: {', '.join(config['适合'])}")

def show_parameter_effects():
    """展示参数变化的实际效果"""
    
    print("\n\n🔬 参数效果实验室")
    print("=" * 60)
    
    # 模拟市场情况
    scenarios = [
        {"name": "🚀 强势突破", "high": 52000, "low": 45000, "current": 51800},
        {"name": "📉 深度回调", "high": 50000, "low": 40000, "current": 43000},
        {"name": "⚖️ 震荡整理", "high": 48000, "low": 46000, "current": 46900},
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print(f"价格: ${scenario['high']:,} → ${scenario['low']:,} → ${scenario['current']:,}")
        
        # 计算61.8%回调位
        price_range = scenario['high'] - scenario['low']
        fib_618 = scenario['low'] + price_range * 0.618
        proximity = abs(scenario['current'] - fib_618) / scenario['current']
        
        print(f"61.8%回调位: ${fib_618:,.0f}")
        print(f"当前距离: {proximity*100:.1f}%")
        
        # 不同阈值的触发情况
        thresholds = [0.01, 0.02, 0.03, 0.05]
        print("触发情况:", end="")
        for threshold in thresholds:
            status = "✅" if proximity <= threshold else "❌"
            print(f" {threshold*100:.0f}%{status}", end="")
        print()

def recommend_config():
    """推荐配置"""
    
    print("\n\n💡 智能配置推荐")
    print("=" * 60)
    
    print("🥇 最佳新手配置 (推荐):")
    print("""
    [fibonacci]
    enabled = true
    lookback_period = 20
    min_price_change_pct = 0.05  
    proximity_threshold_pct = 0.025
    
    [technical_analysis]
    analysis_interval_minutes = 60
    kline_interval = 1h
    """)
    
    print("📈 配置理由:")
    print("• lookback_period=20: 经典周期，兼顾主趋势和灵敏度")
    print("• min_price_change_pct=5%: 过滤噪音，保留有效信号")
    print("• proximity_threshold_pct=2.5%: 稍宽松，不错过机会")
    print("• 60分钟间隔: 及时响应，不会过于频繁")
    
    print("\n🔧 进阶调优建议:")
    print("• 牛市: 适当降低min_price_change_pct (0.03-0.04)")
    print("• 熊市: 适当提高proximity_threshold_pct (0.03-0.04)")  
    print("• 高波动: 增加lookback_period (25-30)")
    print("• 低波动: 减少lookback_period (15-18)")

if __name__ == "__main__":
    display_trading_styles()
    show_parameter_effects()
    recommend_config() 
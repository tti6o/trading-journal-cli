import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import os
from typing import List, Dict, Optional

from services.technical_analysis import FibonacciAnalyzer, TechnicalSignal

# 解决中文乱码问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class ChartGenerator:
    """
    负责生成包含技术分析的K线图
    """
    def __init__(self):
        """
        初始化图表生成器
        """
        pass

    def generate_fibonacci_chart(self, df: pd.DataFrame, symbol: str, timeframe: str,
                                 fib_analyzer, output_path: str):
        """
        生成斐波那契技术分析图表 (简化版本)
        
        Args:
            df: OHLCV数据
            symbol: 交易对符号
            timeframe: 时间框架
            fib_analyzer: 斐波那契分析器实例
            output_path: 输出路径
        """
        try:
            # 获取斐波那契分析信号
            signals = fib_analyzer.analyze(symbol, df.copy())
            
            if not signals:
                print(f"❌ 在 {symbol} 数据中未找到足够的斐波那契信号进行绘图。")
                return

            # 准备绘图数据 - 使用最近150个数据点
            plot_df = df.tail(150).copy()
            plot_title = f"{symbol} Technical Analysis (RSI + Fibonacci) - {timeframe}"
            
            # 从信号中提取斐波那契线
            fib_levels = []
            
            for signal in signals:
                if signal.indicator_type == 'FIBONACCI' and signal.fib_price:
                    fib_levels.append({
                        'level': f"{signal.fib_level*100:.1f}% {signal.fib_type[:4]}",
                        'price': signal.fib_price,
                        'color': 'orange' if signal.fib_type == 'RETRACEMENT' else 'purple'
                    })

            # 简化的高低点标记 - 使用滚动极值
            window = 10
            plot_df['high_point'] = plot_df['high'].rolling(window=window, center=True).max() == plot_df['high']
            plot_df['low_point'] = plot_df['low'].rolling(window=window, center=True).min() == plot_df['low']
            
            # 创建标记数据
            high_marks = plot_df.loc[plot_df['high_point'], 'high']
            low_marks = plot_df.loc[plot_df['low_point'], 'low']
            
            # 限制标记数量以避免图表过于拥挤
            if len(high_marks) > 8:
                high_marks = high_marks.nlargest(8)
            if len(low_marks) > 8:
                low_marks = low_marks.nsmallest(8)

            swing_plots = []
            if not high_marks.empty:
                swing_plots.append(mpf.make_addplot(high_marks, type='scatter', marker='v', color='red', markersize=100))
            if not low_marks.empty:
                swing_plots.append(mpf.make_addplot(low_marks, type='scatter', marker='^', color='green', markersize=100))

            # 准备斐波那契水平线
            hlines = [level['price'] for level in fib_levels]
            hline_colors = [level['color'] for level in fib_levels]

            # 生成图表
            try:
                fig, axes = mpf.plot(
                    plot_df,
                    type='candle', 
                    style='yahoo', 
                    title=plot_title,
                    ylabel='Price', 
                    addplot=swing_plots if swing_plots else None,
                    hlines=dict(hlines=hlines, colors=hline_colors, linestyle='-.', linewidths=1.0) if hlines else None,
                    figsize=(16, 10), 
                    volume=True, 
                    panel_ratios=(3, 1), 
                    returnfig=True
                )

                ax = axes[0]
                
                # 在右侧显示斐波那契水平标签
                for level in fib_levels:
                    try:
                        ax.text(len(plot_df) * 1.02, level['price'], f" {level['level']} ({level['price']:.4f})", 
                                va='center', color=level['color'], fontsize=9, style='italic')
                    except:
                        continue

                plt.tight_layout()
                
                # 确保输出目录存在
                if not os.path.exists(os.path.dirname(output_path)):
                    os.makedirs(os.path.dirname(output_path))
                    
                fig.savefig(output_path, bbox_inches='tight', dpi=100)
                plt.close(fig)  # 释放内存
                
                print(f"✅ 图表已保存到: {output_path}")
                return output_path
                
            except Exception as plot_error:
                print(f"❌ 绘制图表时出错: {plot_error}")
                return None
                
        except Exception as e:
            print(f"❌ 生成斐波那契图表时出错: {e}")
            return None 
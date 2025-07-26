import sys
import os
import pandas as pd

# 临时解决路径问题
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.chart_generator import ChartGenerator
from services.technical_analysis import FibonacciAnalyzer

def run_demo():
    """
    运行图表生成演示
    """
    print("🚀 开始运行斐波那契图表生成演示...")
    
    # 使用本地备份数据
    local_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'XRPUSDT-4h.csv')
    if not os.path.exists(local_data_path):
        print(f"❌ 错误: 本地备份数据 {local_data_path} 未找到。")
        print("请先确保 'data/XRPUSDT-4h.csv' 文件存在。")
        return
        
    df = pd.read_csv(local_data_path)
    
    # 1. 创建分析器实例
    # 为了在小样本上演示，使用较小的回看周期
    fib_analyzer = FibonacciAnalyzer(
        lookback_period=3,  # 极小的回看周期，适合24条数据
        min_price_change_pct=0.01,  # 降低最小价格变化要求
        proximity_threshold_pct=0.05  # 放宽接近阈值
    )
    
    # 2. 创建图表生成器
    chart_gen = ChartGenerator()
    
    output_file = os.path.join(os.path.dirname(__file__), '..', 'user_data', 'fib_chart_final_demo.png')
    
    chart_gen.generate_fibonacci_chart(
        df=df,
        symbol="XRPUSDT",
        timeframe="4h",
        fib_analyzer=fib_analyzer,
        output_path=output_file
    )

if __name__ == "__main__":
    run_demo() 
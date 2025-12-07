"""
专业金融图表生成器 - 基于mplfinance

使用金融行业标准的mplfinance库：
- TradingView风格的专业K线图
- 内置金融指标支持
- 高质量图表输出
- 业界认可的样式
"""

import pandas as pd
import mplfinance as mpf
import tempfile
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, ContextManager
from contextlib import contextmanager
import numpy as np

logger = logging.getLogger(__name__)


class ProfessionalChartGenerator:
    """专业金融图表生成器 - 基于mplfinance"""

    def __init__(self):
        """初始化专业图表生成器"""
        # TradingView风格配色方案
        self.style = mpf.make_mpf_style(
            base_mpl_style='dark_background',
            marketcolors=mpf.make_marketcolors(
                up='#26a69a',      # 绿色阳线（TradingView风格）
                down='#ef5350',    # 红色阴线
                edge='inherit',
                wick={'up': '#26a69a', 'down': '#ef5350'},
                volume={'up': '#26a69a', 'down': '#ef5350'}
            ),
            gridcolor='#404040',
            facecolor='#1e1e1e',
            figcolor='#1e1e1e'
        )

    @contextmanager
    def generate_chart_file(self, symbol: str, df: pd.DataFrame,
                          analysis_result: Dict) -> ContextManager[str]:
        """
        生成专业图表临时文件 - TradingView风格

        Args:
            symbol: 交易对符号
            df: K线数据DataFrame
            analysis_result: 分析结果

        Yields:
            临时文件路径
        """
        temp_file = None
        try:
            if df.empty:
                logger.warning(f"空DataFrame，无法生成 {symbol} 图表")
                yield None
                return

            # 准备数据（最近50个数据点）
            plot_df = df.tail(50).copy()

            # 确保DataFrame索引是DatetimeIndex
            if not isinstance(plot_df.index, pd.DatetimeIndex):
                plot_df.index = pd.to_datetime(plot_df.index)

            # mplfinance需要特定的列名
            plot_df = plot_df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            # 生成有意义的文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_professional_chart_{timestamp}.png"

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.png',
                prefix=f'{symbol}_chart_',
                delete=False
            )

            # 计算技术指标
            rsi_values = self._calculate_rsi(plot_df['Close'])
            ma5 = plot_df['Close'].rolling(window=5).mean()
            ma10 = plot_df['Close'].rolling(window=10).mean()
            ma20 = plot_df['Close'].rolling(window=20).mean()

            # 准备附加图表
            apd = []

            # 添加移动平均线到主图 (panel=0)
            if len(ma5.dropna()) > 0:
                apd.append(mpf.make_addplot(ma5, panel=0, color='#00ff88', width=1.5, alpha=0.8))
            if len(ma10.dropna()) > 0:
                apd.append(mpf.make_addplot(ma10, panel=0, color='#ff9800', width=1.5, alpha=0.8))
            if len(ma20.dropna()) > 0:
                apd.append(mpf.make_addplot(ma20, panel=0, color='#9c27b0', width=1.5, alpha=0.8))

            # 添加RSI到下方面板 (panel=1)
            if len(rsi_values.dropna()) > 0:
                apd.append(mpf.make_addplot(rsi_values, panel=1, color='#ffb74d', width=2, ylabel='RSI'))

                # RSI超买超卖线
                rsi_overbought = pd.Series([70] * len(rsi_values), index=rsi_values.index)
                rsi_oversold = pd.Series([30] * len(rsi_values), index=rsi_values.index)
                rsi_middle = pd.Series([50] * len(rsi_values), index=rsi_values.index)

                apd.extend([
                    mpf.make_addplot(rsi_overbought, panel=1, color='#f44336',
                                   linestyle='--', alpha=0.7, width=1),
                    mpf.make_addplot(rsi_oversold, panel=1, color='#4caf50',
                                   linestyle='--', alpha=0.7, width=1),
                    mpf.make_addplot(rsi_middle, panel=1, color='#9e9e9e',
                                   linestyle='-', alpha=0.3, width=0.8)
                ])

            # 添加斐波那契水平线到主图 (panel=0)
            if analysis_result.get('high_confidence_fib'):
                for fib_signal in analysis_result['high_confidence_fib']:
                    if hasattr(fib_signal, 'price'):
                        fib_line = pd.Series([fib_signal.price] * len(plot_df), index=plot_df.index)
                        apd.append(
                            mpf.make_addplot(fib_line, panel=0, color='#42a5f5',
                                           linestyle='--', alpha=0.8, width=2)
                        )

            # 绘制专业K线图
            mpf.plot(
                plot_df,
                type='candle',
                style=self.style,
                volume=True,
                addplot=apd,
                title=f'{symbol} Professional Technical Analysis',
                ylabel='Price (USDT)',
                ylabel_lower='Volume',
                figsize=(12, 10),
                panel_ratios=(4, 1),  # 主图(K线+成交量):RSI = 4:1
                savefig=dict(
                    fname=temp_file.name,
                    dpi=150,
                    bbox_inches='tight',
                    facecolor='#1e1e1e'
                ),
                show_nontrading=False
            )

            # 关闭文件句柄
            temp_file.close()

            # 验证文件创建成功
            if os.path.exists(temp_file.name):
                file_size = os.path.getsize(temp_file.name)
                logger.info(f"✅ {symbol} 专业图表生成成功: {temp_file.name} ({file_size} bytes)")

                # 重命名为有意义的文件名
                final_path = os.path.join(os.path.dirname(temp_file.name), filename)
                os.rename(temp_file.name, final_path)

                yield final_path
            else:
                logger.error(f"❌ {symbol} 图表文件创建失败")
                yield None

        except Exception as e:
            logger.error(f"生成 {symbol} 专业图表失败: {e}")
            yield None

        finally:
            # 自动清理：确保临时文件被删除
            if temp_file:
                try:
                    # 删除原始临时文件（如果还存在）
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)

                    # 删除重命名后的文件（如果存在）
                    if 'final_path' in locals() and os.path.exists(final_path):
                        os.unlink(final_path)
                        logger.debug(f"🗑️ 已清理临时文件: {final_path}")

                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")

    def generate_batch_charts(self, analysis_results: List[Dict],
                            klines_data: Dict[str, pd.DataFrame]) -> List[str]:
        """
        批量生成专业图表文件

        Args:
            analysis_results: 分析结果列表
            klines_data: K线数据字典

        Returns:
            临时文件路径列表（调用方负责清理）
        """
        chart_paths = []

        for result in analysis_results:
            symbol = result['symbol']

            # 检查是否有K线数据
            if symbol not in klines_data:
                logger.warning(f"缺少 {symbol} 的K线数据")
                continue

            try:
                # 生成单个图表文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{symbol}_professional_chart_{timestamp}.png"

                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.png',
                    prefix=f'{symbol}_chart_',
                    delete=False
                )

                # 生成图表（复用上面的逻辑）
                if self._generate_single_chart(symbol, klines_data[symbol],
                                             result, temp_file.name):

                    # 重命名为有意义的文件名
                    final_path = os.path.join(os.path.dirname(temp_file.name), filename)
                    os.rename(temp_file.name, final_path)
                    chart_paths.append(final_path)

                    logger.info(f"✅ {symbol} 专业批量图表生成成功")
                else:
                    logger.warning(f"❌ {symbol} 专业批量图表生成失败")

                temp_file.close()

            except Exception as e:
                logger.error(f"生成 {symbol} 专业批量图表失败: {e}")

        logger.info(f"📊 专业批量生成完成: {len(chart_paths)} 个图表文件")
        return chart_paths

    def _generate_single_chart(self, symbol: str, df: pd.DataFrame,
                             analysis_result: Dict, output_path: str) -> bool:
        """生成单个专业图表到指定路径"""
        try:
            if df.empty:
                return False

            # 准备数据
            plot_df = df.tail(50).copy()

            # 确保DataFrame索引是DatetimeIndex
            if not isinstance(plot_df.index, pd.DatetimeIndex):
                plot_df.index = pd.to_datetime(plot_df.index)

            # 重命名列
            plot_df = plot_df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })

            # 计算技术指标
            rsi_values = self._calculate_rsi(plot_df['Close'])
            ma5 = plot_df['Close'].rolling(window=5).mean()
            ma10 = plot_df['Close'].rolling(window=10).mean()
            ma20 = plot_df['Close'].rolling(window=20).mean()

            # 准备附加图表
            apd = []

            # 添加移动平均线到主图 (panel=0)
            if len(ma5.dropna()) > 0:
                apd.append(mpf.make_addplot(ma5, panel=0, color='#00ff88', width=1.5, alpha=0.8))
            if len(ma10.dropna()) > 0:
                apd.append(mpf.make_addplot(ma10, panel=0, color='#ff9800', width=1.5, alpha=0.8))
            if len(ma20.dropna()) > 0:
                apd.append(mpf.make_addplot(ma20, panel=0, color='#9c27b0', width=1.5, alpha=0.8))

            # 添加RSI到下方面板 (panel=1)
            if len(rsi_values.dropna()) > 0:
                apd.append(mpf.make_addplot(rsi_values, panel=1, color='#ffb74d', width=2, ylabel='RSI'))

                # RSI超买超卖线
                rsi_overbought = pd.Series([70] * len(rsi_values), index=rsi_values.index)
                rsi_oversold = pd.Series([30] * len(rsi_values), index=rsi_values.index)
                rsi_middle = pd.Series([50] * len(rsi_values), index=rsi_values.index)

                apd.extend([
                    mpf.make_addplot(rsi_overbought, panel=1, color='#f44336',
                                   linestyle='--', alpha=0.7, width=1),
                    mpf.make_addplot(rsi_oversold, panel=1, color='#4caf50',
                                   linestyle='--', alpha=0.7, width=1),
                    mpf.make_addplot(rsi_middle, panel=1, color='#9e9e9e',
                                   linestyle='-', alpha=0.3, width=0.8)
                ])

            # 添加斐波那契水平线到主图 (panel=0)
            if analysis_result.get('high_confidence_fib'):
                for fib_signal in analysis_result['high_confidence_fib']:
                    if hasattr(fib_signal, 'price'):
                        fib_line = pd.Series([fib_signal.price] * len(plot_df), index=plot_df.index)
                        apd.append(
                            mpf.make_addplot(fib_line, panel=0, color='#42a5f5',
                                           linestyle='--', alpha=0.8, width=2)
                        )

            # 绘制图表
            mpf.plot(
                plot_df,
                type='candle',
                style=self.style,
                volume=True,
                addplot=apd,
                title=f'{symbol} Professional Technical Analysis',
                ylabel='Price (USDT)',
                ylabel_lower='Volume',
                figsize=(12, 10),
                panel_ratios=(4, 1),  # 主图(K线+成交量):RSI = 4:1
                savefig=dict(
                    fname=output_path,
                    dpi=150,
                    bbox_inches='tight',
                    facecolor='#1e1e1e'
                ),
                show_nontrading=False
            )

            return os.path.exists(output_path)

        except Exception as e:
            logger.error(f"生成专业单个图表失败: {e}")
            return False

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.fillna(50)

        except Exception as e:
            logger.warning(f"RSI计算失败: {e}")
            return pd.Series([50] * len(prices), index=prices.index)

    @staticmethod
    def cleanup_chart_files(file_paths: List[str]) -> None:
        """清理图表文件列表"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"🗑️ 已清理: {file_path}")
            except Exception as e:
                logger.warning(f"清理文件失败 {file_path}: {e}")


# 单例模式
_professional_chart_generator = None

def get_professional_chart_generator() -> ProfessionalChartGenerator:
    """获取专业图表生成器实例"""
    global _professional_chart_generator
    if _professional_chart_generator is None:
        _professional_chart_generator = ProfessionalChartGenerator()
    return _professional_chart_generator
"""
简化邮件服务 - 使用yagmail框架

替换原来复杂的notification.py，使用成熟的yagmail库
- 代码量减少80%
- 自动处理附件
- 更好的错误处理
- 支持HTML/文本自动识别
"""

import yagmail
import configparser
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SimpleEmailService:
    """简化的邮件服务 - 基于yagmail"""

    def __init__(self, config_file: str = 'config/config.ini'):
        """初始化邮件服务"""
        self.config_file = config_file
        self.enabled = False
        self.yag = None
        self.recipients = []

        # 加载配置
        self._load_config()

        # 初始化连接
        if self.enabled:
            self._init_connection()

    def _load_config(self) -> None:
        """加载邮件配置"""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')

            if not config.has_section('email'):
                logger.warning("邮件配置节未找到")
                return

            self.enabled = config.getboolean('email', 'enabled', fallback=False)

            if self.enabled:
                self.username = config.get('email', 'username')
                self.password = config.get('email', 'password')
                self.smtp_server = config.get('email', 'smtp_server', fallback='smtp.qq.com')
                self.smtp_port = config.getint('email', 'smtp_port', fallback=465)
                self.sender_name = config.get('email', 'sender_name', fallback='交易分析助手')

                # 加载收件人列表
                if config.has_section('technical_analysis'):
                    recipients_str = config.get('technical_analysis', 'notification_recipients', fallback='')
                    if recipients_str:
                        self.recipients = [r.strip() for r in recipients_str.split(',') if r.strip()]

                logger.info(f"邮件服务配置已加载: enabled={self.enabled}, recipients={len(self.recipients)}")

        except Exception as e:
            logger.error(f"加载邮件配置失败: {e}")
            self.enabled = False

    def _init_connection(self) -> None:
        """初始化yagmail连接"""
        try:
            self.yag = yagmail.SMTP(
                user=self.username,
                password=self.password,
                host=self.smtp_server,
                port=self.smtp_port,
                smtp_ssl=True if self.smtp_port == 465 else False
            )
            logger.info("yagmail连接已建立")

        except Exception as e:
            logger.error(f"初始化邮件连接失败: {e}")
            self.enabled = False
            self.yag = None

    def send_test_email(self, recipient: Optional[str] = None) -> bool:
        """发送测试邮件"""
        if not self.enabled or not self.yag:
            logger.warning("邮件服务未启用或连接失败")
            return False

        recipient = recipient or self.username

        try:
            test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            self.yag.send(
                to=recipient,
                subject=f'交易日志系统 - 邮件功能测试 [{test_time}]',
                contents=[
                    '<div style="font-family: Arial; padding: 20px;">',
                    '<div style="background: #e8f5e8; padding: 15px; border-radius: 5px;">',
                    '<h2 style="color: #2c5e2c;">✅ 邮件功能测试成功</h2>',
                    '<p>如果您收到这封邮件，说明邮件通知功能正常工作！</p>',
                    '</div>',
                    f'<p><strong>测试时间:</strong> {test_time}</p>',
                    f'<p><strong>收件人:</strong> {recipient}</p>',
                    f'<p><strong>邮件框架:</strong> yagmail (简化版)</p>',
                    '<hr>',
                    '<p><em>这是一封自动生成的测试邮件，无需回复。</em></p>',
                    '</div>'
                ]
            )

            logger.info(f"测试邮件发送成功: {recipient}")
            return True

        except Exception as e:
            logger.error(f"测试邮件发送失败: {e}")
            return False

    def send_signal_notification(self, signals: List[Any], recipient: str) -> bool:
        """发送技术分析信号通知（纯文本版本）"""
        if not self.enabled or not self.yag:
            logger.warning("邮件服务未启用")
            return False

        try:
            # 生成邮件内容
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            subject = f'技术分析信号提醒 (RSI+斐波那契) - {timestamp}'

            # 构建HTML内容
            html_content = self._build_signal_html(signals, timestamp)
            html_string = ''.join(html_content)  # 转换为字符串

            # 发送邮件
            send_args = {
                'to': recipient,
                'subject': subject,
                'contents': html_string
            }

            self.yag.send(**send_args)

            logger.info(f"技术分析信号邮件发送成功: {recipient} ({len(signals)}个信号)")
            return True

        except Exception as e:
            logger.error(f"信号通知邮件发送失败: {e}")
            return False

    def send_signal_notification_with_files(self, signals: List[Any], recipient: str,
                                          chart_files: Optional[List[str]] = None) -> bool:
        """发送技术分析信号通知（主流文件附件方案）"""
        if not self.enabled or not self.yag:
            logger.warning("邮件服务未启用")
            return False

        try:
            # 生成邮件内容
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            subject = f'技术分析信号提醒 (RSI+斐波那契) - {timestamp}'

            # 构建HTML内容
            html_content = self._build_signal_html(signals, timestamp)
            html_string = ''.join(html_content)  # 转换为字符串

            # 发送邮件
            send_args = {
                'to': recipient,
                'subject': subject,
                'contents': html_string
            }

            # 添加文件附件
            if chart_files:
                # yagmail 支持文件路径列表作为附件
                send_args['attachments'] = chart_files
                logger.info(f"邮件包含 {len(chart_files)} 个图表附件(文件)")

            self.yag.send(**send_args)

            logger.info(f"技术分析信号邮件发送成功: {recipient} ({len(signals)}个信号)")
            return True

        except Exception as e:
            logger.error(f"信号通知邮件发送失败: {e}")
            return False

    def _build_signal_html(self, signals: List[Any], timestamp: str) -> List[str]:
        """构建信号邮件HTML内容"""

        # 统计信号类型
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']

        html_parts = [
            '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">',

            # 头部
            '<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">',
            '<h1 style="margin: 0; font-size: 24px;">📈 技术分析信号提醒</h1>',
            f'<p style="margin: 5px 0 0 0; opacity: 0.9;">RSI + 斐波那契综合分析 | {timestamp}</p>',
            '</div>',

            # 信号概览
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">',
            '<h3 style="margin-top: 0; color: #333;">📊 信号概览</h3>',
            f'<p>🟢 <strong>买入信号:</strong> {len(buy_signals)} 个</p>',
            f'<p>🔴 <strong>卖出信号:</strong> {len(sell_signals)} 个</p>',
            f'<p>📈 <strong>总信号数:</strong> {len(signals)} 个</p>',
            '</div>',

            # 详细信号
            '<div style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px;">',
            '<h3 style="margin-top: 0; color: #333;">🎯 详细信号</h3>'
        ]

        # 添加每个信号的详细信息
        for i, signal in enumerate(signals, 1):
            signal_color = '#28a745' if signal.signal_type == 'BUY' else '#dc3545'
            html_parts.extend([
                f'<div style="border-left: 4px solid {signal_color}; padding: 10px; margin: 10px 0; background: #f8f9fa;">',
                f'<h4 style="margin: 0 0 5px 0; color: {signal_color};">{i}. {signal.symbol} - {signal.signal_type}</h4>',
                f'<p style="margin: 5px 0;"><strong>价格:</strong> ${signal.price:.4f}</p>',
                f'<p style="margin: 5px 0;"><strong>信号描述:</strong> {signal.message}</p>',
                f'<p style="margin: 5px 0;"><strong>时间:</strong> {signal.timestamp.strftime("%H:%M:%S")}</p>',
                '</div>'
            ])

        # 尾部
        html_parts.extend([
            '</div>',

            # 提醒信息
            '<div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin-bottom: 20px;">',
            '<h4 style="margin-top: 0; color: #856404;">⚠️ 风险提醒</h4>',
            '<p style="margin-bottom: 0;">技术分析信号仅供参考，不构成投资建议。投资有风险，决策需谨慎。</p>',
            '</div>',

            # 图表说明
            '<div style="background: #e7f3ff; border: 1px solid #b3d9ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;">',
            '<h4 style="margin-top: 0; color: #0056b3;">📎 图表附件</h4>',
            '<p style="margin-bottom: 0;">本邮件包含技术分析图表，请查看附件获取详细的K线图和指标分析。</p>',
            '</div>',

            # 页脚
            '<div style="text-align: center; padding: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px;">',
            '<p>本邮件由交易日志分析工具自动生成 | 基于yagmail框架</p>',
            '<p>如需停止接收此类邮件，请联系系统管理员</p>',
            '</div>',

            '</div>'
        ])

        return html_parts

    def send_to_all_recipients(self, signals: List[Any]) -> bool:
        """发送给所有配置的收件人（纯文本版本）"""
        if not self.recipients:
            logger.warning("没有配置收件人")
            return False

        success_count = 0
        for recipient in self.recipients:
            if self.send_signal_notification(signals, recipient):
                success_count += 1

        logger.info(f"邮件发送完成: {success_count}/{len(self.recipients)} 成功")
        return success_count > 0

    def send_to_all_recipients_with_files(self, signals: List[Any], chart_files: Optional[List[str]] = None) -> bool:
        """发送给所有配置的收件人（主流文件附件方案）"""
        if not self.recipients:
            logger.warning("没有配置收件人")
            return False

        success_count = 0
        for recipient in self.recipients:
            if self.send_signal_notification_with_files(signals, recipient, chart_files):
                success_count += 1

        logger.info(f"邮件发送完成: {success_count}/{len(self.recipients)} 成功")
        return success_count > 0

    def close(self):
        """关闭邮件连接"""
        if self.yag:
            try:
                self.yag.close()
                logger.info("邮件连接已关闭")
            except:
                pass

    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()


# 单例模式 - 全局邮件服务实例
_email_service = None

def get_simple_email_service() -> SimpleEmailService:
    """获取简化邮件服务实例"""
    global _email_service
    if _email_service is None:
        _email_service = SimpleEmailService()
    return _email_service
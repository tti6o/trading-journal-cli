"""
通知服务模块

提供邮件通知功能，支持技术分析信号推送。
包含邮件模板、发送队列、错误重试等功能。
"""

import logging
import smtplib
import ssl
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import configparser
import time
from queue import Queue, Empty
import threading
import traceback

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """邮件配置类"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    sender_name: str = "交易分析助手"


@dataclass
class NotificationMessage:
    """通知消息类"""
    recipient: str
    subject: str
    content: str
    message_type: str = 'text'  # 'text' or 'html'
    attachments: Optional[List[str]] = None
    priority: int = 1  # 1-高优先级, 2-中优先级, 3-低优先级
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.attachments is None:
            self.attachments = []


class EmailNotificationService:
    """邮件通知服务"""
    
    def __init__(self, config_file: str = 'config/config.ini'):
        """
        初始化邮件通知服务
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.email_config = None
        self.enabled = False
        self.notification_queue = Queue()
        self.worker_thread = None
        self.running = False
        
        # 加载配置
        self._load_config()
        
        # 启动工作线程
        if self.enabled:
            self._start_worker()
    
    def _load_config(self) -> None:
        """从配置文件加载邮件设置"""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            
            if config.has_section('email'):
                self.email_config = EmailConfig(
                    smtp_server=config.get('email', 'smtp_server'),
                    smtp_port=config.getint('email', 'smtp_port'),
                    username=config.get('email', 'username'),
                    password=config.get('email', 'password'),
                    use_tls=config.getboolean('email', 'use_tls', fallback=True),
                    sender_name=config.get('email', 'sender_name', fallback='交易分析助手')
                )
                self.enabled = config.getboolean('email', 'enabled', fallback=False)
                
                logger.info(f"邮件通知配置已加载: enabled={self.enabled}")
            else:
                logger.warning("配置文件中未找到邮件配置段")
                
        except Exception as e:
            logger.error(f"加载邮件配置失败: {e}")
            self.enabled = False
    
    def _start_worker(self) -> None:
        """启动邮件发送工作线程"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("邮件通知工作线程已启动")
    
    def _worker_loop(self) -> None:
        """工作线程主循环"""
        while self.running:
            message = None
            try:
                # 从队列获取通知消息，如果1秒内没有消息则会抛出Empty异常
                message = self.notification_queue.get(timeout=1)
                
                # 发送邮件
                success = self._send_email(message)
                
                if not success:
                    logger.error(f"邮件发送失败，跳过此消息: {message.subject} -> {message.recipient}")
                
            except Empty:
                # 这是正常情况，队列中暂时没有消息，继续下一次循环
                continue
                
            except Exception as e:
                logger.error(f"邮件工作线程发生严重错误: {e}")
                logger.error("错误详情:", exc_info=True)
                if message:
                    logger.error(f"失败的消息: {message.subject} -> {message.recipient}")
            finally:
                # 无论成功失败都要标记任务完成，避免队列阻塞
                if message is not None:
                    self.notification_queue.task_done()
    
    def _send_email(self, message: NotificationMessage) -> bool:
        """
        发送邮件
        
        Args:
            message: 通知消息
            
        Returns:
            发送是否成功
        """
        if not self.email_config:
            logger.error("邮件配置未加载，无法发送邮件")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            
            # 设置邮件头部，确保符合RFC标准
            from email.header import Header
            from email.utils import formataddr, formatdate, make_msgid
            
            # 正确格式化发件人信息
            msg['From'] = formataddr((self.email_config.sender_name, self.email_config.username))
            msg['To'] = message.recipient
            msg['Subject'] = Header(message.subject, 'utf-8').encode()
            
            # 添加必要的邮件头部
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()
            
            # 添加邮件正文
            if message.message_type == 'html':
                msg.attach(MIMEText(message.content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(message.content, 'plain', 'utf-8'))
            
            # 添加附件
            if message.attachments:
                for attachment_path in message.attachments:
                    try:
                        with open(attachment_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {attachment_path.split("/")[-1]}'
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"添加附件失败 {attachment_path}: {e}")
            
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 连接SMTP服务器并发送
            try:
                if self.email_config.smtp_port == 465:
                    # 使用SSL连接（465端口）
                    logger.debug(f"正在连接到邮件服务器 {self.email_config.smtp_server}:465 (SSL)")
                    server = smtplib.SMTP_SSL(self.email_config.smtp_server, self.email_config.smtp_port, context=context)
                    logger.debug("正在进行邮箱认证...")
                    server.login(self.email_config.username, self.email_config.password)
                    logger.debug("认证成功，正在发送邮件...")
                    
                    # 使用 sendmail 方法而不是 send_message
                    text = msg.as_string()
                    server.sendmail(self.email_config.username, [message.recipient], text)
                    logger.debug("邮件发送完成，正在关闭连接...")
                    server.quit()
                else:
                    # 使用普通连接然后升级到TLS（587端口）
                    logger.debug(f"正在连接到邮件服务器 {self.email_config.smtp_server}:{self.email_config.smtp_port} (TLS)")
                    server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
                    if self.email_config.use_tls:
                        server.starttls(context=context)
                    logger.debug("正在进行邮箱认证...")
                    server.login(self.email_config.username, self.email_config.password)
                    logger.debug("认证成功，正在发送邮件...")
                    
                    # 使用 sendmail 方法而不是 send_message
                    text = msg.as_string()
                    server.sendmail(self.email_config.username, [message.recipient], text)
                    logger.debug("邮件发送完成，正在关闭连接...")
                    server.quit()
            except Exception as smtp_error:
                logger.error(f"SMTP连接失败: {smtp_error}")
                logger.error("错误详情:", exc_info=True)
                raise
            
            logger.info(f"邮件发送成功: {message.subject} -> {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def send_notification(self, message: NotificationMessage) -> bool:
        """
        发送通知消息
        
        Args:
            message: 通知消息
            
        Returns:
            是否成功加入发送队列
        """
        if not self.enabled:
            logger.debug("邮件通知已禁用")
            return False
        
        try:
            self.notification_queue.put(message)
            logger.debug(f"通知消息已加入队列: {message.subject}")
            return True
        except Exception as e:
            logger.error(f"添加通知消息到队列失败: {e}")
            return False
    
    def send_signal_notification(self, signals: List[Any], recipient: str) -> bool:
        """
        发送技术分析信号通知
        
        Args:
            signals: 技术信号列表
            recipient: 收件人邮箱
            
        Returns:
            是否成功发送
        """
        if not signals:
            return False
        
        # 生成邮件内容
        subject = f"技术分析信号提醒 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        content = self._generate_signal_email_content(signals)
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            content=content,
            message_type='html',
            priority=1
        )
        
        return self.send_notification(message)

    def send_signal_notification_with_attachments(self, signals: List[Any], recipient: str,
                                                chart_file_paths: List[str] = None,
                                                market_summary: Dict = None) -> bool:
        """
        发送含图表附件的技术分析信号通知 - 简化版本

        Args:
            signals: 技术信号列表
            recipient: 收件人邮箱
            chart_file_paths: 图表文件路径列表（作为附件）
            market_summary: 市场摘要数据

        Returns:
            是否成功发送
        """
        if not signals:
            logger.warning("发送信号通知失败: 没有信号数据")
            return False

        logger.info(f"准备发送技术分析信号邮件到: {recipient}")
        logger.info(f"信号数量: {len(signals)}, 附件数量: {len(chart_file_paths) if chart_file_paths else 0}")

        # 生成邮件内容
        subject = f"技术分析信号提醒 (RSI+斐波那契) - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        content = self._generate_signal_email_content(signals)

        # 准备附件列表
        attachments = chart_file_paths if chart_file_paths else []

        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            content=content,
            message_type='html',
            attachments=attachments,  # 使用附件方式
            priority=1
        )

        logger.info(f"附件邮件消息已创建，主题: {subject}")
        result = self.send_notification(message)
        logger.info(f"邮件发送结果: {result}")

        return result

    def send_signal_notification_with_charts(self, signals: List[Any], recipient: str,
                                             chart_urls: List[str] = None,
                                             market_summary: Dict = None) -> bool:
        """
        发送含外部图表链接的技术分析信号通知 - EBC风格

        Args:
            signals: 技术信号列表
            recipient: 收件人邮箱
            chart_urls: 图表外部URL列表 (参考EBC方案)
            market_summary: 市场摘要数据

        Returns:
            是否成功发送
        """
        if not signals:
            logger.warning("发送信号通知失败: 没有信号数据")
            return False

        logger.info(f"准备发送技术分析信号邮件到: {recipient}")
        logger.info(f"信号数量: {len(signals)}, 图表数量: {len(chart_urls) if chart_urls else 0}")

        # 生成带外部图表链接的邮件内容 - EBC风格
        subject = f"技术分析信号提醒 (RSI+斐波那契) - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        content = self._generate_email_with_embedded_charts(signals, chart_urls, market_summary)

        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            content=content,
            message_type='html',
            attachments=[],  # 不使用附件，图片已内嵌
            priority=1
        )

        logger.info(f"内嵌图表邮件消息已创建，主题: {subject}")
        result = self.send_notification(message)
        logger.info(f"邮件发送结果: {result}")

        return result
    
    def _generate_signal_email_content(self, signals: List[Any]) -> str:
        """
        生成信号邮件内容 (支持RSI和斐波那契分析)
        
        Args:
            signals: 信号列表
            
        Returns:
            HTML格式的邮件内容
        """
        # 统计信号类型和指标类型
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        
        rsi_signals = [s for s in signals if s.indicator_type == 'RSI']
        fibonacci_signals = [s for s in signals if s.indicator_type == 'FIBONACCI']
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: bold; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .summary {{ padding: 20px; background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; }}
                .summary-item {{ display: inline-block; margin: 0 20px 10px 0; padding: 10px 15px; background-color: white; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .signal {{ margin: 20px; padding: 20px; border-radius: 8px; border-left: 5px solid #007bff; background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
                .signal.buy {{ border-left-color: #28a745; background: linear-gradient(to right, #f8fff9, #ffffff); }}
                .signal.sell {{ border-left-color: #dc3545; background: linear-gradient(to right, #fff8f8, #ffffff); }}
                .signal.neutral {{ border-left-color: #ffc107; background: linear-gradient(to right, #fffef8, #ffffff); }}
                .signal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
                .signal-type {{ font-size: 18px; font-weight: bold; }}
                .signal-type.buy {{ color: #28a745; }}
                .signal-type.sell {{ color: #dc3545; }}
                .signal-type.neutral {{ color: #ffc107; }}
                .signal-price {{ font-size: 16px; color: #666; }}
                .rsi-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .rsi-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .signal-message {{ font-size: 14px; line-height: 1.6; color: #333; margin-top: 10px; }}
                .footer {{ padding: 20px; text-align: center; background-color: #f8f9fa; color: #666; font-size: 12px; }}
                .disclaimer {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 技术分析信号 (RSI + 斐波那契)</h1>
                    <p>发现 {len(signals)} 个交易信号 | {len(rsi_signals)} 个RSI信号, {len(fibonacci_signals)} 个斐波那契信号 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <div class="summary-item">
                        <strong>📈 买入信号:</strong> {len(buy_signals)} 个
                    </div>
                    <div class="summary-item">
                        <strong>📉 卖出信号:</strong> {len(sell_signals)} 个
                    </div>
                    <div class="summary-item">
                        <strong>🔶 RSI分析:</strong> {len(rsi_signals)} 个
                    </div>
                    <div class="summary-item">
                        <strong>📐 斐波那契:</strong> {len(fibonacci_signals)} 个
                    </div>
                    <div class="summary-item">
                        <strong>📊 总计:</strong> {len(signals)} 个信号
                    </div>
                </div>
        """
        
        # 按信号类型分组显示
        for signal_type, signal_list in [('买入信号', buy_signals), ('卖出信号', sell_signals)]:
            if signal_list:
                html_content += f"""
                <div style="margin: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                    <h3 style="margin: 0 0 15px 0; color: #333;">🎯 {signal_type} ({len(signal_list)} 个)</h3>
                """
                
                for signal in signal_list:
                    signal_class = signal.signal_type.lower()
                    
                    html_content += f"""
                    <div class="signal {signal_class}">
                        <div class="signal-header">
                            <div>
                                <span class="signal-type {signal_class}">{signal.symbol}</span>
                                <span style="margin-left: 10px; font-size: 14px; color: #666;">
                                    {signal.timestamp.strftime('%H:%M:%S')}
                                </span>
                            </div>
                            <div class="signal-price">
                                💰 ${signal.price:.6f}
                            </div>
                        </div>
                        
                        <div class="rsi-info">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                {self._format_signal_indicator(signal)}
                            </div>
                        </div>
                        
                        <div class="signal-message">
                            💡 <strong>分析说明:</strong> {signal.message}
                        </div>
                    </div>
                    """
                
                html_content += "</div>"
        
        # 如果有中性信号，也显示一部分
        neutral_signals = [s for s in signals if s.signal_type == 'NEUTRAL']
        if neutral_signals:
            # 只显示前5个中性信号，避免邮件过长
            display_neutral = neutral_signals[:5]
            html_content += f"""
            <div style="margin: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                <h3 style="margin: 0 0 15px 0; color: #333;">⚖️ 中性信号 (显示前{len(display_neutral)}个，共{len(neutral_signals)}个)</h3>
            """
            
            for signal in display_neutral:
                html_content += f"""
                <div class="signal neutral">
                    <div class="signal-header">
                        <div>
                            <span class="signal-type neutral">{signal.symbol}</span>
                        </div>
                        <div class="signal-price">
                            💰 ${signal.price:.6f} | {self._format_signal_price_info(signal)}
                        </div>
                    </div>
                    <div class="signal-message" style="font-size: 12px;">
                        {signal.message}
                    </div>
                </div>
                """
            
            html_content += "</div>"
        
        html_content += f"""
                <div class="disclaimer">
                    <strong>⚠️ 风险提示:</strong> 本分析基于RSI和斐波那契技术指标，仅供参考。投资有风险，请结合其他分析方法和基本面分析，并谨慎决策。
                </div>
                
                <div class="footer">
                    <p>本邮件由交易日志分析工具自动生成 | 多指标技术分析系统 (RSI + 斐波那契)</p>
                    <p>如需停止接收此类邮件，请联系系统管理员</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_enhanced_signal_email_content(self, signals: List[Any], 
                                                market_summary: Dict = None) -> str:
        """
        生成增强版信号邮件内容 (支持RSI和斐波那契分析 + 市场摘要)
        
        Args:
            signals: 信号列表
            market_summary: 市场摘要数据
            
        Returns:
            HTML格式的邮件内容
        """
        # 统计信号类型和指标类型
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        
        rsi_signals = [s for s in signals if s.indicator_type == 'RSI']
        fibonacci_signals = [s for s in signals if s.indicator_type == 'FIBONACCI']
        
        # 高置信度信号统计
        high_conf_signals = [s for s in signals if s.confidence >= 0.7]
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 900px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 28px; font-weight: bold; }}
                .header p {{ margin: 10px 0 0 0; font-size: 16px; opacity: 0.9; }}
                .summary {{ padding: 20px; background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                .summary-item {{ padding: 15px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
                .summary-number {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .summary-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                .market-sentiment {{ padding: 20px; margin: 20px; border-radius: 8px; text-align: center; }}
                .market-sentiment.bullish {{ background: linear-gradient(to right, #d4edda, #c3e6cb); border: 1px solid #28a745; }}
                .market-sentiment.bearish {{ background: linear-gradient(to right, #f8d7da, #f1b0b7); border: 1px solid #dc3545; }}
                .market-sentiment.neutral {{ background: linear-gradient(to right, #fff3cd, #ffeaa7); border: 1px solid #ffc107; }}
                .signal {{ margin: 15px 20px; padding: 20px; border-radius: 8px; border-left: 5px solid #007bff; background-color: #ffffff; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
                .signal.buy {{ border-left-color: #28a745; background: linear-gradient(to right, #f8fff9, #ffffff); }}
                .signal.sell {{ border-left-color: #dc3545; background: linear-gradient(to right, #fff8f8, #ffffff); }}
                .signal-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
                .signal-type {{ font-size: 18px; font-weight: bold; }}
                .signal-type.buy {{ color: #28a745; }}
                .signal-type.sell {{ color: #dc3545; }}
                .signal-price {{ font-size: 16px; color: #666; }}
                .indicator-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .indicator-value {{ font-size: 20px; font-weight: bold; color: #007bff; }}
                .signal-message {{ font-size: 14px; line-height: 1.6; color: #333; margin-top: 10px; }}
                .confidence-badge {{ display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
                .confidence-high {{ background-color: #28a745; color: white; }}
                .confidence-medium {{ background-color: #ffc107; color: black; }}
                .confidence-low {{ background-color: #6c757d; color: white; }}
                .chart-notice {{ background-color: #e7f3ff; border: 1px solid #b3d9ff; padding: 15px; margin: 20px; border-radius: 5px; text-align: center; }}
                .footer {{ padding: 20px; text-align: center; background-color: #f8f9fa; color: #666; font-size: 12px; }}
                .disclaimer {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 技术分析信号报告</h1>
                    <p>RSI + 斐波那契综合分析 | 发现 {len(signals)} 个信号 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-number">{len(buy_signals)}</div>
                            <div class="summary-label">📈 买入信号</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len(sell_signals)}</div>
                            <div class="summary-label">📉 卖出信号</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len(rsi_signals)}</div>
                            <div class="summary-label">🔶 RSI分析</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len(fibonacci_signals)}</div>
                            <div class="summary-label">📐 斐波那契</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-number">{len(high_conf_signals)}</div>
                            <div class="summary-label">⭐ 高置信度</div>
                        </div>
                    </div>
                </div>
        """
        
        # 添加市场情绪摘要
        if market_summary:
            sentiment = market_summary.get('market_sentiment', 'NEUTRAL')
            sentiment_class = sentiment.lower()
            sentiment_emoji = {'BULLISH': '🐂', 'BEARISH': '🐻', 'NEUTRAL': '⚖️'}.get(sentiment, '⚖️')
            
            html_content += f"""
                <div class="market-sentiment {sentiment_class}">
                    <h3 style="margin: 0 0 10px 0;">{sentiment_emoji} 市场情绪: {sentiment}</h3>
                    <p style="margin: 0; font-size: 14px;">
                        分析了 {market_summary.get('total_symbols', 0)} 个交易对，
                        总计 {market_summary.get('total_signals', 0)} 个信号，
                        其中 {market_summary.get('high_confidence_signals', 0)} 个高置信度信号
                    </p>
                </div>
            """
        
        # 显示买入和卖出信号
        for signal_type, signal_list, emoji in [('买入信号', buy_signals, '📈'), ('卖出信号', sell_signals, '📉')]:
            if signal_list:
                html_content += f"""
                <div style="margin: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                    <h3 style="margin: 0 0 15px 0; color: #333;">{emoji} {signal_type} ({len(signal_list)} 个)</h3>
                """
                
                for signal in signal_list:
                    signal_class = signal.signal_type.lower()
                    confidence_class = 'high' if signal.confidence >= 0.7 else 'medium' if signal.confidence >= 0.4 else 'low'
                    
                    html_content += f"""
                    <div class="signal {signal_class}">
                        <div class="signal-header">
                            <div>
                                <span class="signal-type {signal_class}">{signal.symbol}</span>
                                <span class="confidence-badge confidence-{confidence_class}">
                                    置信度 {signal.confidence:.1%}
                                </span>
                                <span style="margin-left: 10px; font-size: 14px; color: #666;">
                                    {signal.timestamp.strftime('%H:%M:%S')}
                                </span>
                            </div>
                            <div class="signal-price">
                                💰 ${signal.price:.6f}
                            </div>
                        </div>
                        
                        <div class="indicator-info">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                {self._format_enhanced_signal_indicator(signal)}
                            </div>
                        </div>
                        
                        <div class="signal-message">
                            💡 <strong>分析说明:</strong> {signal.message}
                        </div>
                    </div>
                    """
                
                html_content += "</div>"
        
        # 图表附件说明
        html_content += f"""
            <div class="chart-notice">
                <h4 style="margin: 0 0 10px 0;">📊 技术分析图表</h4>
                <p style="margin: 0;">
                    本邮件已附带相关交易对的技术分析图表，包含K线图、关键高低点标记、
                    斐波那契回调线和扩展线。请查看邮件附件获取详细的可视化分析。
                </p>
            </div>
        """
        
        html_content += f"""
                <div class="disclaimer">
                    <strong>⚠️ 风险提示:</strong> 本分析基于RSI和斐波那契技术指标的综合分析，仅供参考。
                    投资有风险，请结合其他分析方法、基本面分析和风险管理策略，谨慎决策。
                </div>
                
                <div class="footer">
                    <p>本邮件由交易日志分析工具自动生成 | RSI + 斐波那契综合技术分析系统</p>
                    <p>图表附件包含详细的技术分析可视化 | 如需停止接收此类邮件，请联系系统管理员</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _format_signal_indicator(self, signal) -> str:
        """格式化信号指标信息"""
        if signal.indicator_type == 'RSI' and signal.rsi_value is not None:
            return f'''
                <span>RSI(14) 指标值:</span>
                <span class="rsi-value">{signal.rsi_value:.1f}</span>
            '''
        elif signal.indicator_type == 'FIBONACCI':
            fib_pct = signal.fib_level * 100 if signal.fib_level else 0
            return f'''
                <span>斐波那契 {signal.fib_type}:</span>
                <span class="rsi-value">{fib_pct:.1f}% ({signal.trend_direction})</span>
            '''
        else:
            return f'''
                <span>{signal.indicator_type} 指标:</span>
                <span class="rsi-value">置信度 {signal.confidence:.1%}</span>
            '''
    
    def _format_signal_price_info(self, signal) -> str:
        """格式化信号价格信息"""
        if signal.indicator_type == 'RSI' and signal.rsi_value is not None:
            return f"RSI: {signal.rsi_value:.1f}"
        elif signal.indicator_type == 'FIBONACCI':
            fib_pct = signal.fib_level * 100 if signal.fib_level else 0
            return f"FIB: {fib_pct:.1f}%"
        else:
            return f"{signal.indicator_type}: {signal.confidence:.1%}"
    
    def _format_enhanced_signal_indicator(self, signal) -> str:
        """格式化增强版信号指标信息 - 参考EBC专业格式"""
        if signal.indicator_type == 'RSI' and signal.rsi_value is not None:
            # 生成具体的交易策略
            rsi_level = self._get_rsi_level_description(signal.rsi_value)
            trading_strategy = self._generate_rsi_trading_strategy(signal)

            return f'''
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <div style="font-weight: bold; margin-bottom: 10px;">🔶 RSI(14) 技术分析</div>
                    <div><strong>当前RSI值:</strong> {signal.rsi_value:.1f} ({rsi_level})</div>
                    <div><strong>转折点:</strong> {signal.price:.4f}</div>
                    <div style="margin: 10px 0;">
                        <strong>交易策略:</strong><br>
                        {trading_strategy}
                    </div>
                    <div><strong>技术意见:</strong> RSI技术指标{self._get_rsi_trend_opinion(signal.rsi_value)}</div>
                </div>
            '''
        elif signal.indicator_type == 'FIBONACCI':
            fib_pct = signal.fib_level * 100 if signal.fib_level else 0
            trend_emoji = '📈' if signal.trend_direction == 'UP' else '📉'
            fib_strategy = self._generate_fibonacci_trading_strategy(signal)

            return f'''
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <div style="font-weight: bold; margin-bottom: 10px;">📐 斐波那契 {signal.fib_type} 分析</div>
                    <div><strong>关键水平:</strong> {fib_pct:.1f}% @ {signal.price:.4f}</div>
                    <div><strong>趋势方向:</strong> {trend_emoji} {signal.trend_direction}</div>
                    <div style="margin: 10px 0;">
                        <strong>交易策略:</strong><br>
                        {fib_strategy}
                    </div>
                    <div><strong>技术意见:</strong> 价格已{self._get_fib_position_desc(signal)}斐波那契{fib_pct:.1f}%水平，{self._get_fib_expectation(signal)}</div>
                </div>
            '''
        else:
            return f'''
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <div><strong>{signal.indicator_type} 指标:</strong> 置信度 {signal.confidence:.1%}</div>
                </div>
            '''
    
    def _get_rsi_level_description(self, rsi_value: float) -> str:
        """获取RSI水平描述"""
        if rsi_value <= 30:
            return "超卖区域"
        elif rsi_value >= 70:
            return "超买区域"
        elif rsi_value < 40:
            return "偏弱"
        elif rsi_value > 60:
            return "偏强"
        else:
            return "中性区域"

    def _generate_rsi_trading_strategy(self, signal) -> str:
        """生成RSI交易策略 - 参考EBC格式"""
        price = signal.price
        rsi = signal.rsi_value

        if rsi <= 30:  # 超卖
            target1 = price * 1.02  # 2%目标
            target2 = price * 1.05  # 5%目标
            stop_loss = price * 0.98  # 2%止损
            return f"在当前价位 {price:.4f} 附近，考虑逢低买入，目标价为 {target1:.4f}，第二目标价为 {target2:.4f}。止损位设在 {stop_loss:.4f}。"

        elif rsi >= 70:  # 超买
            target1 = price * 0.98  # 2%目标
            target2 = price * 0.95  # 5%目标
            stop_loss = price * 1.02  # 2%止损
            return f"在当前价位 {price:.4f} 附近，考虑逢高卖出，目标价为 {target1:.4f}，第二目标价为 {target2:.4f}。止损位设在 {stop_loss:.4f}。"

        elif signal.signal_type == 'SELL':
            target1 = price * 0.98
            target2 = price * 0.95
            stop_loss = price * 1.02
            return f"在 {price:.4f} 之下，看空，目标价为 {target1:.4f}，第二目标价为 {target2:.4f}。备选策略：在 {price:.4f} 之上反弹时考虑止损。"

        else:  # 中性或买入
            target1 = price * 1.02
            target2 = price * 1.05
            stop_loss = price * 0.98
            return f"在 {price:.4f} 之上，看多，目标价为 {target1:.4f}，第二目标价为 {target2:.4f}。备选策略：在 {price:.4f} 之下考虑止损。"

    def _get_rsi_trend_opinion(self, rsi_value: float) -> str:
        """获取RSI趋势意见"""
        if rsi_value <= 30:
            return "处于超卖区域，有反弹空间，但需谨慎确认底部"
        elif rsi_value >= 70:
            return "处于超买区域，存在回调风险，建议谨慎追高"
        elif rsi_value > 50:
            return "在50%中性区域之上，显示多头优势，但需关注是否持续"
        else:
            return "在50%中性区域之下，显示空头压力，需要观察是否企稳"

    def _generate_fibonacci_trading_strategy(self, signal) -> str:
        """生成斐波那契交易策略"""
        price = signal.price
        fib_level = signal.fib_level * 100

        if signal.signal_type == 'SELL':
            target1 = price * 0.98
            target2 = price * 0.96
            stop_loss = price * 1.015
            return f"价格触及{fib_level:.1f}%斐波那契水平 {price:.4f}，考虑在此位置附近做空，目标价为 {target1:.4f}，第二目标价为 {target2:.4f}。止损位设在 {stop_loss:.4f}。"
        else:
            target1 = price * 1.02
            target2 = price * 1.04
            stop_loss = price * 0.985
            return f"价格在{fib_level:.1f}%斐波那契水平 {price:.4f} 获得支撑，考虑在此位置附近做多，目标价为 {target1:.4f}，第二目标价为 {target2:.4f}。止损位设在 {stop_loss:.4f}。"

    def _get_fib_position_desc(self, signal) -> str:
        """获取斐波那契位置描述"""
        if signal.signal_type == 'SELL':
            return "触及"
        else:
            return "接近"

    def _get_fib_expectation(self, signal) -> str:
        """获取斐波那契预期"""
        fib_level = signal.fib_level * 100
        if signal.signal_type == 'SELL':
            if fib_level >= 61.8:
                return "预期可能出现回调压力"
            else:
                return "存在进一步上涨受阻的可能"
        else:
            if fib_level <= 38.2:
                return "预期可能获得反弹支撑"
            else:
                return "存在进一步下跌受限的可能"
    
    def test_email_config(self) -> Dict[str, Any]:
        """
        测试邮件配置（仅测试连接和认证）
        
        Returns:
            测试结果字典
        """
        if not self.email_config:
            return {
                'success': False,
                'message': '邮件配置未加载'
            }
        
        try:
            # 创建SSL上下文
            context = ssl.create_default_context()
            
            # 测试SMTP连接
            if self.email_config.smtp_port == 465:
                # 使用SSL连接（465端口）
                logger.debug(f"测试连接到 {self.email_config.smtp_server}:465 (SSL)")
                with smtplib.SMTP_SSL(self.email_config.smtp_server, self.email_config.smtp_port, context=context) as server:
                    logger.debug("测试邮箱认证...")
                    server.login(self.email_config.username, self.email_config.password)
                    logger.debug("认证测试成功")
            else:
                # 使用普通连接然后升级到TLS（587端口）
                logger.debug(f"测试连接到 {self.email_config.smtp_server}:{self.email_config.smtp_port} (TLS)")
                with smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port) as server:
                    if self.email_config.use_tls:
                        server.starttls(context=context)
                    logger.debug("测试邮箱认证...")
                    server.login(self.email_config.username, self.email_config.password)
                    logger.debug("认证测试成功")
            
            return {
                'success': True,
                'message': '邮件配置测试成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'邮件配置测试失败: {str(e)}'
            }
    
    def send_test_email(self, recipient: Optional[str] = None) -> Dict[str, Any]:
        """
        发送测试邮件
        
        Args:
            recipient: 收件人邮箱，如果为None则发送给配置的用户名邮箱
            
        Returns:
            发送结果字典
        """
        if not self.email_config:
            return {
                'success': False,
                'message': '邮件配置未加载'
            }
        
        # 如果没有指定收件人，则发送给自己
        if recipient is None:
            recipient = self.email_config.username
        
        try:
            # 创建测试邮件内容
            test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = f"交易日志系统 - 邮件功能测试 [{test_time}]"
            
            content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #e8f5e8; padding: 20px; border-radius: 5px; text-align: center; }}
                    .content {{ margin: 20px 0; }}
                    .info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                    .success {{ color: #28a745; font-weight: bold; }}
                    .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>✅ 邮件功能测试成功</h2>
                    <p class="success">如果您收到这封邮件，说明邮件通知功能正常工作！</p>
                </div>
                
                <div class="content">
                    <div class="info">
                        <h3>📧 邮件配置信息</h3>
                        <p><strong>SMTP服务器:</strong> {self.email_config.smtp_server}:{self.email_config.smtp_port}</p>
                        <p><strong>发送邮箱:</strong> {self.email_config.username}</p>
                        <p><strong>发送者名称:</strong> {self.email_config.sender_name}</p>
                        <p><strong>安全连接:</strong> {'SSL' if self.email_config.smtp_port == 465 else 'TLS' if self.email_config.use_tls else '无'}</p>
                    </div>
                    
                    <div class="info">
                        <h3>🕒 测试信息</h3>
                        <p><strong>测试时间:</strong> {test_time}</p>
                        <p><strong>收件人:</strong> {recipient}</p>
                        <p><strong>邮件类型:</strong> HTML格式测试邮件</p>
                    </div>
                    
                    <div class="info">
                        <h3>🔧 系统状态</h3>
                        <p><strong>通知服务状态:</strong> {'运行中' if self.running else '已停止'}</p>
                        <p><strong>待发送队列:</strong> {self.notification_queue.qsize()} 条消息</p>
                        <p><strong>工作线程:</strong> {'活跃' if self.worker_thread and self.worker_thread.is_alive() else '未启动'}</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>这是一封自动生成的测试邮件，无需回复。</p>
                    <p>交易日志分析工具 - 邮件通知系统</p>
                </div>
            </body>
            </html>
            """
            
            # 创建测试消息
            test_message = NotificationMessage(
                recipient=recipient,
                subject=subject,
                content=content,
                message_type='html',
                priority=1
            )
            
            logger.info(f"正在发送测试邮件到: {recipient}")
            
            # 直接发送测试邮件（不通过队列）
            success = self._send_email(test_message)
            
            if success:
                logger.info(f"✅ 测试邮件发送成功: {recipient}")
                return {
                    'success': True,
                    'message': f'测试邮件发送成功到 {recipient}',
                    'recipient': recipient,
                    'timestamp': test_time
                }
            else:
                logger.error(f"❌ 测试邮件发送失败: {recipient}")
                return {
                    'success': False,
                    'message': f'测试邮件发送失败到 {recipient}'
                }
                
        except Exception as e:
            logger.error(f"发送测试邮件时发生异常: {e}")
            logger.error("详细错误信息:", exc_info=True)
            return {
                'success': False,
                'message': f'发送测试邮件失败: {str(e)}'
            }
    
    def stop(self) -> None:
        """停止通知服务"""
        if self.running:
            self.running = False
            
            # 等待队列清空
            self.notification_queue.join()
            
            # 等待工作线程结束
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5)
            
            logger.info("邮件通知服务已停止")
    
    def _generate_email_with_embedded_charts(self, signals: List[Any],
                                           chart_urls: List[str] = None,
                                           market_summary: Dict = None) -> str:
        """
        生成带外部图表链接的HTML邮件内容 - EBC风格

        Args:
            signals: 信号列表
            chart_urls: 图表外部URL列表 (参考EBC方案)
            market_summary: 市场摘要数据

        Returns:
            包含外部图表链接的HTML邮件内容
        """
        # 首先生成基础的邮件内容
        base_html = self._generate_enhanced_signal_email_content(signals, market_summary)

        # 如果没有图表，直接返回基础HTML
        if not chart_urls:
            return base_html

        # 生成外部图表链接的HTML - EBC风格
        charts_html = self._generate_embedded_charts_html(chart_urls)

        # 在邮件HTML中插入图表部分
        # 找到合适的位置插入图表（在disclaimer之前）
        disclaimer_pos = base_html.find('<div class="disclaimer">')
        if disclaimer_pos != -1:
            # 在disclaimer之前插入图表
            enhanced_html = (base_html[:disclaimer_pos] +
                           charts_html + '\n                ' +
                           base_html[disclaimer_pos:])
        else:
            # 如果没找到disclaimer，在footer之前插入
            footer_pos = base_html.find('<div class="footer">')
            if footer_pos != -1:
                enhanced_html = (base_html[:footer_pos] +
                               charts_html + '\n                ' +
                               base_html[footer_pos:])
            else:
                # 如果都没找到，直接在结尾前添加
                enhanced_html = base_html.replace('</body>', charts_html + '\n        </body>')

        return enhanced_html

    def _generate_embedded_charts_html(self, chart_urls: List[str]) -> str:
        """
        生成外部链接图表的HTML代码 - EBC方案
        🚀 使用外部URL而非base64内嵌，大幅减少邮件大小

        Args:
            chart_urls: 图表Web URL列表

        Returns:
            图表HTML代码
        """
        if not chart_urls:
            return ""

        charts_html = '''
                <div class="charts-section" style="margin: 20px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                    <h2 style="color: #333; text-align: center; margin-bottom: 20px;">📊 技术分析图表</h2>
                    <p style="text-align: center; color: #666; margin-bottom: 30px;">
                        以下图表显示了相关交易对的K线走势、RSI指标和斐波那契水平线分析
                    </p>
        '''

        for i, chart_url in enumerate(chart_urls):
            try:
                # 从URL中提取币种名称
                import re
                symbol_match = re.search(r'([A-Z]+USDT)', chart_url)
                symbol = symbol_match.group(1) if symbol_match else f'Chart_{i+1}'

                charts_html += f'''
                    <div style="margin: 30px 0; text-align: center;">
                        <h3 style="color: #007bff; margin-bottom: 15px;">🎯 {symbol} 技术分析图表</h3>
                        <div style="border: 2px solid #e0e0e0; border-radius: 8px; padding: 10px; background-color: white; display: inline-block; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <img src="{chart_url}"
                                 alt="{symbol} 技术分析图表"
                                 style="max-width: 100%; height: auto; border-radius: 4px; max-width: 800px;"
                                 loading="lazy" />
                        </div>
                        <p style="font-size: 12px; color: #888; margin-top: 10px; font-style: italic;">
                            包含K线图、RSI指标和斐波那契水平线分析
                        </p>
                    </div>
                    '''

            except Exception as e:
                logger.error(f"处理图表URL失败 {chart_url}: {e}")
                continue

        charts_html += '''
                    <div style="text-align: center; margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-radius: 5px;">
                        <p style="margin: 0; color: #0066cc; font-size: 14px;">
                            💡 <strong>图表说明：</strong> 绿色蜡烛表示上涨，红色蜡烛表示下跌。RSI指标显示超买超卖情况，蓝色虚线为斐波那契关键水平。
                        </p>
                    </div>
                </div>
        '''

        return charts_html

    def _convert_image_to_base64(self, image_path: str) -> str:
        """
        将图片文件转换为base64编码

        Args:
            image_path: 图片文件路径

        Returns:
            base64编码的图片数据，失败返回空字符串
        """
        try:
            import os
            if not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                return ""

            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                logger.debug(f"图片 {image_path} 转换为base64成功，大小: {len(base64_data)} 字符")
                return base64_data

        except Exception as e:
            logger.error(f"转换图片为base64失败 {image_path}: {e}")
            return ""

    def get_status(self) -> Dict[str, Any]:
        """
        获取通知服务状态

        Returns:
            状态字典
        """
        return {
            'enabled': self.enabled,
            'running': self.running,
            'queue_size': self.notification_queue.qsize(),
            'config_loaded': self.email_config is not None,
            'worker_alive': self.worker_thread and self.worker_thread.is_alive() if self.worker_thread else False
        }


# 全局通知服务实例
_notification_service = None


def get_notification_service() -> EmailNotificationService:
    """获取全局通知服务实例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = EmailNotificationService()
    return _notification_service
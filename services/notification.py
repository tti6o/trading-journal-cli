"""
通知服务模块

提供邮件通知功能，支持技术分析信号推送。
包含邮件模板、发送队列、错误重试等功能。
"""

import logging
import smtplib
import ssl
import json
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
    
    def _generate_signal_email_content(self, signals: List[Any]) -> str:
        """
        生成信号邮件内容 (适配MVP版本技术分析)
        
        Args:
            signals: 信号列表
            
        Returns:
            HTML格式的邮件内容
        """
        # 统计信号类型
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        
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
                    <h1>🚨 RSI技术分析信号</h1>
                    <p>发现 {len(signals)} 个交易信号 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <div class="summary-item">
                        <strong>📈 买入信号:</strong> {len(buy_signals)} 个
                    </div>
                    <div class="summary-item">
                        <strong>📉 卖出信号:</strong> {len(sell_signals)} 个
                    </div>
                    <div class="summary-item">
                        <strong>📊 总计分析:</strong> {len(signals)} 个交易对
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
                                <span>RSI(14) 指标值:</span>
                                <span class="rsi-value">{signal.rsi_value:.1f}</span>
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
                            💰 ${signal.price:.6f} | RSI: {signal.rsi_value:.1f}
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
                    <strong>⚠️ 风险提示:</strong> 本分析仅基于RSI技术指标，仅供参考。投资有风险，请结合其他分析方法并谨慎决策。
                </div>
                
                <div class="footer">
                    <p>本邮件由交易日志分析工具自动生成 | RSI技术分析模块 (MVP版本)</p>
                    <p>如需停止接收此类邮件，请联系系统管理员</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
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
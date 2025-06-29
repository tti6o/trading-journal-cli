"""
通知服务模块

提供邮件通知功能，支持技术分析信号推送。
包含邮件模板、发送队列、错误重试等功能。
"""

import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import configparser
import time
from queue import Queue
import threading

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
            try:
                # 从队列获取通知消息
                message = self.notification_queue.get(timeout=1)
                
                # 发送邮件
                self._send_email(message)
                
                # 标记任务完成
                self.notification_queue.task_done()
                
            except Exception as e:
                if "timed out" not in str(e):
                    logger.error(f"邮件工作线程发生错误: {e}")
                continue
    
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
            msg['From'] = f"{self.email_config.sender_name} <{self.email_config.username}>"
            msg['To'] = message.recipient
            msg['Subject'] = message.subject
            
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
            
            # 连接SMTP服务器并发送
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            
            if self.email_config.use_tls:
                server.starttls()
            
            server.login(self.email_config.username, self.email_config.password)
            server.send_message(msg)
            server.quit()
            
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
        生成信号邮件内容
        
        Args:
            signals: 信号列表
            
        Returns:
            HTML格式的邮件内容
        """
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f0f0f0; padding: 20px; text-align: center; }}
                .signal {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }}
                .buy {{ border-left-color: #28a745; }}
                .sell {{ border-left-color: #dc3545; }}
                .indicators {{ margin: 10px 0; }}
                .indicator {{ display: inline-block; margin: 5px; padding: 5px 10px; background-color: #f8f9fa; border-radius: 3px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 技术分析信号提醒</h2>
                <p>发现 {len(signals)} 个技术分析信号</p>
                <p>时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        for signal in signals:
            signal_class = 'buy' if signal.signal_type == 'BUY' else 'sell'
            confidence_percent = f"{signal.confidence * 100:.1f}%"
            
            html_content += f"""
            <div class="signal {signal_class}">
                <h3>{signal.symbol} - {signal.signal_type} 信号</h3>
                <p><strong>置信度:</strong> {confidence_percent}</p>
                <p><strong>当前价格:</strong> {signal.price:.6f}</p>
                <p><strong>信号描述:</strong> {signal.message}</p>
                
                <div class="indicators">
                    <h4>技术指标:</h4>
            """
            
            for indicator, value in signal.indicators.items():
                if isinstance(value, float):
                    value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                html_content += f'<span class="indicator">{indicator}: {value_str}</span>'
            
            html_content += """
                </div>
            </div>
            """
        
        html_content += """
            <div class="footer">
                <p>本信号仅供参考，投资有风险，请谨慎决策。</p>
                <p>交易日志分析工具 - 技术分析模块</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def test_email_config(self) -> Dict[str, Any]:
        """
        测试邮件配置
        
        Returns:
            测试结果字典
        """
        if not self.email_config:
            return {
                'success': False,
                'message': '邮件配置未加载'
            }
        
        try:
            # 测试SMTP连接
            server = smtplib.SMTP(self.email_config.smtp_server, self.email_config.smtp_port)
            
            if self.email_config.use_tls:
                server.starttls()
            
            server.login(self.email_config.username, self.email_config.password)
            server.quit()
            
            return {
                'success': True,
                'message': '邮件配置测试成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'邮件配置测试失败: {str(e)}'
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
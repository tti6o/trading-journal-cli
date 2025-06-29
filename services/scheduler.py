"""
定时任务调度器

提供定时同步交易数据的功能，支持可配置的同步间隔。
采用关注点分离的设计，调度逻辑与业务逻辑解耦。
"""

import logging
import time
import signal
import sys
import configparser
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from core import journal as journal_core
from core import database as database_setup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务"""
    
    def __init__(self, config_file: str = 'config/config.ini'):
        """
        初始化调度器服务
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.scheduler: Optional[BackgroundScheduler] = None
        self.enabled = False
        self.sync_interval_hours = 4
        self.initial_sync_days = 30
        
        # 加载配置
        self._load_config()
        
        # 初始化调度器
        if self.enabled:
            self._init_scheduler()
    
    def _load_config(self) -> None:
        """从配置文件加载调度器设置"""
        try:
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            
            # 读取调度器配置
            if config.has_section('scheduler'):
                self.enabled = config.getboolean('scheduler', 'enabled', fallback=True)
                self.sync_interval_hours = config.getint('scheduler', 'sync_interval_hours', fallback=4)
                self.initial_sync_days = config.getint('scheduler', 'initial_sync_days', fallback=30)
            
            logger.info(f"调度器配置已加载: enabled={self.enabled}, "
                       f"interval={self.sync_interval_hours}h, initial_days={self.initial_sync_days}")
                       
        except Exception as e:
            logger.warning(f"加载配置文件失败，使用默认配置: {e}")
            # 使用默认配置
            self.enabled = True
            self.sync_interval_hours = 4
            self.initial_sync_days = 30
    
    def _init_scheduler(self) -> None:
        """初始化后台调度器"""
        try:
            self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
            
            # 添加事件监听器
            self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
            self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
            
            logger.info("后台调度器初始化成功")
            
        except Exception as e:
            logger.error(f"初始化调度器失败: {e}")
            self.scheduler = None
    
    def _job_executed_listener(self, event):
        """任务执行成功监听器"""
        logger.info(f"定时任务执行成功: {event.job_id}")
    
    def _job_error_listener(self, event):
        """任务执行失败监听器"""
        logger.error(f"定时任务执行失败: {event.job_id}, 异常: {event.exception}")
    
    def _do_sync(self) -> None:
        """执行数据同步任务"""
        try:
            logger.info("🕐 开始执行定时同步任务...")
            
            # 检查是否需要智能同步
            last_sync = database_setup.get_last_sync_timestamp()
            
            if last_sync:
                # 计算增量同步天数
                last_sync_time = datetime.fromisoformat(last_sync)
                time_diff = datetime.now() - last_sync_time
                sync_days = max(1, int(time_diff.total_seconds() / 86400) + 1)  # 至少同步1天
                
                logger.info(f"📅 上次同步时间: {last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"📊 本次增量同步: {sync_days} 天")
            else:
                # 首次同步，使用配置的初始天数
                sync_days = self.initial_sync_days
                logger.info(f"🆕 首次同步，同步最近 {sync_days} 天的数据")
            
            # 创建交易日志管理器并执行同步
            manager = journal_core.get_manager()
            result = manager.sync_trades(days=sync_days)
            
            if result['success']:
                # 更新同步时间戳
                database_setup.update_last_sync_timestamp()
                
                logger.info(f"✅ 定时同步任务完成!")
                logger.info(f"📊 新增交易记录: {result['new_count']} 条")
                logger.info(f"⏭️  跳过重复记录: {result['duplicate_count']} 条")
                logger.info(f"📈 数据库总记录数: {result['total_count']} 条")
                
                if result['new_count'] > 0:
                    logger.info("💡 建议查看最新的统计报告")
            else:
                logger.error(f"❌ 定时同步任务失败: {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ 执行定时同步任务时发生异常: {e}")
    
    def start(self) -> bool:
        """启动调度器服务"""
        if not self.enabled:
            logger.info("调度器已禁用，不启动定时任务")
            return False
        
        if not self.scheduler:
            logger.error("调度器未初始化，无法启动")
            return False
        
        try:
            # 添加定时任务
            self.scheduler.add_job(
                func=self._do_sync,
                trigger=IntervalTrigger(hours=self.sync_interval_hours),
                id='sync_trades_job',
                name='定时同步交易数据',
                replace_existing=True,
                max_instances=1  # 防止任务重叠执行
            )
            
            # 启动调度器
            self.scheduler.start()
            
            logger.info(f"🚀 定时同步服务已启动!")
            logger.info(f"⏰ 同步间隔: 每 {self.sync_interval_hours} 小时")
            logger.info(f"📅 下次同步时间: {datetime.now() + timedelta(hours=self.sync_interval_hours)}")
            
            return True
            
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            return False
    
    def stop(self) -> None:
        """停止调度器服务"""
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=True)
                logger.info("🛑 定时同步服务已停止")
            except Exception as e:
                logger.error(f"停止调度器时发生错误: {e}")
    
    def get_status(self) -> dict:
        """获取调度器状态信息"""
        if not self.scheduler:
            return {
                'running': False,
                'enabled': self.enabled,
                'error': '调度器未初始化'
            }
        
        jobs = self.scheduler.get_jobs()
        next_run_time = None
        
        if jobs:
            sync_job = next((job for job in jobs if job.id == 'sync_trades_job'), None)
            if sync_job:
                next_run_time = sync_job.next_run_time
        
        return {
            'running': self.scheduler.running,
            'enabled': self.enabled,
            'sync_interval_hours': self.sync_interval_hours,
            'next_run_time': next_run_time.isoformat() if next_run_time else None,
            'jobs_count': len(jobs),
            'last_sync': database_setup.get_last_sync_timestamp()
        }
    
    def trigger_sync_now(self) -> dict:
        """立即触发一次同步任务"""
        try:
            logger.info("🔥 手动触发同步任务...")
            self._do_sync()
            return {'success': True, 'message': '手动同步任务已完成'}
        except Exception as e:
            error_msg = f"手动同步失败: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}


def signal_handler(signum, frame):
    """信号处理器，用于优雅退出"""
    logger.info("接收到退出信号，正在关闭调度器...")
    if hasattr(signal_handler, 'scheduler_service'):
        signal_handler.scheduler_service.stop()
    sys.exit(0)


def run_scheduler_daemon():
    """运行调度器守护进程"""
    try:
        # 确保数据目录存在
        import os
        os.makedirs('data', exist_ok=True)
        
        # 初始化数据库
        database_setup.init_db()
        
        # 创建调度器服务
        scheduler_service = SchedulerService()
        
        # 设置信号处理器
        signal_handler.scheduler_service = scheduler_service
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动调度器
        if scheduler_service.start():
            logger.info("📱 调度器守护进程已启动，按 Ctrl+C 退出")
            
            # 保持主线程存活
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("接收到键盘中断信号")
        else:
            logger.error("调度器启动失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"调度器守护进程运行失败: {e}")
        sys.exit(1)
    finally:
        if 'scheduler_service' in locals():
            scheduler_service.stop()


if __name__ == '__main__':
    run_scheduler_daemon() 
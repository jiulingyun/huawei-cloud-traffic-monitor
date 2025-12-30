"""
监控逻辑服务

实现流量阈值判断、关机条件判断和监控日志记录
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

# 注意：数据库操作相关的方法需要在实际使用时传入正确的 Session 和模型


class MonitorLogic:
    """监控逻辑处理器"""
    
    @staticmethod
    def check_traffic_threshold(
        remaining_traffic: float,
        threshold: float
    ) -> Tuple[bool, str]:
        """
        检查流量是否低于阈值
        
        Args:
            remaining_traffic: 剩余流量（GB）
            threshold: 阈值（GB）
            
        Returns:
            (是否低于阈值, 判断结果描述)
        """
        is_below = remaining_traffic < threshold
        
        if is_below:
            percentage = (remaining_traffic / threshold * 100) if threshold > 0 else 0
            result_desc = (
                f"流量低于阈值 ({remaining_traffic:.2f}GB < {threshold:.2f}GB, "
                f"剩余 {percentage:.1f}%)"
            )
            logger.warning(result_desc)
        else:
            result_desc = f"流量正常 ({remaining_traffic:.2f}GB >= {threshold:.2f}GB)"
            logger.info(result_desc)
        
        return is_below, result_desc
    
    @staticmethod
    def should_trigger_shutdown(
        is_below_threshold: bool,
        config: Any,  # MonitorConfig 实例
        db: Any  # Session 实例
    ) -> Tuple[bool, str]:
        """
        判断是否应该触发关机
        
        Args:
            is_below_threshold: 是否低于阈值
            config: 监控配置
            db: 数据库会话
            
        Returns:
            (是否应该关机, 判断原因)
        """
        # 如果流量未低于阈值，不关机
        if not is_below_threshold:
            return False, "流量正常，无需关机"
        
        # 如果配置未启用自动关机，不关机
        if not getattr(config, 'auto_shutdown_enabled', False):
            return False, "流量低于阈值，但未启用自动关机"
        
        # 检查是否在关机冷却期
        # TODO: 实现关机冷却期检查（例如：上次关机后X小时内不再关机）
        
        # 检查是否有最近的关机记录
        # TODO: 查询最近的关机记录，避免频繁关机
        
        logger.info(f"触发关机条件: config_id={config.id}")
        
        return True, "流量低于阈值且启用自动关机"
    
    @staticmethod
    def create_monitor_log(
        db: Any,  # Session 实例
        account_id: int,
        remaining_traffic: float,
        threshold: float,
        is_below_threshold: bool,
        check_result: str,
        traffic_total: Optional[float] = None,
        traffic_used: Optional[float] = None,
        usage_percentage: Optional[float] = None,
        server_id: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Any:
        """
        创建监控日志
        
        Args:
            db: 数据库会话
            account_id: 账户 ID
            remaining_traffic: 剩余流量
            threshold: 阈值
            is_below_threshold: 是否低于阈值
            check_result: 检查结果描述
            traffic_total: 总流量
            traffic_used: 已用流量
            usage_percentage: 使用百分比
            server_id: 服务器 ID
            error_message: 错误信息（可选）
            
        Returns:
            创建的监控日志
        """
        try:
            from app.models.monitor_log import MonitorLog
            log = MonitorLog(
                account_id=account_id,
                server_id=server_id or 0,  # 如果没有指定服务器，使用 0 表示账户级别监控
                traffic_remaining=remaining_traffic,
                traffic_total=traffic_total,
                traffic_used=traffic_used,
                usage_percentage=usage_percentage,
                threshold=threshold,
                is_below_threshold=is_below_threshold,
                # 统一使用 UTC 存储时间，避免本地/UTC 混用导致前端解析错误
                check_time=datetime.utcnow(),
                message=check_result
            )
            
            db.add(log)
            db.commit()
            db.refresh(log)
            
            logger.info(
                f"监控日志已保存: log_id={log.id}, "
                f"account_id={account_id}, "
                f"is_below_threshold={is_below_threshold}"
            )
            
            return log
            
        except Exception as e:
            db.rollback()
            logger.error(f"保存监控日志失败: {e}")
            raise
    
    @staticmethod
    def get_monitor_logs(
        db: Any,  # Session 实例
        config_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Any]:
        """
        查询监控日志
        
        Args:
            db: 数据库会话
            config_id: 监控配置 ID（可选，过滤条件）
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            监控日志列表
        """
        from app.models.monitor_log import MonitorLog
        query = db.query(MonitorLog)
        
        if config_id is not None:
            query = query.filter(MonitorLog.config_id == config_id)
        
        query = query.order_by(MonitorLog.check_time.desc())
        query = query.limit(limit).offset(offset)
        
        logs = query.all()
        
        logger.info(f"查询监控日志: count={len(logs)}, config_id={config_id}")
        
        return logs
    
    @staticmethod
    def get_latest_log(
        db: Any,  # Session 实例
        config_id: int
    ) -> Optional[Any]:
        """
        获取最新的监控日志
        
        Args:
            db: 数据库会话
            config_id: 监控配置 ID
            
        Returns:
            最新的监控日志，不存在返回 None
        """
        from app.models.monitor_log import MonitorLog
        log = (
            db.query(MonitorLog)
            .filter(MonitorLog.config_id == config_id)
            .order_by(MonitorLog.check_time.desc())
            .first()
        )
        
        if log:
            logger.info(f"获取最新监控日志: log_id={log.id}, config_id={config_id}")
        else:
            logger.info(f"未找到监控日志: config_id={config_id}")
        
        return log
    
    @staticmethod
    def get_monitor_statistics(
        db: Any,  # Session 实例
        config_id: int
    ) -> Dict[str, Any]:
        """
        获取监控统计信息
        
        Args:
            db: 数据库会话
            config_id: 监控配置 ID
            
        Returns:
            统计信息字典
        """
        # 查询所有日志
        from app.models.monitor_log import MonitorLog
        logs = (
            db.query(MonitorLog)
            .filter(MonitorLog.config_id == config_id)
            .all()
        )
        
        total_checks = len(logs)
        below_threshold_count = sum(1 for log in logs if log.is_below_threshold)
        error_count = sum(1 for log in logs if log.error_message is not None)
        
        # 计算平均剩余流量
        if logs:
            avg_remaining = sum(log.remaining_traffic for log in logs) / len(logs)
            latest_log = max(logs, key=lambda x: x.check_time)
        else:
            avg_remaining = 0
            latest_log = None
        
        stats = {
            'config_id': config_id,
            'total_checks': total_checks,
            'below_threshold_count': below_threshold_count,
            'normal_count': total_checks - below_threshold_count - error_count,
            'error_count': error_count,
            'avg_remaining_traffic': round(avg_remaining, 2),
            'latest_check_time': latest_log.check_time.isoformat() if latest_log else None,
            'latest_remaining_traffic': latest_log.remaining_traffic if latest_log else None
        }
        
        logger.info(
            f"监控统计: config_id={config_id}, "
            f"total_checks={total_checks}, "
            f"below_threshold={below_threshold_count}"
        )
        
        return stats


class ThresholdCalculator:
    """阈值计算器"""
    
    @staticmethod
    def calculate_warning_threshold(
        threshold: float,
        warning_percentage: float = 0.2
    ) -> float:
        """
        计算预警阈值
        
        Args:
            threshold: 主阈值（GB）
            warning_percentage: 预警百分比（默认 20%）
            
        Returns:
            预警阈值（GB）
        """
        warning_threshold = threshold * (1 + warning_percentage)
        logger.debug(
            f"计算预警阈值: threshold={threshold}GB, "
            f"warning={warning_threshold}GB (+{warning_percentage*100}%)"
        )
        return warning_threshold
    
    @staticmethod
    def calculate_dynamic_threshold(
        historical_usage: List[float],
        safety_factor: float = 1.2
    ) -> float:
        """
        基于历史使用情况计算动态阈值
        
        Args:
            historical_usage: 历史流量使用列表（GB）
            safety_factor: 安全系数（默认 1.2，即预留 20% 缓冲）
            
        Returns:
            动态阈值（GB）
        """
        if not historical_usage:
            logger.warning("历史使用数据为空，无法计算动态阈值")
            return 0
        
        avg_usage = sum(historical_usage) / len(historical_usage)
        dynamic_threshold = avg_usage * safety_factor
        
        logger.info(
            f"计算动态阈值: avg_usage={avg_usage:.2f}GB, "
            f"threshold={dynamic_threshold:.2f}GB (safety_factor={safety_factor})"
        )
        
        return dynamic_threshold
    
    @staticmethod
    def is_trend_increasing(
        traffic_history: List[Tuple[datetime, float]],
        window_size: int = 5
    ) -> bool:
        """
        判断流量使用趋势是否在增加
        
        Args:
            traffic_history: 流量历史记录 [(时间, 剩余流量)]
            window_size: 滑动窗口大小
            
        Returns:
            是否呈增长趋势
        """
        if len(traffic_history) < window_size:
            return False
        
        # 取最近的记录
        recent = traffic_history[-window_size:]
        
        # 简单趋势判断：比较前半部分和后半部分的平均值
        mid = len(recent) // 2
        first_half_avg = sum(t[1] for t in recent[:mid]) / mid
        second_half_avg = sum(t[1] for t in recent[mid:]) / (len(recent) - mid)
        
        is_increasing = first_half_avg > second_half_avg
        
        logger.debug(
            f"流量趋势分析: first_avg={first_half_avg:.2f}GB, "
            f"second_avg={second_half_avg:.2f}GB, "
            f"is_increasing={is_increasing}"
        )
        
        return is_increasing


# 创建全局监控逻辑实例
monitor_logic = MonitorLogic()
threshold_calculator = ThresholdCalculator()

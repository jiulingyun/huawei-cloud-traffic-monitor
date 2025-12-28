#!/usr/bin/env python3
"""
测试监控逻辑服务
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.monitor_logic import MonitorLogic, ThresholdCalculator


def test_check_traffic_threshold():
    """测试流量阈值检查"""
    print("=" * 50)
    print("测试流量阈值检查")
    print("=" * 50)
    
    # 测试场景1: 流量低于阈值
    is_below, desc = MonitorLogic.check_traffic_threshold(
        remaining_traffic=50.0,
        threshold=100.0
    )
    print(f"✅ 场景1 - 流量低于阈值")
    print(f"   Result: is_below={is_below}, desc={desc}")
    assert is_below is True
    assert "50.00GB < 100.00GB" in desc
    
    # 测试场景2: 流量正常
    is_below, desc = MonitorLogic.check_traffic_threshold(
        remaining_traffic=150.0,
        threshold=100.0
    )
    print(f"✅ 场景2 - 流量正常")
    print(f"   Result: is_below={is_below}, desc={desc}")
    assert is_below is False
    assert "150.00GB >= 100.00GB" in desc
    
    # 测试场景3: 流量刚好等于阈值
    is_below, desc = MonitorLogic.check_traffic_threshold(
        remaining_traffic=100.0,
        threshold=100.0
    )
    print(f"✅ 场景3 - 流量等于阈值")
    print(f"   Result: is_below={is_below}, desc={desc}")
    assert is_below is False
    
    print("\n✅ 流量阈值检查测试通过！\n")


def test_calculate_warning_threshold():
    """测试预警阈值计算"""
    print("=" * 50)
    print("测试预警阈值计算")
    print("=" * 50)
    
    # 默认预警百分比 20%
    warning = ThresholdCalculator.calculate_warning_threshold(
        threshold=100.0
    )
    print(f"✅ 默认预警阈值（20%）")
    print(f"   Threshold: 100GB, Warning: {warning}GB")
    assert warning == 120.0
    
    # 自定义预警百分比 30%
    warning = ThresholdCalculator.calculate_warning_threshold(
        threshold=100.0,
        warning_percentage=0.3
    )
    print(f"✅ 自定义预警阈值（30%）")
    print(f"   Threshold: 100GB, Warning: {warning}GB")
    assert warning == 130.0
    
    print("\n✅ 预警阈值计算测试通过！\n")


def test_calculate_dynamic_threshold():
    """测试动态阈值计算"""
    print("=" * 50)
    print("测试动态阈值计算")
    print("=" * 50)
    
    # 基于历史使用数据
    historical_usage = [80.0, 85.0, 90.0, 88.0, 92.0]
    
    dynamic_threshold = ThresholdCalculator.calculate_dynamic_threshold(
        historical_usage=historical_usage,
        safety_factor=1.2
    )
    
    avg = sum(historical_usage) / len(historical_usage)
    expected = avg * 1.2
    
    print(f"✅ 动态阈值计算")
    print(f"   Historical Usage: {historical_usage}")
    print(f"   Average: {avg}GB")
    print(f"   Dynamic Threshold: {dynamic_threshold}GB (safety_factor=1.2)")
    print(f"   Expected: {expected}GB")
    
    assert abs(dynamic_threshold - expected) < 0.01
    
    # 测试空历史数据
    empty_threshold = ThresholdCalculator.calculate_dynamic_threshold(
        historical_usage=[],
        safety_factor=1.2
    )
    print(f"✅ 空历史数据")
    print(f"   Result: {empty_threshold}GB")
    assert empty_threshold == 0
    
    print("\n✅ 动态阈值计算测试通过！\n")


def test_is_trend_increasing():
    """测试流量趋势判断"""
    print("=" * 50)
    print("测试流量趋势判断")
    print("=" * 50)
    
    # 测试场景1: 流量递减趋势（剩余流量递减表示使用量递增）
    now = datetime.now()
    decreasing_traffic = [
        (now, 100.0),
        (now, 95.0),
        (now, 90.0),
        (now, 85.0),
        (now, 80.0)
    ]
    
    is_increasing = ThresholdCalculator.is_trend_increasing(
        traffic_history=decreasing_traffic,
        window_size=5
    )
    print(f"✅ 场景1 - 剩余流量递减（使用量递增）")
    print(f"   Traffic: 100 -> 95 -> 90 -> 85 -> 80")
    print(f"   Is Increasing: {is_increasing}")
    assert is_increasing is True
    
    # 测试场景2: 流量递增趋势（剩余流量递增表示使用量递减）
    increasing_traffic = [
        (now, 80.0),
        (now, 85.0),
        (now, 90.0),
        (now, 95.0),
        (now, 100.0)
    ]
    
    is_increasing = ThresholdCalculator.is_trend_increasing(
        traffic_history=increasing_traffic,
        window_size=5
    )
    print(f"✅ 场景2 - 剩余流量递增（使用量递减）")
    print(f"   Traffic: 80 -> 85 -> 90 -> 95 -> 100")
    print(f"   Is Increasing: {is_increasing}")
    assert is_increasing is False
    
    # 测试场景3: 数据不足
    short_traffic = [
        (now, 100.0),
        (now, 95.0)
    ]
    
    is_increasing = ThresholdCalculator.is_trend_increasing(
        traffic_history=short_traffic,
        window_size=5
    )
    print(f"✅ 场景3 - 数据不足")
    print(f"   Data Points: 2 (< window_size=5)")
    print(f"   Is Increasing: {is_increasing}")
    assert is_increasing is False
    
    print("\n✅ 流量趋势判断测试通过！\n")


def test_threshold_edge_cases():
    """测试阈值边界情况"""
    print("=" * 50)
    print("测试阈值边界情况")
    print("=" * 50)
    
    # 测试零阈值
    is_below, desc = MonitorLogic.check_traffic_threshold(
        remaining_traffic=50.0,
        threshold=0.0
    )
    print(f"✅ 零阈值测试")
    print(f"   Remaining: 50GB, Threshold: 0GB")
    print(f"   Result: is_below={is_below}")
    assert is_below is False
    
    # 测试负值流量（异常情况）
    is_below, desc = MonitorLogic.check_traffic_threshold(
        remaining_traffic=-10.0,
        threshold=100.0
    )
    print(f"✅ 负值流量测试")
    print(f"   Remaining: -10GB, Threshold: 100GB")
    print(f"   Result: is_below={is_below}")
    assert is_below is True
    
    # 测试非常小的差值
    is_below, desc = MonitorLogic.check_traffic_threshold(
        remaining_traffic=99.99,
        threshold=100.0
    )
    print(f"✅ 小差值测试")
    print(f"   Remaining: 99.99GB, Threshold: 100GB")
    print(f"   Result: is_below={is_below}")
    assert is_below is True
    
    print("\n✅ 阈值边界情况测试通过！\n")


if __name__ == "__main__":
    try:
        test_check_traffic_threshold()
        test_calculate_warning_threshold()
        test_calculate_dynamic_threshold()
        test_is_trend_increasing()
        test_threshold_edge_cases()
        
        print("=" * 50)
        print("🎉 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

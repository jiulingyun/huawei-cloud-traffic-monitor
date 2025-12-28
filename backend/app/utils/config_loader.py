"""
配置文件加载和管理
"""
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger


class ConfigLoader:
    """配置文件加载器"""
    
    def __init__(self, config_dir: str = "./config"):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        加载 YAML 配置文件
        
        Args:
            filename: 文件名
            
        Returns:
            配置字典
        """
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"成功加载配置文件: {filename}")
                return config or {}
        except Exception as e:
            logger.error(f"加载 YAML 配置失败: {e}")
            raise
    
    def save_yaml(self, filename: str, config: Dict[str, Any]) -> bool:
        """
        保存 YAML 配置文件
        
        Args:
            filename: 文件名
            config: 配置字典
            
        Returns:
            是否成功
        """
        file_path = self.config_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                logger.info(f"成功保存配置文件: {filename}")
                return True
        except Exception as e:
            logger.error(f"保存 YAML 配置失败: {e}")
            return False
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """
        加载 JSON 配置文件
        
        Args:
            filename: 文件名
            
        Returns:
            配置字典
        """
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"成功加载配置文件: {filename}")
                return config
        except Exception as e:
            logger.error(f"加载 JSON 配置失败: {e}")
            raise
    
    def save_json(self, filename: str, config: Dict[str, Any], indent: int = 2) -> bool:
        """
        保存 JSON 配置文件
        
        Args:
            filename: 文件名
            config: 配置字典
            indent: 缩进空格数
            
        Returns:
            是否成功
        """
        file_path = self.config_dir / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=indent)
                logger.info(f"成功保存配置文件: {filename}")
                return True
        except Exception as e:
            logger.error(f"保存 JSON 配置失败: {e}")
            return False
    
    def load_config(self, filename: str, format: str = 'auto') -> Dict[str, Any]:
        """
        自动检测格式并加载配置文件
        
        Args:
            filename: 文件名
            format: 格式（auto/yaml/json）
            
        Returns:
            配置字典
        """
        if format == 'auto':
            # 根据文件扩展名自动判断
            if filename.endswith(('.yaml', '.yml')):
                return self.load_yaml(filename)
            elif filename.endswith('.json'):
                return self.load_json(filename)
            else:
                logger.warning(f"无法识别的配置文件格式: {filename}，尝试使用 YAML")
                return self.load_yaml(filename)
        elif format == 'yaml':
            return self.load_yaml(filename)
        elif format == 'json':
            return self.load_json(filename)
        else:
            raise ValueError(f"不支持的配置格式: {format}")
    
    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并多个配置字典
        
        Args:
            *configs: 配置字典列表
            
        Returns:
            合并后的配置
        """
        result = {}
        for config in configs:
            result.update(config)
        return result
    
    def get_config_value(
        self,
        config: Dict[str, Any],
        key_path: str,
        default: Any = None
    ) -> Any:
        """
        获取嵌套配置值
        
        Args:
            config: 配置字典
            key_path: 键路径（用.分隔，如: 'database.host'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value


# 创建全局配置加载器实例
config_loader = ConfigLoader()

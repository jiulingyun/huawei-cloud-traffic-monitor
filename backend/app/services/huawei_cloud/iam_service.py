"""
华为云 IAM 服务

用于获取 Token 和项目列表，支持账户下所有区域的服务器查询

华为云 IAM API 支持两种认证方式：
1. Token 认证 - 需要先获取 Token
2. AK/SK 签名认证 - 直接使用 AK/SK 签名

本服务使用全局 IAM 端点 (https://iam.myhuaweicloud.com) 调用 /v3/auth/projects 接口
获取账户下所有项目（各区域）信息
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import quote
from loguru import logger
import requests
import hashlib
import hmac
from datetime import datetime


# IAM 全局端点
IAM_GLOBAL_ENDPOINT = "https://iam.myhuaweicloud.com"


@dataclass
class Project:
    """项目信息"""
    id: str
    name: str  # 区域名，如 cn-north-4
    domain_id: str
    enabled: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "domain_id": self.domain_id,
            "enabled": self.enabled
        }


class IAMService:
    """
    华为云 IAM 服务
    
    用于获取项目列表，支持跨区域查询服务器
    """
    
    def __init__(self, ak: str, sk: str):
        """
        初始化 IAM 服务
        
        Args:
            ak: Access Key
            sk: Secret Key
        """
        self.ak = ak
        self.sk = sk
        self.endpoint = IAM_GLOBAL_ENDPOINT
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        logger.info("初始化 IAM 服务")
    
    def _sign_request(
        self,
        method: str,
        uri: str,
        query_params: Optional[Dict[str, str]] = None,
        body: str = ""
    ) -> Dict[str, str]:
        """
        生成 AK/SK 签名
        
        使用华为云 SDK-HMAC-SHA256 签名算法
        """
        # 规范化 URI
        canonical_uri = '/'.join(
            quote(segment, safe='')
            for segment in uri.split('/')
        )
        if not canonical_uri.endswith('/'):
            canonical_uri += '/'
        
        # 规范化查询字符串
        canonical_query_string = ""
        if query_params:
            sorted_params = sorted(query_params.items())
            canonical_query_string = "&".join(
                f"{quote(k, safe='')}={quote(str(v), safe='')}"
                for k, v in sorted_params
            )
        
        # 获取当前时间戳
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        # 提取主机名
        host = self.endpoint.replace('https://', '').replace('http://', '')
        
        # 规范化请求头
        signed_headers_str = "content-type;host;x-sdk-date"
        canonical_headers = f"content-type:application/json\nhost:{host}\nx-sdk-date:{timestamp}\n"
        
        # 计算请求体哈希
        hashed_request_payload = hashlib.sha256(body.encode('utf-8')).hexdigest()
        
        # 构建规范请求
        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{canonical_query_string}\n"
            f"{canonical_headers}\n"
            f"{signed_headers_str}\n"
            f"{hashed_request_payload}"
        )
        
        # 计算签名
        string_to_sign = (
            f"SDK-HMAC-SHA256\n"
            f"{timestamp}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        
        signature = hmac.new(
            self.sk.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'X-Sdk-Date': timestamp,
            'Host': host,
            'Authorization': (
                f'SDK-HMAC-SHA256 '
                f'Access={self.ak}, '
                f'SignedHeaders={signed_headers_str}, '
                f'Signature={signature}'
            )
        }
    
    def list_projects(self) -> List[Project]:
        """
        获取账户下所有项目列表
        
        调用 GET /v3/auth/projects 接口
        该接口返回当前用户可访问的所有项目（即所有区域）
        
        Returns:
            项目列表，每个项目包含 id 和 name（区域名）
        """
        logger.info("获取项目列表")
        
        uri = "/v3/auth/projects"
        url = f"{self.endpoint}{uri}"
        
        headers = self._sign_request(
            method="GET",
            uri=uri,
            body=""
        )
        
        try:
            logger.info(f"发送 IAM API 请求: GET {url}")
            
            response = self.session.request(
                method="GET",
                url=url,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"IAM API 响应: status={response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            projects = self._parse_projects(data)
            
            logger.info(f"获取到 {len(projects)} 个项目")
            return projects
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"IAM API 请求失败: {e}"
            try:
                error_detail = e.response.json()
                error_msg += f", 详情: {error_detail}"
            except:
                pass
            logger.error(error_msg)
            raise IAMException(error_msg)
        except Exception as e:
            logger.error(f"IAM API 请求异常: {e}")
            raise IAMException(f"请求异常: {e}")
    
    def _parse_projects(self, response: Dict[str, Any]) -> List[Project]:
        """解析项目列表响应"""
        projects = []
        project_list = response.get("projects", [])
        
        # 常见的 ECS 支持区域
        ecs_regions = {
            'cn-north-1', 'cn-north-4', 'cn-north-9',
            'cn-east-2', 'cn-east-3',
            'cn-south-1', 'cn-south-2',
            'cn-southwest-2',
            'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3',
            'af-south-1', 'la-south-2', 'sa-brazil-1',
            'la-north-2', 'na-mexico-1',
            'eu-west-0', 'eu-west-101',
            'tr-west-1', 'me-east-1', 'ru-northwest-2',
        }
        
        for p in project_list:
            name = p.get("name", "")
            project_id = p.get("id", "")
            
            # 过滤掉非区域项目（如 MOS 等特殊项目）
            # 区域名通常是如 cn-north-4 的格式
            if not name or not project_id:
                continue
            
            # 只保留 ECS 支持的区域
            if name not in ecs_regions:
                logger.debug(f"跳过非 ECS 区域项目: {name}")
                continue
            
            project = Project(
                id=project_id,
                name=name,
                domain_id=p.get("domain_id", ""),
                enabled=p.get("enabled", True)
            )
            projects.append(project)
            logger.debug(f"解析项目: id={project_id}, region={name}")
        
        return projects
    
    def get_project_by_region(self, region: str) -> Optional[Project]:
        """
        获取指定区域的项目
        
        Args:
            region: 区域名称（如 cn-north-4）
            
        Returns:
            项目信息，未找到返回 None
        """
        projects = self.list_projects()
        
        for project in projects:
            if project.name == region:
                return project
        
        return None


class IAMException(Exception):
    """IAM 服务异常"""
    pass

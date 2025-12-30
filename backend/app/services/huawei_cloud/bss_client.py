"""
华为云 BSS (Business Support System) API 客户端
用于调用计费相关的 API，如流量包查询
"""
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Optional, Any
import requests
from urllib.parse import quote
from loguru import logger


class HuaweiCloudBSSClient:
    """华为云 BSS API 客户端"""
    
    # BSS 服务端点
    ENDPOINTS = {
        'cn': 'https://bss.myhuaweicloud.com',      # 中国站
        'intl': 'https://bss-intl.myhuaweicloud.com'  # 国际站
    }
    
    def __init__(self, access_key: str, secret_key: str, is_international: bool = False):
        """
        初始化 BSS 客户端
        
        Args:
            access_key: Access Key
            secret_key: Secret Key
            is_international: 是否国际站账户
        """
        self.ak = access_key
        self.sk = secret_key
        self.is_international = is_international
        self.endpoint = self.ENDPOINTS['intl'] if is_international else self.ENDPOINTS['cn']
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'huawei-cloud-monitor/1.0'
        })
        
        logger.info(f"初始化 BSS 客户端: endpoint={self.endpoint}")
    
    def _sign_request(
        self,
        method: str,
        uri: str,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: str = ""
    ) -> Dict[str, str]:
        """
        生成请求签名 (SDK-HMAC-SHA256)
        
        Args:
            method: HTTP 方法
            uri: 请求 URI
            query_params: 查询参数
            headers: 请求头
            body: 请求体
            
        Returns:
            签名后的请求头
        """
        # 规范化 URI：对路径中每个部分单独进行 URL 编码
        # 华为云要求保留 '/' 不编码，但对每个路径段进行编码
        canonical_uri = '/'.join(
            quote(segment, safe='')
            for segment in uri.split('/')
        )
        # 确保以 / 结尾（华为云签名规范要求）
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
        
        # 规范化请求头
        signed_headers_str = "content-type;host;x-sdk-date"
        
        # 获取当前时间戳
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        # 提取主机名
        host = self.endpoint.replace('https://', '').replace('http://', '')
        
        # 构建规范请求头
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
        
        # 返回签名请求头
        auth_headers = {
            'X-Sdk-Date': timestamp,
            'Host': host,
            'Authorization': (
                f'SDK-HMAC-SHA256 '
                f'Access={self.ak}, '
                f'SignedHeaders={signed_headers_str}, '
                f'Signature={signature}'
            )
        }
        
        if headers:
            auth_headers.update(headers)
        
        return auth_headers
    
    def _request(
        self,
        method: str,
        uri: str,
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            uri: 请求 URI
            query_params: 查询参数
            body: 请求体
            timeout: 超时时间（秒）
            
        Returns:
            响应 JSON
            
        Raises:
            HuaweiCloudBSSException: API 调用失败
        """
        # 构建完整 URL
        url = f"{self.endpoint}{uri}"
        
        # 请求体序列化
        body_str = json.dumps(body) if body else ""
        
        # 生成签名
        headers = self._sign_request(
            method=method,
            uri=uri,
            query_params=query_params,
            body=body_str
        )
        
        try:
            logger.info(f"发送 BSS API 请求: {method} {url}")
            logger.debug(f"请求体: {body_str}")
            
            response = self.session.request(
                method=method,
                url=url,
                params=query_params,
                data=body_str if body_str else None,
                headers=headers,
                timeout=timeout
            )
            
            logger.info(f"BSS API 响应: status={response.status_code}")
            
            # 检查响应状态
            if response.status_code >= 400:
                error_msg = f"BSS API 请求失败: HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f", 详情: {error_detail}"
                except:
                    error_msg += f", 响应: {response.text}"
                logger.error(error_msg)
                raise HuaweiCloudBSSException(error_msg)
            
            # 解析响应
            if response.text:
                return response.json()
            return {}
            
        except requests.exceptions.Timeout:
            logger.error(f"BSS API 请求超时: {url}")
            raise HuaweiCloudBSSException("请求超时")
        except HuaweiCloudBSSException:
            raise
        except Exception as e:
            logger.error(f"BSS API 请求异常: {e}")
            raise HuaweiCloudBSSException(f"请求异常: {e}")
    
    def get(
        self,
        uri: str,
        query_params: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """GET 请求"""
        return self._request('GET', uri, query_params=query_params, timeout=timeout)
    
    def post(
        self,
        uri: str,
        body: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """POST 请求"""
        return self._request('POST', uri, query_params=query_params, body=body, timeout=timeout)


class HuaweiCloudBSSException(Exception):
    """华为云 BSS API 异常"""
    pass

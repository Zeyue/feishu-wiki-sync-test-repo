import os
import json
import requests
import urllib3
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
from pathlib import Path
from typing import Optional, Dict
import logging
from dotenv import load_dotenv

# 禁用所有警告
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class FeishuDocUploader:
    """飞书文档上传器"""
    
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.base_url = "https://open.feishu.cn/open-apis"
        self.token = None
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        
        # 完全禁用 SSL 验证
        session.verify = False
        session.trust_env = False
        
        # 配置重试策略
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        
        # 配置适配器
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        
        # 设置请求头
        session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        return session
    
    def get_access_token(self) -> Optional[str]:
        """获取访问令牌"""
        try:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            logger.info(f"正在请求访问令牌，APP_ID: {self.app_id}")
            logger.info(f"请求URL: {url}")
            
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json'
            }
            
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = self.session.post(
                url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    self.token = result["tenant_access_token"]
                    return self.token
            
            logger.error(f"获取令牌失败: {response.text}")
            return None
            
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL证书错误: {str(e)}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {str(e)}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取令牌时发生错误: {str(e)}")
            logger.exception(e)  # 打印完整的错误堆栈
            return None
    
    def get_headers(self) -> Dict:
        """获取请求头"""
        if not self.token:
            self.get_access_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def upload_markdown(self, file_path: str, space_id: str, parent_token: str) -> Optional[str]:
        """上传Markdown文件到飞书知识库"""
        try:
            # 读取并处理文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 确保内容不为空
            if not content.strip():
                logger.error(f"文件内容为空: {file_path}")
                return None
            
            # 构造请求数据
            payload = {
                "title": Path(file_path).stem,
                "parent_node_token": parent_token,
                "node_type": "origin",
                "obj_type": "doc",
                "content": content
            }
            
            logger.debug(f"请求数据: {json.dumps(payload, ensure_ascii=False)}")
            
            # 发送请求
            url = f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes"
            logger.info(f"请求URL: {url}")
            
            response = self.session.post(
                url,
                headers=self.get_headers(),
                json=payload
            )
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    node_token = result["data"]["node_token"]
                    logger.info(f"文档上传成功: {file_path} -> {node_token}")
                    return node_token
                else:
                    logger.error(f"API返回错误: {result.get('msg')}")
            else:
                logger.error(f"HTTP请求失败: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.error(f"上传文档时发生错误: {str(e)}")
            logger.exception(e)
            return None

    def test_connection(self):
        """测试与飞书服务器的连接"""
        try:
            logger.info("正在测试与飞书服务器的连接...")
            test_url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            
            logger.info(f"尝试连接: {test_url}")
            response = self.session.post(
                test_url,
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                },
                timeout=30
            )
            
            logger.info(f"连接成功: 状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    logger.info("认证接口测试成功")
                    return True
                
            logger.error(f"认证接口测试失败: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            logger.exception(e)
            return False

def main():
    """主函数"""
    # 获取配置
    space_id = os.getenv("FEISHU_WIKI_ID")
    parent_token = os.getenv("FEISHU_PARENT_TOKEN")
    docs_dir = "doc"  # 文档目录
    
    # 检查文档目录
    if not os.path.exists(docs_dir):
        logger.error(f"文档目录不存在: {docs_dir}")
        return
        
    # 检查是否有 Markdown 文件
    md_files = []
    for root, _, files in os.walk(docs_dir):
        md_files.extend([os.path.join(root, f) for f in files if f.endswith('.md')])
    
    if not md_files:
        logger.error(f"未找到 Markdown 文件在目录: {docs_dir}")
        return
        
    logger.info(f"找到 {len(md_files)} 个 Markdown 文件")
    for f in md_files:
        logger.info(f"- {f}")
    
    # 初始化上传器
    uploader = FeishuDocUploader()
    
    # 测试连接
    if not uploader.test_connection():
        logger.error("无法连接到飞书服务器，请检查网络设置")
        return
    
    # 验证认证
    if not uploader.get_access_token():
        logger.error("获取访问令牌失败")
        return
    
    # 遍历上传文档
    success_count = 0
    fail_count = 0
    
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                logger.info(f"正在处理: {file_path}")
                
                if uploader.upload_markdown(file_path, space_id, parent_token):
                    success_count += 1
                else:
                    fail_count += 1
    
    logger.info(f"同步完成! 成功: {success_count}, 失败: {fail_count}")

if __name__ == "__main__":
    main() 
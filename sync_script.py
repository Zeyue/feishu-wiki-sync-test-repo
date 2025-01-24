import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, List
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FeishuAPI:
    """飞书 API 客户端"""
    
    def __init__(self):
        """初始化飞书API客户端"""
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.base_url = "https://open.feishu.cn/open-apis"
        self.token = None
    
    def get_access_token(self) -> Optional[str]:
        """
        获取飞书访问令牌
        Returns:
            str: 访问令牌
        """
        try:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            response = requests.post(
                url,
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                }
            )
            response.raise_for_status()
            self.token = response.json()["tenant_access_token"]
            return self.token
        except Exception as e:
            logger.error(f"获取访问令牌失败: {str(e)}")
            return None

    def get_headers(self) -> Dict:
        """
        获取请求头
        Returns:
            Dict: 包含认证信息的请求头
        """
        if not self.token:
            self.get_access_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_wiki_doc(self, space_id: str, parent_token: str, title: str, content: str) -> Optional[str]:
        """
        在知识库中创建文档
        Args:
            space_id: 知识库ID
            parent_token: 父节点token
            title: 文档标题
            content: 文档内容
        Returns:
            str: 创建的文档node_token
        """
        try:
            url = f"{self.base_url}/wiki/v2/spaces/{space_id}/documents"
            payload = {
                "parent_node_token": parent_token,
                "title": title,
                "content": content,
                "obj_type": "doc"
            }
            
            response = requests.post(
                url,
                headers=self.get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                logger.info(f"文档创建成功: {title}")
                return result["data"]["node_token"]
            else:
                logger.error(f"文档创建失败: {result.get('msg')}")
                return None
                
        except Exception as e:
            logger.error(f"创建文档时发生错误: {str(e)}")
            return None

class GitHubAPI:
    """GitHub API 客户端"""
    
    def __init__(self):
        """初始化GitHub API客户端"""
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_repo_content(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """
        获取仓库内容
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            path: 文件路径
        Returns:
            List[Dict]: 仓库内容列表
        """
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取仓库内容失败: {str(e)}")
            return []

def main():
    """主函数"""
    # 初始化API客户端
    feishu = FeishuAPI()
    github = GitHubAPI()
    
    # 获取环境变量
    space_id = os.getenv("FEISHU_WIKI_ID")
    parent_token = os.getenv("FEISHU_PARENT_TOKEN")
    github_owner = os.getenv("GITHUB_OWNER")
    github_repo = os.getenv("GITHUB_REPO")
    
    if not all([space_id, parent_token, github_owner, github_repo]):
        logger.error("缺少必要的环境变量配置")
        return
    
    # 获取GitHub仓库内容
    contents = github.get_repo_content(github_owner, github_repo)
    
    # 同步文件到飞书知识库
    for item in contents:
        if item["type"] == "file" and item["name"].endswith(".md"):
            try:
                # 获取文件内容
                response = requests.get(item["download_url"])
                content = response.text
                
                # 创建飞书文档
                doc_token = feishu.create_wiki_doc(
                    space_id=space_id,
                    parent_token=parent_token,
                    title=Path(item["name"]).stem,
                    content=content
                )
                
                if doc_token:
                    logger.info(f"文件 {item['name']} 同步成功")
                else:
                    logger.error(f"文件 {item['name']} 同步失败")
                    
            except Exception as e:
                logger.error(f"处理文件 {item['name']} 时发生错误: {str(e)}")

if __name__ == "__main__":
    main() 
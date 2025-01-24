import os
import logging
from dotenv import load_dotenv
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class WikiNodeFetcher:
    """知识库节点获取器"""
    
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.base_url = "https://open.feishu.cn/open-apis"
        self.token = None
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        session.verify = False
        session.proxies = {'http': None, 'https': None}
        return session
    
    def get_access_token(self) -> bool:
        """获取访问令牌"""
        try:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            response = self.session.post(
                url,
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    self.token = result["tenant_access_token"]
                    return True
            
            logger.error(f"获取令牌失败: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"获取令牌时发生错误: {str(e)}")
            return False
    
    def get_space_nodes(self, space_id: str):
        """获取知识库节点"""
        if not self.token and not self.get_access_token():
            return
        
        try:
            url = f"{self.base_url}/wiki/v2/spaces/{space_id}/nodes"
            response = self.session.get(
                url,
                headers={"Authorization": f"Bearer {self.token}"},
                params={"page_size": 50}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    nodes = result["data"]["items"]
                    print("\n知识库节点列表:")
                    print("-" * 50)
                    for node in nodes:
                        print(f"节点名称: {node['title']}")
                        print(f"节点Token: {node['node_token']}")
                        print(f"节点类型: {node['obj_type']}")
                        if node.get('parent_node_token'):
                            print(f"父节点Token: {node['parent_node_token']}")
                        print("-" * 50)
                else:
                    logger.error(f"获取节点失败: {result.get('msg')}")
            else:
                logger.error(f"请求失败: {response.text}")
                
        except Exception as e:
            logger.error(f"获取节点时发生错误: {str(e)}")

def main():
    """主函数"""
    # 获取知识库ID
    space_id = os.getenv("FEISHU_WIKI_ID")
    if not space_id:
        logger.error("请在.env文件中设置 FEISHU_WIKI_ID")
        return
    
    # 获取节点信息
    fetcher = WikiNodeFetcher()
    fetcher.get_space_nodes(space_id)
    
    print("\n使用说明:")
    print("1. 从上面的节点列表中找到您想要上传文档的目标目录")
    print("2. 复制对应的节点Token")
    print("3. 将节点Token更新到 .env 文件的 FEISHU_PARENT_TOKEN 配置项中")

if __name__ == "__main__":
    main() 
# GitHub仓库同步到飞书知识库工具

## 项目简介
本项目旨在实现GitHub仓库内容到飞书知识库的自动同步功能，并为后续Coze平台智能体的接入做准备。

## 功能特性
1. GitHub仓库同步
   - 支持指定GitHub仓库的同步
   - 支持选择性同步指定目录或文件
   - 支持Markdown文件的格式转换
   
2. 飞书知识库集成
   - 自动创建知识库目录结构
   - 保持文档层级关系
   - 支持文档更新检测

3. 自动化部署
   - 通过GitHub Actions实现自动同步
   - 支持定时同步
   - 支持手动触发同步

## 技术架构
- 编程语言：Python
- 依赖服务：
  - GitHub API
  - 飞书开放API
  - GitHub Actions

## 使用说明
1. 配置要求
   - GitHub Personal Access Token
   - 飞书应用凭证（App ID和App Secret）
   - 目标知识库ID

2. 环境变量配置
   ```env
   GITHUB_TOKEN=your_github_token
   FEISHU_APP_ID=your_feishu_app_id
   FEISHU_APP_SECRET=your_feishu_app_secret
   FEISHU_WIKI_ID=your_wiki_id
   ```

3. 运行方式
   - 本地运行：`python sync_script.py`
   - GitHub Actions自动运行（每日凌晨2点）
   - 手动触发工作流

## 开发计划
1. 第一阶段：基础同步功能
   - [x] 项目初始化
   - [ ] GitHub仓库内容获取
   - [ ] 飞书知识库API对接
   - [ ] 文档同步基础功能

2. 第二阶段：增强功能
   - [ ] 增量同步支持
   - [ ] 文档格式转换优化
   - [ ] 同步日志与监控

3. 第三阶段：自动化集成
   - [ ] GitHub Actions配置
   - [ ] 错误处理和通知
   - [ ] 使用文档完善

## 注意事项
- 确保飞书应用具有知识库的读写权限
- GitHub Token需要有仓库的读取权限
- 建议在同步前备份重要文档

## 贡献指南
欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证
MIT License 
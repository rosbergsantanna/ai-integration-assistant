# AI整合助手 🤖

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/velist/ai-integration-assistant.svg)](https://github.com/velist/ai-integration-assistant/stargazers)

**可自定义配置的多AI协助分析工具**，支持通过API调用智谱轻言、硅基流动等多个AI服务，提供规范化输出格式，专为Claude Code环境优化。

![Demo](https://img.shields.io/badge/Demo-Available-brightgreen)
![Status](https://img.shields.io/badge/Status-Active-success)

## 核心功能

- **多AI服务整合**: 支持智谱轻言、硅基流动、OpenAI等多个AI服务
- **统一API接口**: 封装不同AI服务的调用差异，提供统一的使用方式  
- **规范化输出**: 标准化AI响应格式，支持表格和详细分析视图
- **配置化管理**: 灵活的配置文件系统，支持项目级别配置
- **Claude Code集成**: 专为Claude Code环境优化的输出样式

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化配置

```bash
python ai_assistant_cli.py init
```

### 3. 配置AI服务

```bash
# 配置智谱轻言
python ai_assistant_cli.py config zhipu sk-your-api-key

# 配置硅基流动  
python ai_assistant_cli.py config silicon sk-your-api-key
```

### 4. 查看服务状态

```bash
python ai_assistant_cli.py list
```

### 5. 开始使用

```bash
# 分析文本内容
python ai_assistant_cli.py analyze "请分析这段代码的性能问题"

# 代码审查
python ai_assistant_cli.py code-review src/main.py

# 错误分析
python ai_assistant_cli.py error "IndexError: list index out of range" -c bug_code.py
```

## 主要组件

### 1. AI服务管理器 (`src/ai_service_manager.py`)
- 统一的AI服务调用接口
- 异步并发调用支持
- 错误处理和重试机制
- 免费模型优先使用

### 2. 输出格式化器 (`src/output_formatter.py`)  
- 多种输出格式支持（表格、详细、综合）
- 响应内容清理和格式化
- 置信度和性能指标显示
- Claude Code适配的输出样式

### 3. 命令行接口 (`ai_assistant_cli.py`)
- 完整的CLI命令支持
- 配置管理功能
- 批量分析和结果保存
- 服务状态监控

### 4. 配置文件
- `.claude/ai-services-config.json`: AI服务配置
- `.claude/output-styles/AI整合助手.json`: 输出样式配置

## 配置文件说明

### AI服务配置 (`.claude/ai-services-config.json`)

包含各个AI服务的API配置、模型信息和提示词模板：

```json
{
  "services": {
    "zhipu": {
      "name": "智谱轻言",
      "api_base": "https://open.bigmodel.cn/api/paas/v4/chat/completions", 
      "api_key": "your-api-key",
      "models": {
        "glm-4-flash": {
          "name": "GLM-4-Flash",
          "type": "free"
        }
      }
    }
  }
}
```

### 输出样式配置

支持自定义输出格式、表格样式、AI响应前缀等：

```json
{
  "settings": {
    "output_format": {
      "ai_output_prefix": "[{ai_name}]: ",
      "use_tables": true
    }
  }
}
```

## 使用示例

### 在Claude Code中使用

1. 配置输出样式后，Claude Code会自动使用AI整合助手的格式
2. 多AI分析结果会以表格形式展示
3. 支持 `[服务名]:` 格式的规范化输出

### 代码分析示例

```bash
python ai_assistant_cli.py code-review main.py --save analysis_result.md
```

输出格式：
```
| AI服务 | 模型 | 状态 | 分析结果预览 | 置信度 | 响应时间 |
|--------|------|------|-------------|--------|----------|
| 智谱轻言 | glm-4-flash | ✅ 成功 | 代码结构清晰，建议添加错误处理... | 8.5/10 | 1.2s |
| 硅基流动 | deepseek-v2.5 | ✅ 成功 | 性能良好，可以优化循环逻辑... | 7.8/10 | 2.1s |
```

## 命令参考

| 命令 | 功能 | 示例 |
|------|------|------|
| `init` | 初始化配置 | `python ai_assistant_cli.py init` |
| `config` | 配置AI服务 | `python ai_assistant_cli.py config zhipu sk-xxx` |
| `list` | 查看服务状态 | `python ai_assistant_cli.py list -v` |  
| `analyze` | 分析内容 | `python ai_assistant_cli.py analyze "内容"` |
| `code-review` | 代码审查 | `python ai_assistant_cli.py code-review file.py` |
| `error` | 错误分析 | `python ai_assistant_cli.py error "错误信息"` |
| `test` | 测试连接 | `python ai_assistant_cli.py test -v` |

## 支持的AI服务

- **智谱轻言**: GLM-4系列模型，支持免费的GLM-4-Flash
- **硅基流动**: DeepSeek、Qwen、Llama等多种免费模型
- **OpenAI**: GPT系列模型（需付费API）

## 扩展开发

### 添加新的AI服务

1. 在 `ai-services-config.json` 中添加服务配置
2. 按需修改 `AIServiceManager` 的调用逻辑
3. 更新输出格式化器的服务名称映射

### 自定义输出格式

1. 修改 `.claude/output-styles/AI整合助手.json` 配置
2. 在 `OutputFormatter` 类中添加新的格式化方法
3. 更新模板定义

## 🎯 适用场景

- **代码审查**: 多AI视角的代码质量分析
- **错误诊断**: 快速定位和解决问题  
- **技术调研**: 获取多方面的技术见解
- **学习辅助**: 理解复杂概念和最佳实践
- **Claude Code集成**: 无缝集成到开发工作流

## 🔮 未来规划

- [ ] 支持更多AI服务提供商
- [ ] 添加批量文件分析功能
- [ ] 实现分析结果缓存机制
- [ ] 开发Web界面版本
- [ ] 集成代码质量评分系统

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)  
5. 开启Pull Request

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/velist/ai-integration-assistant/issues)
- 讨论区: [GitHub Discussions](https://github.com/velist/ai-integration-assistant/discussions)

## 🙏 致谢

感谢以下AI服务提供商：
- [智谱轻言](https://open.bigmodel.cn/) - 提供GLM系列模型
- [硅基流动](https://siliconflow.cn/) - 提供多种开源模型API
- [OpenAI](https://openai.com/) - GPT系列模型

## ⭐ Star History

如果这个项目对您有帮助，请给它一个星标！⭐

[![Star History Chart](https://api.star-history.com/svg?repos=velist/ai-integration-assistant&type=Date)](https://star-history.com/#velist/ai-integration-assistant&Date)

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

**注意**: 本项目仅供学习和研究使用，请遵守各AI服务商的使用条款。使用前请确保您有合法的API访问权限。
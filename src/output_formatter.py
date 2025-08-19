#!/usr/bin/env python3
"""
Output Formatter - AI输出格式化Agent
负责将多个AI服务的输出统一格式化为指定样式
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ai_service_manager import AIResponse


@dataclass
class FormattedOutput:
    """格式化输出数据类"""
    content: str
    format_type: str
    metadata: Dict[str, Any]


class OutputFormatter:
    """输出格式化器"""
    
    def __init__(self, style_config_path: str = None):
        """
        初始化输出格式化器
        
        Args:
            style_config_path: 输出样式配置文件路径
        """
        self.style_config_path = style_config_path or ".claude/output-styles/AI整合助手.json"
        self.style_config = self._load_style_config()
    
    def _load_style_config(self) -> Dict:
        """加载输出样式配置"""
        try:
            with open(self.style_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 返回默认配置
            return {
                "settings": {
                    "output_format": {
                        "ai_output_prefix": "[{ai_name}]: ",
                        "use_tables": True,
                        "section_headers": True,
                        "code_blocks": True
                    }
                },
                "templates": {
                    "analysis_output": "| AI服务 | 模型 | 分析结果 | 置信度 |\n|--------|------|----------|--------|\n| {ai_name} | {model} | {analysis} | {confidence} |",
                    "ai_response": "[{ai_name}]: {response}",
                    "summary_format": "## 综合分析\n\n{combined_analysis}\n\n## 建议操作\n\n{recommendations}"
                }
            }
    
    def format_single_ai_response(self, response: AIResponse) -> str:
        """
        格式化单个AI响应
        
        Args:
            response: AI响应对象
            
        Returns:
            str: 格式化后的输出
        """
        template = self.style_config.get("templates", {}).get("ai_response", "[{ai_name}]: {response}")
        
        if not response.success:
            return template.format(
                ai_name=response.service_name,
                response=f"调用失败: {response.error_message}"
            )
        
        # 处理输出内容
        content = self._clean_content(response.content)
        
        # 添加置信度和响应时间信息
        metadata = f" (置信度: {response.confidence:.1f}/10, 响应时间: {response.response_time:.2f}s)"
        
        return template.format(
            ai_name=response.service_name,
            response=content + metadata
        )
    
    def format_analysis_table(self, responses: List[AIResponse]) -> str:
        """
        格式化为分析表格
        
        Args:
            responses: AI响应列表
            
        Returns:
            str: 表格格式的分析结果
        """
        if not responses:
            return "无AI分析数据"
        
        # 表格头部
        table_lines = [
            "| AI服务 | 模型 | 状态 | 分析结果预览 | 置信度 | 响应时间 |",
            "|--------|------|------|-------------|--------|----------|"
        ]
        
        for response in responses:
            service_name = self._get_service_display_name(response.service_name)
            model_name = response.model_name
            
            if response.success:
                status = "✅ 成功"
                preview = self._truncate_content(response.content, 50)
                confidence = f"{response.confidence:.1f}/10"
            else:
                status = "❌ 失败"
                preview = response.error_message or "未知错误"
                confidence = "0/10"
            
            response_time = f"{response.response_time:.2f}s"
            
            table_lines.append(
                f"| {service_name} | {model_name} | {status} | {preview} | {confidence} | {response_time} |"
            )
        
        return "\n".join(table_lines)
    
    def format_detailed_responses(self, responses: List[AIResponse]) -> str:
        """
        格式化详细响应内容
        
        Args:
            responses: AI响应列表
            
        Returns:
            str: 详细格式化的响应内容
        """
        if not responses:
            return "无AI响应数据"
        
        sections = []
        
        for i, response in enumerate(responses, 1):
            service_display = self._get_service_display_name(response.service_name)
            
            if response.success:
                section = f"""### {i}. {service_display} ({response.model_name})

**状态**: ✅ 调用成功
**置信度**: {response.confidence:.1f}/10
**响应时间**: {response.response_time:.2f}s
**Token使用**: {self._format_token_usage(response.token_usage)}

**分析内容**:
{self._format_content_with_blocks(response.content)}"""
            else:
                section = f"""### {i}. {service_display} ({response.model_name})

**状态**: ❌ 调用失败
**错误信息**: {response.error_message}
**响应时间**: {response.response_time:.2f}s"""
            
            sections.append(section)
        
        return "\n\n---\n\n".join(sections)
    
    def format_combined_analysis(self, responses: List[AIResponse]) -> str:
        """
        格式化综合分析结果
        
        Args:
            responses: AI响应列表
            
        Returns:
            str: 综合分析格式化输出
        """
        successful_responses = [r for r in responses if r.success]
        failed_responses = [r for r in responses if not r.success]
        
        if not successful_responses:
            return "## ⚠️ 分析失败\n\n所有AI服务调用均失败，无法提供分析结果。"
        
        # 统计信息
        total_services = len(responses)
        success_count = len(successful_responses)
        avg_confidence = sum(r.confidence for r in successful_responses) / len(successful_responses)
        avg_response_time = sum(r.response_time for r in successful_responses) / len(successful_responses)
        
        # 构建综合分析
        analysis_parts = []
        
        # 头部统计
        stats_section = f"""## 📊 分析统计

| 指标 | 值 |
|------|-----|
| 调用服务数 | {total_services} |
| 成功调用数 | {success_count} |
| 成功率 | {(success_count/total_services)*100:.1f}% |
| 平均置信度 | {avg_confidence:.1f}/10 |
| 平均响应时间 | {avg_response_time:.2f}s |

"""
        analysis_parts.append(stats_section)
        
        # 快速概览表格
        if self.style_config.get("settings", {}).get("output_format", {}).get("use_tables", True):
            table_section = "## 📋 分析概览\n\n" + self.format_analysis_table(responses) + "\n\n"
            analysis_parts.append(table_section)
        
        # 成功的分析结果
        if successful_responses:
            success_section = "## ✅ 成功分析结果\n\n"
            for response in successful_responses:
                service_name = self._get_service_display_name(response.service_name)
                success_section += f"**[{service_name}]**: {self._truncate_content(response.content, 200)}\n\n"
            analysis_parts.append(success_section)
        
        # 失败的调用信息
        if failed_responses:
            fail_section = "## ❌ 失败调用信息\n\n"
            for response in failed_responses:
                service_name = self._get_service_display_name(response.service_name)
                fail_section += f"**[{service_name}]**: {response.error_message}\n\n"
            analysis_parts.append(fail_section)
        
        # 综合建议
        if len(successful_responses) >= 2:
            recommendations = self._generate_recommendations(successful_responses)
            if recommendations:
                rec_section = f"## 🎯 综合建议\n\n{recommendations}\n\n"
                analysis_parts.append(rec_section)
        
        return "".join(analysis_parts)
    
    def format_for_claude_code(self, responses: List[AIResponse], format_type: str = "combined") -> FormattedOutput:
        """
        格式化为Claude Code适用的输出
        
        Args:
            responses: AI响应列表
            format_type: 格式类型 (table, detailed, combined)
            
        Returns:
            FormattedOutput: 格式化输出对象
        """
        if format_type == "table":
            content = self.format_analysis_table(responses)
        elif format_type == "detailed":
            content = self.format_detailed_responses(responses)
        else:  # combined
            content = self.format_combined_analysis(responses)
        
        metadata = {
            "total_responses": len(responses),
            "successful_responses": len([r for r in responses if r.success]),
            "format_type": format_type,
            "timestamp": self._get_timestamp()
        }
        
        return FormattedOutput(
            content=content,
            format_type=format_type,
            metadata=metadata
        )
    
    def _get_service_display_name(self, service_name: str) -> str:
        """获取服务显示名称"""
        name_mapping = {
            "zhipu": "智谱轻言",
            "silicon": "硅基流动",
            "openai": "OpenAI",
            "claude": "Claude"
        }
        return name_mapping.get(service_name, service_name.title())
    
    def _clean_content(self, content: str) -> str:
        """清理内容格式"""
        # 移除多余的空行
        content = re.sub(r'\n\s*\n', '\n\n', content.strip())
        # 处理表格字符转义
        content = content.replace('|', '\\|')
        return content
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """截断内容"""
        if len(content) <= max_length:
            return content.replace('\n', ' ')
        
        truncated = content[:max_length].replace('\n', ' ')
        return truncated + "..."
    
    def _format_content_with_blocks(self, content: str) -> str:
        """格式化内容，包含代码块处理"""
        # 检测是否包含代码
        if '```' in content or content.count('\n') > 10:
            return f"```\n{content}\n```"
        return content
    
    def _format_token_usage(self, token_usage: Dict[str, int]) -> str:
        """格式化token使用信息"""
        if not token_usage:
            return "未知"
        
        total = token_usage.get('total_tokens', 0)
        prompt = token_usage.get('prompt_tokens', 0)
        completion = token_usage.get('completion_tokens', 0)
        
        if total:
            return f"总计: {total}, 输入: {prompt}, 输出: {completion}"
        
        return "未记录"
    
    def _generate_recommendations(self, responses: List[AIResponse]) -> str:
        """生成综合建议"""
        if len(responses) < 2:
            return ""
        
        # 简单的建议生成逻辑
        high_confidence = [r for r in responses if r.confidence >= 8.0]
        medium_confidence = [r for r in responses if 6.0 <= r.confidence < 8.0]
        
        recommendations = []
        
        if high_confidence:
            rec = f"- 高置信度分析 ({len(high_confidence)}个): 建议优先采纳这些建议"
            recommendations.append(rec)
        
        if medium_confidence:
            rec = f"- 中等置信度分析 ({len(medium_confidence)}个): 可作为参考补充"
            recommendations.append(rec)
        
        if len(set(r.service_name for r in responses)) >= 2:
            recommendations.append("- 多服务验证: 建议结合多个AI意见做最终决策")
        
        fast_responses = [r for r in responses if r.response_time < 2.0]
        if fast_responses:
            recommendations.append(f"- 快速响应服务 ({len(fast_responses)}个): 适合后续快速迭代使用")
        
        return "\n".join(recommendations) if recommendations else ""
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class AIIntegrationAgent:
    """AI整合助手Agent - 结合多个AI服务进行协作分析"""
    
    def __init__(self, config_path: str = None, style_path: str = None):
        """
        初始化AI整合助手
        
        Args:
            config_path: AI服务配置文件路径
            style_path: 输出样式配置文件路径
        """
        from ai_service_manager import AIServiceManager
        
        self.service_manager = AIServiceManager(config_path)
        self.formatter = OutputFormatter(style_path)
        self.session_active = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.service_manager.__aenter__()
        self.session_active = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.service_manager.__aexit__(exc_type, exc_val, exc_tb)
        self.session_active = False
    
    async def analyze_code(self, code: str, language: str = "python") -> FormattedOutput:
        """
        代码分析
        
        Args:
            code: 要分析的代码
            language: 编程语言
            
        Returns:
            FormattedOutput: 格式化的分析结果
        """
        prompt = f"""请对以下{language}代码进行全面分析：

```{language}
{code}
```

请从以下角度进行分析：
1. 代码质量和规范性
2. 性能优化建议
3. 安全性检查
4. 可维护性评估
5. 潜在问题识别

请提供具体的改进建议和最佳实践推荐。"""
        
        responses = await self.service_manager.analyze_with_multiple_ai(prompt, template_type="code_review")
        return self.formatter.format_for_claude_code(responses, "combined")
    
    async def analyze_error(self, error_message: str, code: str = "", language: str = "python") -> FormattedOutput:
        """
        错误分析
        
        Args:
            error_message: 错误消息
            code: 相关代码
            language: 编程语言
            
        Returns:
            FormattedOutput: 格式化的分析结果
        """
        prompt = f"""请分析以下错误：

错误信息：
{error_message}

相关代码：
```{language}
{code}
```

请提供：
1. 错误根本原因分析
2. 具体解决方案
3. 预防措施建议
4. 相关最佳实践"""
        
        responses = await self.service_manager.analyze_with_multiple_ai(prompt, template_type="bug_analysis")
        return self.formatter.format_for_claude_code(responses, "combined")
    
    async def general_analysis(self, content: str, analysis_type: str = "general") -> FormattedOutput:
        """
        通用分析
        
        Args:
            content: 要分析的内容
            analysis_type: 分析类型
            
        Returns:
            FormattedOutput: 格式化的分析结果
        """
        responses = await self.service_manager.analyze_with_multiple_ai(content, template_type="analysis")
        return self.formatter.format_for_claude_code(responses, "combined")
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        available_services = self.service_manager.get_available_services()
        free_models = self.service_manager.get_free_models()
        
        return {
            "available_services": available_services,
            "free_models": free_models,
            "session_active": self.session_active,
            "total_services": len(self.service_manager.config['services']),
            "enabled_services": len(available_services)
        }


if __name__ == "__main__":
    # 测试示例
    import asyncio
    
    async def test_formatter():
        """测试输出格式化器"""
        # 创建模拟响应
        responses = [
            AIResponse(
                service_name="zhipu",
                model_name="glm-4-flash",
                content="这段代码整体结构清晰，但存在一些可以优化的地方...",
                confidence=8.5,
                token_usage={"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50},
                response_time=1.2,
                success=True
            ),
            AIResponse(
                service_name="silicon",
                model_name="deepseek-v2.5",
                content="代码质量良好，建议添加更多的错误处理...",
                confidence=7.8,
                token_usage={"total_tokens": 200, "prompt_tokens": 120, "completion_tokens": 80},
                response_time=2.1,
                success=True
            )
        ]
        
        formatter = OutputFormatter()
        result = formatter.format_for_claude_code(responses, "combined")
        print(result.content)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        import sys
        asyncio.run(test_formatter())
    else:
        print("Output Formatter - AI输出格式化Agent")
        print("使用 'python output_formatter.py test' 运行测试")
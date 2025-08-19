#!/usr/bin/env python3
"""
AI Service Manager - 多AI服务调用封装类
支持智谱轻言、硅基流动等多个AI服务的统一调用接口
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class AIResponse:
    """AI响应数据类"""
    service_name: str
    model_name: str
    content: str
    confidence: float
    token_usage: Dict[str, int]
    response_time: float
    success: bool
    error_message: Optional[str] = None


class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化AI服务管理器
        
        Args:
            config_path: 配置文件路径，默认为 .claude/ai-services-config.json
        """
        self.config_path = config_path or ".claude/ai-services-config.json"
        self.config = self._load_config()
        self.session = None
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件格式错误: {self.config_path}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def get_available_services(self) -> List[str]:
        """获取可用的AI服务列表"""
        return [service for service, config in self.config['services'].items() 
                if config.get('enabled', False) and config.get('api_key')]
    
    def get_service_models(self, service_name: str) -> List[str]:
        """获取指定服务的模型列表"""
        service_config = self.config['services'].get(service_name)
        if not service_config:
            return []
        return list(service_config.get('models', {}).keys())
    
    def get_free_models(self) -> Dict[str, List[str]]:
        """获取所有免费模型"""
        free_models = {}
        for service_name, service_config in self.config['services'].items():
            if not service_config.get('enabled', False):
                continue
            
            models = service_config.get('models', {})
            free_list = [model_name for model_name, model_config in models.items() 
                        if model_config.get('type') == 'free']
            
            if free_list:
                free_models[service_name] = free_list
        
        return free_models
    
    async def call_ai_service(self, 
                            service_name: str, 
                            model_name: str, 
                            prompt: str, 
                            temperature: float = None,
                            max_tokens: int = None) -> AIResponse:
        """
        调用指定的AI服务
        
        Args:
            service_name: 服务名称 (zhipu, silicon, openai)
            model_name: 模型名称
            prompt: 输入提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            AIResponse: AI响应对象
        """
        import time
        start_time = time.time()
        
        service_config = self.config['services'].get(service_name)
        if not service_config:
            return AIResponse(
                service_name=service_name,
                model_name=model_name,
                content="",
                confidence=0.0,
                token_usage={},
                response_time=0.0,
                success=False,
                error_message=f"未找到服务配置: {service_name}"
            )
        
        if not service_config.get('enabled', False):
            return AIResponse(
                service_name=service_name,
                model_name=model_name,
                content="",
                confidence=0.0,
                token_usage={},
                response_time=0.0,
                success=False,
                error_message=f"服务未启用: {service_name}"
            )
        
        api_key = service_config.get('api_key')
        if not api_key:
            return AIResponse(
                service_name=service_name,
                model_name=model_name,
                content="",
                confidence=0.0,
                token_usage={},
                response_time=0.0,
                success=False,
                error_message=f"API密钥未配置: {service_name}"
            )
        
        model_config = service_config.get('models', {}).get(model_name)
        if not model_config:
            return AIResponse(
                service_name=service_name,
                model_name=model_name,
                content="",
                confidence=0.0,
                token_usage={},
                response_time=0.0,
                success=False,
                error_message=f"未找到模型配置: {model_name}"
            )
        
        # 构建请求参数
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature or model_config.get('temperature', 0.7),
            "max_tokens": max_tokens or model_config.get('max_tokens', 4096)
        }
        
        # 构建请求头
        headers = {}
        for key, value in service_config.get('headers', {}).items():
            headers[key] = value.replace('{api_key}', api_key)
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.get('global_settings', {}).get('timeout', 30))
            
            async with self.session.post(
                service_config['api_base'],
                json=payload,
                headers=headers,
                timeout=timeout
            ) as response:
                response_time = time.time() - start_time
                
                if response.status != 200:
                    error_text = await response.text()
                    return AIResponse(
                        service_name=service_name,
                        model_name=model_name,
                        content="",
                        confidence=0.0,
                        token_usage={},
                        response_time=response_time,
                        success=False,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                
                result = await response.json()
                
                # 解析响应
                content = ""
                token_usage = {}
                
                if 'choices' in result and result['choices']:
                    content = result['choices'][0].get('message', {}).get('content', '')
                
                if 'usage' in result:
                    token_usage = result['usage']
                
                return AIResponse(
                    service_name=service_name,
                    model_name=model_name,
                    content=content,
                    confidence=8.5,  # 默认置信度
                    token_usage=token_usage,
                    response_time=response_time,
                    success=True
                )
                
        except asyncio.TimeoutError:
            return AIResponse(
                service_name=service_name,
                model_name=model_name,
                content="",
                confidence=0.0,
                token_usage={},
                response_time=time.time() - start_time,
                success=False,
                error_message="请求超时"
            )
        except Exception as e:
            return AIResponse(
                service_name=service_name,
                model_name=model_name,
                content="",
                confidence=0.0,
                token_usage={},
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    async def analyze_with_multiple_ai(self, 
                                     prompt: str, 
                                     services: List[str] = None, 
                                     template_type: str = "analysis") -> List[AIResponse]:
        """
        使用多个AI服务进行分析
        
        Args:
            prompt: 分析内容
            services: 要使用的服务列表，默认使用所有可用服务
            template_type: 模板类型 (analysis, code_review, bug_analysis)
            
        Returns:
            List[AIResponse]: AI响应列表
        """
        if services is None:
            services = self.get_available_services()
        
        # 获取对应的提示词模板
        template_key = f"{template_type}_template"
        template = self.config.get('prompts', {}).get(template_key, "{content}")
        formatted_prompt = template.format(content=prompt, language="", code="", error="")
        
        tasks = []
        for service_name in services:
            # 获取该服务的默认模型
            models = self.get_service_models(service_name)
            if not models:
                continue
                
            # 优先使用免费模型
            free_models = [m for m in models 
                         if self.config['services'][service_name]['models'][m].get('type') == 'free']
            model_name = free_models[0] if free_models else models[0]
            
            task = self.call_ai_service(service_name, model_name, formatted_prompt)
            tasks.append(task)
        
        if not tasks:
            return []
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                continue
            valid_results.append(result)
        
        return valid_results
    
    def format_ai_responses(self, responses: List[AIResponse]) -> str:
        """格式化AI响应为表格形式"""
        if not responses:
            return "没有获得AI分析结果"
        
        # 构建表格
        table_rows = ["| AI服务 | 模型 | 分析结果 | 置信度 | 响应时间 |"]
        table_rows.append("|--------|------|----------|--------|----------|")
        
        for response in responses:
            if response.success:
                # 截断内容以适应表格显示
                content = response.content[:100] + "..." if len(response.content) > 100 else response.content
                content = content.replace('\n', ' ').replace('|', '\\|')  # 转义表格字符
                
                table_rows.append(
                    f"| {response.service_name} | {response.model_name} | {content} | "
                    f"{response.confidence:.1f}/10 | {response.response_time:.2f}s |"
                )
            else:
                table_rows.append(
                    f"| {response.service_name} | {response.model_name} | "
                    f"错误: {response.error_message} | 0/10 | {response.response_time:.2f}s |"
                )
        
        return "\n".join(table_rows)
    
    def get_combined_analysis(self, responses: List[AIResponse]) -> str:
        """获取综合分析结果"""
        successful_responses = [r for r in responses if r.success]
        
        if not successful_responses:
            return "所有AI服务调用失败，无法提供分析结果"
        
        # 简单的综合分析逻辑
        combined_content = "\n\n".join([
            f"**{r.service_name} ({r.model_name})**:\n{r.content}" 
            for r in successful_responses
        ])
        
        avg_confidence = sum(r.confidence for r in successful_responses) / len(successful_responses)
        
        summary = f"""## 综合分析 (基于{len(successful_responses)}个AI服务)

{combined_content}

---
**平均置信度**: {avg_confidence:.1f}/10
**参与分析的AI服务**: {', '.join([r.service_name for r in successful_responses])}
"""
        
        return summary


# 配置管理工具函数
def setup_ai_service(service_name: str, api_key: str, models: List[str] = None):
    """配置AI服务"""
    config_path = ".claude/ai-services-config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"配置文件不存在: {config_path}")
        return False
    
    if service_name not in config['services']:
        print(f"不支持的服务: {service_name}")
        print(f"支持的服务: {list(config['services'].keys())}")
        return False
    
    # 更新配置
    config['services'][service_name]['api_key'] = api_key
    config['services'][service_name]['enabled'] = True
    
    # 如果指定了模型，则只启用这些模型
    if models:
        available_models = list(config['services'][service_name]['models'].keys())
        for model in models:
            if model not in available_models:
                print(f"警告: 模型 {model} 不在可用列表中: {available_models}")
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"成功配置 {service_name} 服务")
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


def list_ai_services():
    """列出所有AI服务状态"""
    config_path = ".claude/ai-services-config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"配置文件不存在: {config_path}")
        return
    
    print("AI服务配置状态:")
    print("-" * 50)
    
    for service_name, service_config in config['services'].items():
        status = "✅ 已启用" if service_config.get('enabled') and service_config.get('api_key') else "❌ 未配置"
        model_count = len(service_config.get('models', {}))
        free_count = len([m for m in service_config.get('models', {}).values() if m.get('type') == 'free'])
        
        print(f"服务: {service_config['name']} ({service_name})")
        print(f"状态: {status}")
        print(f"模型数量: {model_count} (免费: {free_count})")
        print(f"API地址: {service_config['api_base']}")
        print("-" * 50)


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup" and len(sys.argv) >= 4:
            service_name = sys.argv[2]
            api_key = sys.argv[3]
            setup_ai_service(service_name, api_key)
        elif sys.argv[1] == "list":
            list_ai_services()
        else:
            print("用法:")
            print("  python ai_service_manager.py setup <service_name> <api_key>")
            print("  python ai_service_manager.py list")
    else:
        print("AI Service Manager - 多AI服务调用封装类")
        print("支持的命令:")
        print("  setup <service_name> <api_key> - 配置AI服务")
        print("  list - 列出服务状态")
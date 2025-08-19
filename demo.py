#!/usr/bin/env python3
"""
AI整合助手演示脚本
展示如何在代码中直接使用AI整合助手功能
"""

import asyncio
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ai_service_manager import AIServiceManager
from src.output_formatter import AIIntegrationAgent, OutputFormatter


async def demo_basic_usage():
    """基本使用演示"""
    print("🚀 AI整合助手基本使用演示")
    print("=" * 50)
    
    # 检查配置文件是否存在
    config_path = ".claude/ai-services-config.json"
    if not os.path.exists(config_path):
        print("❌ 配置文件不存在，请先运行:")
        print("   python ai_assistant_cli.py init")
        print("   python ai_assistant_cli.py config zhipu <your-api-key>")
        return
    
    try:
        # 创建AI整合助手实例
        async with AIIntegrationAgent() as agent:
            
            # 获取服务状态
            status = agent.get_service_status()
            print(f"📊 服务状态:")
            print(f"   可用服务: {len(status['available_services'])}/{status['total_services']}")
            print(f"   服务列表: {', '.join(status['available_services'])}")
            
            if not status['available_services']:
                print("❌ 没有可用的AI服务，请先配置")
                print("   python ai_assistant_cli.py config zhipu <your-api-key>")
                return
            
            print(f"   免费模型: {status['free_models']}")
            print()
            
            # 演示1: 通用文本分析
            print("📝 演示1: 通用文本分析")
            print("-" * 30)
            
            sample_text = """
            Python是一种高级编程语言，以其简洁易读的语法而闻名。
            它广泛应用于Web开发、数据科学、人工智能等领域。
            Python的哲学是"优雅"、"明确"、"简单"。
            """
            
            print(f"分析内容: {sample_text.strip()}")
            print("\n🔍 开始分析...")
            
            result = await agent.general_analysis(sample_text)
            print(result.content)
            print("\n" + "=" * 50 + "\n")
            
            # 演示2: 代码分析
            print("🔧 演示2: 代码分析")
            print("-" * 30)
            
            sample_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(result)
            '''
            
            print("分析代码:")
            print(sample_code)
            print("🔍 开始代码分析...")
            
            result = await agent.analyze_code(sample_code, "python")
            print(result.content)
            print("\n" + "=" * 50 + "\n")
            
            # 演示3: 错误分析
            print("🐛 演示3: 错误分析")
            print("-" * 30)
            
            error_msg = "IndexError: list index out of range"
            error_code = '''
data = [1, 2, 3]
for i in range(5):
    print(data[i])  # 这里会出错
            '''
            
            print(f"错误信息: {error_msg}")
            print("相关代码:")
            print(error_code)
            print("🔍 开始错误分析...")
            
            result = await agent.analyze_error(error_msg, error_code, "python")
            print(result.content)
            
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


async def demo_output_formats():
    """输出格式演示"""
    print("\n🎨 输出格式演示")
    print("=" * 50)
    
    # 创建模拟响应数据
    from src.ai_service_manager import AIResponse
    
    mock_responses = [
        AIResponse(
            service_name="zhipu",
            model_name="glm-4-flash", 
            content="这是智谱轻言的分析结果。代码整体结构良好，但建议添加错误处理机制以提高健壮性。",
            confidence=8.5,
            token_usage={"total_tokens": 120, "prompt_tokens": 80, "completion_tokens": 40},
            response_time=1.2,
            success=True
        ),
        AIResponse(
            service_name="silicon",
            model_name="deepseek-v2.5",
            content="从性能角度分析，当前实现可以进一步优化。建议使用缓存机制减少重复计算。",
            confidence=7.8,
            token_usage={"total_tokens": 150, "prompt_tokens": 90, "completion_tokens": 60},
            response_time=2.1,
            success=True
        ),
        AIResponse(
            service_name="openai",
            model_name="gpt-3.5-turbo",
            content="",
            confidence=0.0,
            token_usage={},
            response_time=0.5,
            success=False,
            error_message="API密钥未配置"
        )
    ]
    
    formatter = OutputFormatter()
    
    # 演示不同的输出格式
    print("📋 表格格式:")
    table_result = formatter.format_for_claude_code(mock_responses, "table")
    print(table_result.content)
    print()
    
    print("📖 详细格式:")
    detailed_result = formatter.format_for_claude_code(mock_responses, "detailed") 
    print(detailed_result.content)
    print()
    
    print("🔄 综合格式:")
    combined_result = formatter.format_for_claude_code(mock_responses, "combined")
    print(combined_result.content)


async def demo_service_manager():
    """AI服务管理器演示"""
    print("\n🤖 AI服务管理器演示")  
    print("=" * 50)
    
    try:
        async with AIServiceManager() as manager:
            
            # 获取服务信息
            available = manager.get_available_services()
            all_models = {}
            free_models = manager.get_free_models()
            
            print(f"📡 可用服务: {available}")
            print(f"🆓 免费模型: {free_models}")
            
            for service in available:
                models = manager.get_service_models(service)
                all_models[service] = models
                print(f"   {service}: {models}")
            
            if not available:
                print("❌ 没有可用服务，演示结束")
                return
            
            # 测试单个服务调用
            print(f"\n🧪 测试服务调用:")
            service_name = available[0]
            model_name = all_models[service_name][0]
            
            print(f"   调用 {service_name} ({model_name})...")
            
            response = await manager.call_ai_service(
                service_name, 
                model_name, 
                "请简单介绍一下人工智能的发展历程"
            )
            
            if response.success:
                print(f"   ✅ 调用成功")
                print(f"   📝 响应内容: {response.content[:100]}...")
                print(f"   ⏱️  响应时间: {response.response_time:.2f}s")
                print(f"   🎯 置信度: {response.confidence}/10")
            else:
                print(f"   ❌ 调用失败: {response.error_message}")
            
    except Exception as e:
        print(f"❌ 服务管理器演示失败: {e}")


def main():
    """主函数"""
    print("🎪 AI整合助手完整演示")
    print("适用于Claude Code环境的多AI服务整合工具")
    print("=" * 60)
    
    try:
        # 运行所有演示
        asyncio.run(demo_basic_usage())
        asyncio.run(demo_output_formats())
        asyncio.run(demo_service_manager())
        
        print("\n🎉 演示完成！")
        print("\n📚 更多用法:")
        print("   python ai_assistant_cli.py --help")
        print("   python ai_assistant_cli.py list")
        print("   python ai_assistant_cli.py analyze '你的内容'")
        
    except KeyboardInterrupt:
        print("\n⚠️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
AI整合助手 - 命令行接口
支持多AI服务配置和调用的统一管理工具
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ai_service_manager import AIServiceManager, setup_ai_service, list_ai_services
from src.output_formatter import AIIntegrationAgent, OutputFormatter


class AIAssistantCLI:
    """AI整合助手CLI管理器"""
    
    def __init__(self):
        self.config_dir = Path(".claude")
        self.services_config = self.config_dir / "ai-services-config.json"
        self.style_config = self.config_dir / "output-styles" / "AI整合助手.json"
    
    def ensure_config_exists(self):
        """确保配置文件存在"""
        if not self.services_config.exists():
            print("❌ AI服务配置文件不存在，请先运行初始化命令")
            print("   python ai_assistant_cli.py init")
            sys.exit(1)
    
    def cmd_init(self, args):
        """初始化配置"""
        self.config_dir.mkdir(exist_ok=True)
        (self.config_dir / "output-styles").mkdir(exist_ok=True)
        
        if self.services_config.exists() and not args.force:
            print("⚠️  配置文件已存在，使用 --force 强制重新初始化")
            return
        
        # 检查是否已有配置文件（避免覆盖）
        if self.services_config.exists():
            print("🔄 强制重新初始化配置文件...")
        else:
            print("🚀 初始化AI整合助手配置...")
        
        print("✅ 配置文件已创建")
        print(f"   - AI服务配置: {self.services_config}")
        print(f"   - 输出样式配置: {self.style_config}")
        print("\n📝 下一步操作:")
        print("   1. 配置AI服务: python ai_assistant_cli.py config <service> <api_key>")
        print("   2. 查看服务状态: python ai_assistant_cli.py list")
        print("   3. 开始使用: python ai_assistant_cli.py analyze <content>")
    
    def cmd_config(self, args):
        """配置AI服务"""
        self.ensure_config_exists()
        
        service_name = args.service
        api_key = args.api_key
        
        success = setup_ai_service(service_name, api_key)
        if success:
            print(f"✅ 成功配置 {service_name} 服务")
            print(f"🔑 API密钥: {api_key[:10]}...")
            
            # 显示可用模型
            try:
                with open(self.services_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                models = list(config['services'][service_name]['models'].keys())
                free_models = [
                    m for m, info in config['services'][service_name]['models'].items() 
                    if info.get('type') == 'free'
                ]
                
                print(f"📋 可用模型 ({len(models)}个):")
                for model in models:
                    model_info = config['services'][service_name]['models'][model]
                    model_type = "🆓 免费" if model_info.get('type') == 'free' else "💰 付费"
                    print(f"   - {model} ({model_type})")
                
            except Exception as e:
                print(f"⚠️  获取模型信息失败: {e}")
        else:
            print(f"❌ 配置 {service_name} 服务失败")
    
    def cmd_list(self, args):
        """列出AI服务状态"""
        self.ensure_config_exists()
        
        print("🤖 AI整合助手 - 服务状态")
        print("=" * 50)
        
        try:
            with open(self.services_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            enabled_count = 0
            total_count = len(config['services'])
            
            for service_name, service_config in config['services'].items():
                has_key = bool(service_config.get('api_key'))
                is_enabled = service_config.get('enabled', False)
                
                if has_key and is_enabled:
                    status = "✅ 已启用"
                    enabled_count += 1
                elif has_key:
                    status = "⚠️  已配置但未启用"
                else:
                    status = "❌ 未配置"
                
                print(f"\n📡 {service_config['name']} ({service_name})")
                print(f"   状态: {status}")
                print(f"   API地址: {service_config['api_base']}")
                
                # 显示模型信息
                models = service_config.get('models', {})
                free_count = len([m for m in models.values() if m.get('type') == 'free'])
                paid_count = len(models) - free_count
                print(f"   模型: {len(models)}个 (免费: {free_count}, 付费: {paid_count})")
                
                if has_key and args.verbose:
                    key_preview = service_config['api_key'][:10] + "..." if service_config['api_key'] else "无"
                    print(f"   API密钥: {key_preview}")
            
            print("\n" + "=" * 50)
            print(f"📊 总计: {enabled_count}/{total_count} 个服务已启用")
            
            if enabled_count == 0:
                print("\n💡 提示: 使用以下命令配置AI服务:")
                print("   python ai_assistant_cli.py config zhipu <your_api_key>")
                print("   python ai_assistant_cli.py config silicon <your_api_key>")
            
        except Exception as e:
            print(f"❌ 读取配置失败: {e}")
    
    async def cmd_analyze(self, args):
        """分析内容"""
        self.ensure_config_exists()
        
        content = args.content
        if not content:
            # 从标准输入读取
            if not sys.stdin.isatty():
                content = sys.stdin.read().strip()
            else:
                print("❌ 请提供要分析的内容")
                return
        
        if not content:
            print("❌ 没有要分析的内容")
            return
        
        print("🔍 开始AI分析...")
        print(f"📝 内容长度: {len(content)} 字符")
        
        try:
            async with AIIntegrationAgent() as agent:
                # 检查可用服务
                status = agent.get_service_status()
                available = status['available_services']
                
                if not available:
                    print("❌ 没有可用的AI服务，请先配置")
                    print("   使用: python ai_assistant_cli.py config <service> <api_key>")
                    return
                
                print(f"🚀 使用 {len(available)} 个AI服务进行分析: {', '.join(available)}")
                
                # 执行分析
                result = await agent.general_analysis(content)
                
                print("\n" + "=" * 60)
                print(result.content)
                print("=" * 60)
                
                # 保存分析结果
                if args.save:
                    output_file = args.save
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.content)
                    print(f"\n💾 分析结果已保存到: {output_file}")
                
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    async def cmd_code_review(self, args):
        """代码审查"""
        self.ensure_config_exists()
        
        code_file = args.file
        language = args.language or self._detect_language(code_file)
        
        try:
            with open(code_file, 'r', encoding='utf-8') as f:
                code = f.read()
        except FileNotFoundError:
            print(f"❌ 文件未找到: {code_file}")
            return
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
        
        print(f"🔍 开始代码审查: {code_file}")
        print(f"📝 语言: {language}, 行数: {code.count(chr(10)) + 1}")
        
        try:
            async with AIIntegrationAgent() as agent:
                result = await agent.analyze_code(code, language)
                
                print("\n" + "=" * 60)
                print(result.content)
                print("=" * 60)
                
                if args.save:
                    output_file = args.save
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.content)
                    print(f"\n💾 审查结果已保存到: {output_file}")
                
        except Exception as e:
            print(f"❌ 代码审查失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    async def cmd_error_analysis(self, args):
        """错误分析"""
        self.ensure_config_exists()
        
        error_message = args.error
        code_file = args.code_file
        language = args.language
        
        code = ""
        if code_file:
            try:
                with open(code_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                language = language or self._detect_language(code_file)
            except Exception as e:
                print(f"⚠️  读取代码文件失败: {e}")
        
        print("🐛 开始错误分析...")
        print(f"❌ 错误信息: {error_message[:100]}...")
        if code:
            print(f"📝 相关代码: {len(code)} 字符")
        
        try:
            async with AIIntegrationAgent() as agent:
                result = await agent.analyze_error(error_message, code, language or "text")
                
                print("\n" + "=" * 60)
                print(result.content)
                print("=" * 60)
                
                if args.save:
                    output_file = args.save
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result.content)
                    print(f"\n💾 错误分析结果已保存到: {output_file}")
                
        except Exception as e:
            print(f"❌ 错误分析失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    def cmd_test(self, args):
        """测试配置"""
        self.ensure_config_exists()
        
        print("🧪 测试AI服务连接...")
        
        async def run_test():
            try:
                async with AIServiceManager() as manager:
                    available_services = manager.get_available_services()
                    
                    if not available_services:
                        print("❌ 没有可用的AI服务")
                        return
                    
                    print(f"📡 测试 {len(available_services)} 个服务...")
                    
                    test_prompt = "Hello, please respond with 'Connection successful' in Chinese."
                    
                    for service_name in available_services:
                        models = manager.get_service_models(service_name)
                        if models:
                            model_name = models[0]  # 使用第一个模型测试
                            
                            print(f"   测试 {service_name} ({model_name})...", end="")
                            
                            response = await manager.call_ai_service(
                                service_name, model_name, test_prompt
                            )
                            
                            if response.success:
                                print(f" ✅ 成功 ({response.response_time:.2f}s)")
                                if args.verbose:
                                    print(f"      响应: {response.content[:50]}...")
                            else:
                                print(f" ❌ 失败: {response.error_message}")
                        else:
                            print(f"   {service_name}: ❌ 没有可用模型")
            
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
        
        asyncio.run(run_test())
    
    def _detect_language(self, filename: str) -> str:
        """检测文件语言"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sh': 'bash',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown'
        }
        
        ext = Path(filename).suffix.lower()
        return ext_map.get(ext, 'text')


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="AI整合助手 - 多AI服务协作分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 初始化配置
  python ai_assistant_cli.py init
  
  # 配置AI服务
  python ai_assistant_cli.py config zhipu sk-xxx
  python ai_assistant_cli.py config silicon sk-xxx
  
  # 查看服务状态
  python ai_assistant_cli.py list
  
  # 分析内容
  python ai_assistant_cli.py analyze "请分析这段文本的情感倾向"
  
  # 代码审查
  python ai_assistant_cli.py code-review src/main.py
  
  # 错误分析
  python ai_assistant_cli.py error "IndexError: list index out of range"
  
  # 测试服务连接
  python ai_assistant_cli.py test
        """
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化配置')
    init_parser.add_argument('--force', action='store_true', help='强制重新初始化')
    
    # config 命令
    config_parser = subparsers.add_parser('config', help='配置AI服务')
    config_parser.add_argument('service', choices=['zhipu', 'silicon', 'openai'], help='服务名称')
    config_parser.add_argument('api_key', help='API密钥')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出AI服务状态')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析内容')
    analyze_parser.add_argument('content', nargs='?', help='要分析的内容')
    analyze_parser.add_argument('-s', '--save', help='保存结果到文件')
    analyze_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细错误')
    
    # code-review 命令
    review_parser = subparsers.add_parser('code-review', help='代码审查')
    review_parser.add_argument('file', help='要审查的代码文件')
    review_parser.add_argument('-l', '--language', help='指定编程语言')
    review_parser.add_argument('-s', '--save', help='保存结果到文件')
    review_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细错误')
    
    # error 命令
    error_parser = subparsers.add_parser('error', help='错误分析')
    error_parser.add_argument('error', help='错误信息')
    error_parser.add_argument('-c', '--code-file', help='相关代码文件')
    error_parser.add_argument('-l', '--language', help='指定编程语言')
    error_parser.add_argument('-s', '--save', help='保存结果到文件')
    error_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细错误')
    
    # test 命令
    test_parser = subparsers.add_parser('test', help='测试AI服务连接')
    test_parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = AIAssistantCLI()
    
    try:
        if args.command == 'init':
            cli.cmd_init(args)
        elif args.command == 'config':
            cli.cmd_config(args)
        elif args.command == 'list':
            cli.cmd_list(args)
        elif args.command == 'analyze':
            await cli.cmd_analyze(args)
        elif args.command == 'code-review':
            await cli.cmd_code_review(args)
        elif args.command == 'error':
            await cli.cmd_error_analysis(args)
        elif args.command == 'test':
            cli.cmd_test(args)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # 检查依赖
    try:
        import aiohttp
    except ImportError:
        print("❌ 缺少依赖: pip install aiohttp")
        sys.exit(1)
    
    asyncio.run(main())
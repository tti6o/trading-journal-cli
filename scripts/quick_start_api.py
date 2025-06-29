#!/usr/bin/env python3
"""
币安 API 集成快速入门脚本

这个脚本会引导您完成以下步骤：
1. 检查依赖包安装
2. 创建配置文件
3. 测试 API 连接
4. 同步交易数据
5. 生成分析报告
"""

import sys
import os
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import journal_core
import database_setup


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)


def print_step(step_num: int, description: str):
    """打印步骤"""
    print(f"\n📍 步骤 {step_num}: {description}")
    print("-" * 40)


def check_dependencies():
    """检查依赖包"""
    print_step(1, "检查依赖包安装")
    
    required_packages = ['ccxt', 'pandas', 'openpyxl', 'click', 'configparser']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - 已安装")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("正在安装缺少的依赖包...")
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✅ 依赖包安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖包安装失败，请手动运行: pip install -r requirements.txt")
            return False
    
    return True


def setup_database():
    """设置数据库"""
    print_step(2, "设置数据库")
    
    if database_setup.database_exists():
        print("✅ 数据库已存在")
        return True
    else:
        print("🔧 正在初始化数据库...")
        try:
            success = journal_core.initialize_database()
            if success:
                print("✅ 数据库初始化成功")
                return True
            else:
                print("❌ 数据库初始化失败")
                return False
        except Exception as e:
            print(f"❌ 数据库初始化异常: {e}")
            return False


def setup_config():
    """设置 API 配置"""
    print_step(3, "设置 API 配置")
    
    config_file = 'config.ini'
    
    if os.path.exists(config_file):
        print(f"✅ 配置文件 {config_file} 已存在")
        
        # 验证配置文件内容
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(config_file)
            
            api_key = config.get('binance', 'api_key', fallback='')
            api_secret = config.get('binance', 'api_secret', fallback='')
            
            if api_key and api_secret and not api_key.startswith('您的'):
                print("✅ API 密钥配置看起来正常")
                return True
            else:
                print("⚠️  API 密钥需要更新")
        except Exception as e:
            print(f"⚠️  配置文件格式有问题: {e}")
    
    print("\n🔧 创建 API 配置文件...")
    
    # 创建示例配置文件
    try:
        # 使用新架构创建配置
        config_content = """[binance]
api_key = "YOUR_BINANCE_API_KEY_HERE"
api_secret = "YOUR_BINANCE_API_SECRET_HERE"

[exchange]
name = "binance"
sandbox = false
rate_limit = true
"""
        
        with open('config.ini', 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        print("✅ 配置文件模板已创建: config.ini")
        print("✅ 配置模板创建成功")
    except Exception as e:
        print(f"❌ 创建配置模板失败: {e}")
        return False
    
    print("\n📝 请按照以下步骤配置 API 密钥:")
    print("1. 登录币安官网 (https://www.binance.com)")
    print("2. 进入 API 管理页面")
    print("3. 创建新的 API Key (只给予读取权限)")
    print("4. 复制 API Key 和 Secret")
    print("5. 编辑 config.ini.sample 文件，填入您的密钥")
    print("6. 将文件重命名为 config.ini")
    
    input("\n按回车键继续 (请确保您已完成上述配置)...")
    
    # 再次检查配置
    if os.path.exists(config_file):
        print("✅ 发现配置文件，继续下一步")
        return True
    else:
        print("❌ 配置文件不存在，请手动创建 config.ini")
        return False


def test_api_connection():
    """测试 API 连接"""
    print_step(4, "测试 API 连接")
    
    try:
        result = journal_core.test_binance_api_connection()
        
        if result['success']:
            print("✅ API 连接成功!")
            print(f"📊 账户资产数量: {result['assets_count']}")
            
            if result['assets_count'] > 0:
                print("\n💰 账户资产情况:")
                for currency, balance in result['account_info']['assets'].items():
                    if balance['total'] > 0.01:
                        print(f"   {currency}: {balance['total']:.6f}")
            
            return True
        else:
            print(f"❌ API 连接失败: {result['error']}")
            print("\n🔍 可能的原因:")
            print("- API 密钥不正确")
            print("- 网络连接问题")
            print("- API 权限设置问题")
            return False
            
    except Exception as e:
        print(f"❌ API 连接测试异常: {e}")
        return False


def sync_data():
    """同步数据"""
    print_step(5, "同步交易数据")
    
    print("🔄 开始同步最近 7 天的交易记录...")
    
    try:
        result = journal_core.sync_binance_trades(days=7)
        
        if result['success']:
            print("✅ 数据同步成功!")
            print(f"📅 同步时间范围: {result['sync_period']}")
            print(f"📊 新增交易记录: {result['new_count']} 条")
            print(f"⏭️  跳过重复记录: {result['duplicate_count']} 条")
            print(f"📈 数据库总记录数: {result['total_count']} 条")
            
            return result['new_count'] > 0 or result['duplicate_count'] > 0
        else:
            print(f"❌ 数据同步失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 数据同步异常: {e}")
        return False


def generate_report():
    """生成分析报告"""
    print_step(6, "生成分析报告")
    
    try:
        # 获取汇总统计
        stats = journal_core.generate_summary_report()
        
        if stats['total_trades'] > 0:
            print("✅ 报告生成成功!")
            print(f"📊 总交易数量: {stats['total_trades']} 笔")
            print(f"💰 总净盈亏: {stats['total_pnl']:.2f} USDT")
            print(f"📈 胜率: {stats['win_rate']:.1f}%")
            print(f"📊 盈亏比: {stats['profit_loss_ratio']:.2f}")
            print(f"📅 数据时间范围: {stats['time_range']}")
            
            return True
        else:
            print("⚠️  没有交易数据可生成报告")
            return False
            
    except Exception as e:
        print(f"❌ 生成报告异常: {e}")
        return False


def show_next_steps():
    """显示后续步骤"""
    print_section("🎯 后续使用建议")
    
    print("现在您可以使用以下命令:")
    print()
    print("📊 查看详细报告:")
    print("   python main.py report summary")
    print()
    print("📋 查看交易记录:")
    print("   python main.py report list-trades --limit 20")
    print()
    print("🔄 定期同步数据:")
    print("   python main.py api sync --days 7")
    print()
    print("🔍 查看特定币种:")
    print("   python main.py currency BTC --details")
    print()
    print("📈 查看所有币种:")
    print("   python main.py list-currencies")
    print()
    print("🛠️ 查看所有命令:")
    print("   python main.py --help")
    print("   python main.py api --help")


def main():
    """主函数"""
    print_section("币安 API 集成快速入门")
    
    print("欢迎使用币安 API 集成功能！")
    print("这个脚本将引导您完成初始设置和数据同步。")
    
    # 执行设置步骤
    steps = [
        ("检查依赖包", check_dependencies),
        ("设置数据库", setup_database),
        ("配置 API 密钥", setup_config),
        ("测试 API 连接", test_api_connection),
        ("同步交易数据", sync_data),
        ("生成分析报告", generate_report),
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step_name, step_func in steps:
        try:
            success = step_func()
            if success:
                success_count += 1
                print(f"✅ {step_name} - 完成")
            else:
                print(f"❌ {step_name} - 失败")
                
                # 如果是关键步骤失败，询问是否继续
                if step_name in ["配置 API 密钥", "测试 API 连接"]:
                    continue_setup = input(f"\n是否继续后续步骤？(y/n): ").lower().strip()
                    if continue_setup != 'y':
                        break
        except Exception as e:
            print(f"❌ {step_name} - 异常: {e}")
    
    # 显示设置结果
    print_section("设置结果")
    
    print(f"📈 完成进度: {success_count}/{total_steps} ({success_count/total_steps*100:.1f}%)")
    
    if success_count == total_steps:
        print("🎉 恭喜！所有设置都成功完成！")
        print("您现在可以使用 API 自动同步功能了。")
        show_next_steps()
    elif success_count >= 4:  # 至少完成前4步
        print("✅ 基本设置完成，可以开始使用部分功能。")
        show_next_steps()
    else:
        print("⚠️  设置不完整，请检查配置和网络连接。")
        print("\n🔍 建议:")
        print("1. 检查网络连接")
        print("2. 验证 API 密钥配置")
        print("3. 查看错误信息并尝试手动配置")
        print("4. 运行测试脚本: python scripts/test_api_integration.py")
    
    return success_count >= 4


if __name__ == "__main__":
    try:
        success = main()
        print(f"\n👋 感谢使用！")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n⏹️  用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1) 
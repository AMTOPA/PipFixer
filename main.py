import os
import json
import subprocess
import sys
import re
from zhipuai import ZhipuAI
from typing import Tuple, Optional, Dict

CONFIG_FILE = "config.json"
MIRROR_SOURCES = {
    "1": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "2": "https://mirrors.aliyun.com/pypi/simple",
    "3": "https://pypi.mirrors.ustc.edu.cn/simple",
    "4": "https://mirrors.cloud.tencent.com/pypi/simple",
    "5": "https://pypi.doubanio.com/simple",
    "0": "https://pypi.org/simple"  # 官方源
}

def load_config() -> dict:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config: dict) -> None:
    """保存配置文件"""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def setup_mirror(config: dict) -> None:
    """使用pip命令设置镜像源"""
    print("\n请选择PyPI镜像源(输入数字):")
    for num, url in MIRROR_SOURCES.items():
        print(f"{num}. {url}")
    
    choice = input(f"选择镜像源(1-5, 0为官方源, 默认为1): ").strip() or "1"
    mirror_url = MIRROR_SOURCES.get(choice, MIRROR_SOURCES["1"])
    
    # 使用pip命令设置镜像源
    cmd = f"pip config set global.index-url {mirror_url}"
    try:
        subprocess.run(cmd, shell=True, check=True)
        config["mirror_source"] = mirror_url
        save_config(config)
        print(f"\n已成功设置镜像源: {mirror_url}")
        print("当前pip配置:")
        subprocess.run("pip config list", shell=True)
    except subprocess.CalledProcessError as e:
        print(f"\n设置镜像源失败: {e}")

def initialize_config() -> dict:
    """初始化配置"""
    config = load_config()
    
    if "api_key" not in config:
        api_key = input("请输入智谱清言的API秘钥: ").strip()
        config["api_key"] = api_key
    
    if "package_manager" not in config:
        print("\n请选择默认包管理器:")
        print("1. pip")
        print("2. conda")
        choice = input("输入选择 (1/2, 默认为1): ").strip() or "1"
        config["package_manager"] = "pip" if choice == "1" else "conda"
    
    if "mirror_source" not in config:
        print("\n是否要配置PyPI镜像源? (国内用户推荐使用)")
        choice = input("是否配置? [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            setup_mirror(config)
        else:
            config["mirror_source"] = "未配置(使用默认源)"
            save_config(config)
    
    return config

def is_valid_command(cmd: str) -> bool:
    """检查是否已经是有效命令"""
    patterns = [
        r"^pip\s+(install|uninstall|show|list|search|download|config)\s",
        r"^pip\s+--version$",
        r"^pip\s+list$",
        r"^conda\s+",
        r"^python\s+-m\s+pip\s+"
    ]
    return any(re.match(p, cmd, re.IGNORECASE) for p in patterns)

def extract_command_from_response(response: str) -> Tuple[str, str]:
    """从AI响应中提取命令和包名"""
    # 尝试提取类似pip的命令格式
    patterns = [
        r"(pip|conda)\s+(install|uninstall|show|list|search|download)\s+([^\s]+)",
        r"正确的命令是:\s*(.*)",
        r"应该使用:\s*(.*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            command = match.group(0)
            package = match.groups()[-1] if len(match.groups()) > 2 else ""
            return command, package
    
    # 默认返回原始输入
    parts = response.split()
    package = parts[-1] if len(parts) > 0 else ""
    return response, package

def get_ai_correction(client: ZhipuAI, user_input: str, package_manager: str) -> Tuple[str, str]:
    """调用AI进行命令修正"""
    # 如果已经是有效命令，直接返回
    if is_valid_command(user_input):
        parts = user_input.split()
        package = parts[-1] if len(parts) > 2 else ""
        return user_input, package
    
    # 特殊处理版本查询
    version_patterns = [r"-v(ersion)?$", r"version$", r"--version$"]
    for pattern in version_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            pkg = re.sub(pattern, "", user_input, flags=re.IGNORECASE).strip()
            return f"{package_manager} show {pkg}", pkg
    
    prompt = f"""
    请根据用户输入识别并修正为正确的{package_manager}命令，支持以下操作：
    - 安装包: install/instal/instll → install
    - 卸载包: uninstall/uninstal/remove → uninstall
    - 查看信息: show/version/info → show
    - 其他合法{package_manager}命令
    
    修正常见包名错误，如：
    - pytorch → torch
    - opencv → opencv-python
    
    只需返回修正后的完整命令，不要解释。
    
    示例：
    输入: instal pytorch → {package_manager} install torch
    输入: torch version → {package_manager} show torch
    输入: remove numpy → {package_manager} uninstall numpy
    
    当前输入: {user_input}
    """
    
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[{
                "role": "system",
                "content": "你是一个专业的Python包管理助手，只需返回修正后的命令，不要解释"
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.1
        )
        
        corrected = response.choices[0].message.content.strip()
        return extract_command_from_response(corrected)
    except Exception as e:
        print(f"AI调用出错: {e}")
        return f"{package_manager} {user_input}", user_input.split()[-1] if user_input else ""

def execute_command(command: str) -> None:
    """执行命令"""
    print(f"执行: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"执行失败: {e.stderr}")

def confirm_action(prompt: str = "确认执行? [Y/n]: ") -> bool:
    """获取用户确认"""
    print(prompt, end="", flush=True)
    try:
        if sys.platform == "win32":
            import msvcrt
            key = msvcrt.getch().decode().lower()
        else:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                key = sys.stdin.read(1).lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        print()
        return key in ("y", "\r", "\n")
    except Exception:
        print()
        return False

def main():
    config = initialize_config()
    client = ZhipuAI(api_key=config["api_key"])
    pm = config["package_manager"]
    
    print(f"\n当前包管理器: {pm}")
    print(f"镜像源: {config.get('mirror_source', '未配置')}")
    print("支持操作: install/uninstall/show/list/search/download/config等")
    print("特殊命令: change mirror (切换镜像源)")
    print("输入命令(如'torch -v'), Ctrl+C退出\n")
    
    while True:
        try:
            cmd = input(f"{pm} >>> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit"):
                break
                
            # 特殊处理换源命令
            if cmd.lower() in ("change mirror", "mirror"):
                setup_mirror(config)
                continue
                
            corrected, package = get_ai_correction(client, cmd, pm)
            
            # 如果命令未变化且是有效命令，直接执行
            if corrected == cmd and is_valid_command(cmd):
                execute_command(cmd)
                continue
                
            print(f"修正结果: {corrected}")
            
            if confirm_action():
                execute_command(corrected)
                
        except KeyboardInterrupt:
            print("\n退出程序")
            break
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    try:
        import zhipuai
    except ImportError:
        print("请先安装依赖: pip install zhipuai")
        sys.exit(1)
    
    main()
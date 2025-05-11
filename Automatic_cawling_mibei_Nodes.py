# 导入必要的标准库模块
import os  # 操作系统接口，用于文件路径操作
import re  # 正则表达式，用于文本模式匹配
import sys  # 系统相关功能，如退出程序
import time  # 时间相关功能，如延时
import random  # 随机数生成
import requests  # HTTP请求库
import subprocess  # 子进程管理
import psutil  # 进程和系统工具库
import json  # JSON数据处理
from bs4 import BeautifulSoup  # HTML解析库
from datetime import datetime  # 日期时间处理
import logging  # 日志记录
from typing import Optional, List, Dict, Any  # 类型注解


# === 配置类 ===
class Config:
    """程序全局配置类"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取脚本所在目录绝对路径
    V2RAYN_EXE = "v2rayN.exe"  # v2rayN可执行文件名
    CONFIG_FILE = "config.json"  # v2rayN配置文件名称
    NODES_FILE = "nodes.txt"  # 节点信息保存文件名
    CHECK_TIMEOUT = 10  # 进程检查超时时间(秒)
    MAIN_URL = 'https://www.mibei77.com/'  # 目标网站主URL

    # 用户代理列表，用于模拟不同浏览器
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",  # Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X...",  # Safari
        # 其他用户代理...
    ]


# === 日志设置 ===
def setup_logging():
    """配置日志记录系统"""
    logging.basicConfig(
        level=logging.INFO,  # 设置日志级别为INFO
        format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
        handlers=[  # 日志处理器
            logging.FileHandler(os.path.join(Config.BASE_DIR, 'v2ray_updater.log')),  # 文件日志
            logging.StreamHandler()  # 控制台日志
        ]
    )


# === 工具函数 ===
def get_random_headers() -> Dict[str, str]:
    """生成包含随机User-Agent的请求头字典

    返回:
        Dict[str, str]: 包含随机User-Agent的请求头
    """
    return {"User-Agent": random.choice(Config.USER_AGENTS)}  # 随机选择一个用户代理


def get_v2rayn_path() -> str:
    """获取v2rayN可执行文件完整路径

    返回:
        str: v2rayN.exe的完整路径
    """
    return os.path.join(Config.BASE_DIR, Config.V2RAYN_EXE)  # 拼接完整路径


def get_config_path() -> str:
    """获取v2rayN配置文件完整路径

    返回:
        str: config.json的完整路径
    """
    return os.path.join(Config.BASE_DIR, Config.CONFIG_FILE)


def get_nodes_path() -> str:
    """获取节点信息文件保存路径

    返回:
        str: nodes.txt的完整路径
    """
    return os.path.join(Config.BASE_DIR, Config.NODES_FILE)


# === v2rayN 进程操作 ===
def is_v2rayn_running() -> bool:
    """检查v2rayN进程是否正在运行

    返回:
        bool: True表示正在运行，False表示未运行
    """
    # 遍历所有进程
    for proc in psutil.process_iter(['name']):
        # 检查进程名是否包含v2rayn.exe(不区分大小写)
        if proc.info['name'] and 'v2rayn.exe' in proc.info['name'].lower():
            return True
    return False


def wait_for_v2rayn(timeout: int = Config.CHECK_TIMEOUT) -> bool:
    """等待v2rayN启动，直到超时

    参数:
        timeout (int): 等待超时时间(秒)

    返回:
        bool: True表示启动成功，False表示超时
    """
    logging.info(f"等待 v2rayN.exe 启动（最多 {timeout} 秒）...")
    start_time = time.time()  # 记录开始时间

    # 在超时时间内循环检查
    while time.time() - start_time < timeout:
        if is_v2rayn_running():  # 检查进程
            logging.info("v2rayN 已启动")
            return True
        time.sleep(1)  # 每秒检查一次

    logging.warning("超时未检测到 v2rayN 进程")
    return False


def terminate_v2rayn() -> bool:
    """终止正在运行的v2rayN进程

    返回:
        bool: True表示成功终止，False表示终止失败
    """
    logging.info("尝试关闭旧的 v2rayN...")
    terminated = False  # 终止状态标志

    # 遍历所有进程
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'v2rayn.exe' in proc.info['name'].lower():
            try:
                proc.terminate()  # 尝试正常终止
                proc.wait(timeout=5)  # 等待进程结束
                terminated = True
            except psutil.TimeoutExpired:  # 超时未结束
                proc.kill()  # 强制终止
                terminated = True
            except psutil.NoSuchProcess:  # 进程已不存在
                pass

    time.sleep(1)  # 等待进程完全退出
    return terminated


def start_v2rayn() -> bool:
    """启动v2rayN程序

    返回:
        bool: True表示启动成功，False表示启动失败
    """
    v2rayn_path = get_v2rayn_path()  # 获取完整路径

    # 检查文件是否存在
    if not os.path.exists(v2rayn_path):
        logging.error(f"v2rayN 文件不存在: {v2rayn_path}")
        return False

    try:
        logging.info("正在启动 v2rayN...")
        # 使用subprocess启动程序
        subprocess.Popen([v2rayn_path])
        return wait_for_v2rayn()  # 等待启动完成
    except Exception as e:
        logging.error(f"启动 v2rayN 失败: {e}")
        return False


def restart_v2rayn() -> bool:
    """重启v2rayN程序

    返回:
        bool: True表示重启成功，False表示失败
    """
    terminate_v2rayn()  # 先终止
    return start_v2rayn()  # 再启动


# === 订阅管理 ===
def update_v2rayn_subscription(new_url: str) -> bool:
    """更新v2rayN的订阅链接

    参数:
        new_url (str): 新的订阅URL

    返回:
        bool: True表示更新成功，False表示失败
    """
    config_path = get_config_path()  # 获取配置文件路径

    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        logging.error(f"无法找到 config.json 文件：{config_path}")
        return False

    try:
        # 读取配置文件内容
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # 获取订阅列表，默认为空列表
        subscriptions = config_data.get("subscriptions", [])
        updated = False  # 更新状态标志

        # 检查是否已存在相同URL
        for sub in subscriptions:
            if sub.get("url") == new_url:
                logging.info("已存在相同订阅链接，无需更新")
                return True

        # 添加新订阅
        subscriptions.append({"url": new_url})
        config_data["subscriptions"] = subscriptions

        # 写回配置文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

        logging.info(f"已更新 v2rayN 订阅列表，新的链接：{new_url}")
        return True

    except json.JSONDecodeError as e:
        logging.error(f"无法解析 config.json 文件：{e}")
    except Exception as e:
        logging.error(f"更新订阅失败: {type(e).__name__}: {e}")

    return False


# === 节点获取功能 ===
def get_today_date_str() -> str:
    """获取当前日期的格式化字符串

    返回:
        str: 格式为"YYYY年MM月DD日"的日期字符串
    """
    return datetime.now().strftime('%Y年%m月%d日')


def find_node_page_url(main_url: str) -> Optional[str]:
    """从主页查找包含当天节点的页面URL

    参数:
        main_url (str): 网站主页URL

    返回:
        Optional[str]: 找到的URL，未找到则返回None
    """
    try:
        logging.info(f"正在访问主页面: {main_url}")
        # 发送HTTP GET请求
        response = requests.get(main_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()  # 检查请求是否成功

        # 解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')
        today = get_today_date_str()  # 获取当天日期字符串

        # 查找所有<a>标签
        for a_tag in soup.find_all('a', href=True):
            link_text = a_tag.get_text(strip=True)  # 获取链接文本
            # 检查是否符合当天节点链接特征
            if link_text.startswith(today) and "免费精选节点" in link_text:
                return a_tag['href']  # 返回找到的URL

        logging.warning("未找到今日免费精选节点链接")
    except requests.RequestException as e:
        logging.error(f"访问主页面失败: {e}")
    except Exception as e:
        logging.error(f"解析主页面失败: {e}")

    return None


def extract_node_url(node_page_url: str) -> Optional[str]:
    """从节点页面提取节点文件URL

    参数:
        node_page_url (str): 节点页面URL

    返回:
        Optional[str]: 找到的节点文件URL，未找到则返回None
    """
    try:
        logging.info(f"正在访问节点页面: {node_page_url}")
        response = requests.get(node_page_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()

        # 使用正则表达式匹配.txt文件链接
        txt_pattern = re.compile(r'http[s]?://mm\.mibei77\.com/\d{6}/[\w\.]+\.txt', re.IGNORECASE)
        txt_links = txt_pattern.findall(response.text)  # 查找所有匹配的URL

        if txt_links:
            return txt_links[0]  # 返回第一个匹配的URL

        logging.warning("未找到 .txt 节点链接")
    except requests.RequestException as e:
        logging.error(f"访问节点页面失败: {e}")
    except Exception as e:
        logging.error(f"解析节点页面失败: {e}")

    return None


def download_nodes_file(node_url: str) -> bool:
    """下载节点文件并保存到本地

    参数:
        node_url (str): 节点文件URL

    返回:
        bool: True表示下载成功，False表示失败
    """
    try:
        logging.info(f"正在下载节点文件: {node_url}")
        response = requests.get(node_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()  # 检查下载是否成功

        # 获取保存路径并写入文件
        nodes_path = get_nodes_path()
        with open(nodes_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        logging.info(f"节点文件已保存到: {nodes_path}")
        return True
    except requests.RequestException as e:
        logging.error(f"下载节点文件失败: {e}")
    except Exception as e:
        logging.error(f"保存节点文件失败: {e}")

    return False


# === 主程序 ===
def main():
    """程序主入口函数"""
    setup_logging()  # 初始化日志系统
    logging.info("=== v2ray自动更新程序开始运行 ===")

    # 1. 检查v2rayN可执行文件是否存在
    v2rayn_path = get_v2rayn_path()
    if not os.path.exists(v2rayn_path):
        logging.error(f"错误: v2rayN 文件不存在: {v2rayn_path}")
        sys.exit(1)  # 退出程序

    # 2. 确保v2rayN正在运行
    if not is_v2rayn_running():
        if not start_v2rayn():  # 尝试启动
            sys.exit(1)  # 启动失败则退出

    # 3. 获取节点页面URL
    node_page_url = find_node_page_url(Config.MAIN_URL)
    if not node_page_url:
        sys.exit(1)  # 未找到则退出

    # 4. 从节点页面提取节点文件URL
    node_url = extract_node_url(node_page_url)
    if not node_url:
        sys.exit(1)  # 未找到则退出

    # 5. 下载节点文件
    if not download_nodes_file(node_url):
        sys.exit(1)  # 下载失败则退出

    # 6. 更新订阅并重启v2rayN
    if update_v2rayn_subscription(node_url):
        if not restart_v2rayn():  # 重启v2rayN
            sys.exit(1)  # 重启失败则退出

    logging.info("=== 程序运行完成 ===")

def update_and_restart_if_needed():
    """更新节点并重启 v2rayN 的主流程"""
    # 获取节点页面
    node_page_url = find_node_page_url(Config.MAIN_URL)
    if not node_page_url:
        return

    # 提取节点下载链接
    node_url = extract_node_url(node_page_url)
    if not node_url:
        return

    # 下载节点文件
    if not download_nodes_file(node_url):
        return

    # 更新订阅并重启
    if update_v2rayn_subscription(node_url):
        restart_v2rayn()

def daemon_monitor(interval: int = 300):
    """后台守护主循环，每隔 interval 秒检查一次"""
    setup_logging()
    logging.info("=== v2rayN 后台监控程序已启动 ===")

    try:
        while True:
            if not is_v2rayn_running():
                logging.warning("检测到 v2rayN 未运行，开始更新节点并重启...")
                update_and_restart_if_needed()
            else:
                logging.info("v2rayN 正常运行中，无需更新")
            time.sleep(interval)  # 等待下一个周期
    except KeyboardInterrupt:
        logging.info("监控程序手动中断，退出。")
    except Exception as e:
        logging.error(f"后台监控发生异常: {type(e).__name__}: {e}")

def generate_silent_bat_and_vbs(script_name: str = "v2ray_auto_updater.py", bat_name: str = "run_v2ray_silent.bat", vbs_name: str = "silent_runner.vbs"):
    """
    生成一个 .bat 和 .vbs 文件组合来实现 Python 脚本的静默运行。

    参数:
        script_name (str): Python 脚本文件名
        bat_name (str): 生成的 .bat 文件名
        vbs_name (str): 生成的 .vbs 文件名
    """
    # 创建 VBS 文件的内容
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python {os.path.join(Config.BASE_DIR, script_name)}", 0, False
'''

    # VBS 文件路径
    vbs_path = os.path.join(Config.BASE_DIR, vbs_name)

    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        print(f"[√] 已生成静默运行 VBS 文件: {vbs_path}")
    except Exception as e:
        print(f"[×] 生成 VBS 文件失败: {e}")

    # 创建 BAT 文件的内容
    bat_content = f"""@echo off
REM 使用 VBS 脚本在后台运行 Python 脚本
start /min "" cscript "{vbs_path}"
exit
"""

    # BAT 文件路径
    bat_path = os.path.join(Config.BASE_DIR, bat_name)

    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        print(f"[√] 已生成静默运行批处理文件: {bat_path}")
    except Exception as e:
        print(f"[×] 生成 .bat 文件失败: {e}")


if __name__ == "__main__":
    daemon_monitor(interval=600)  # 每10分钟检测一次


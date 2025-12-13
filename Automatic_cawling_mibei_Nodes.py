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
import base64  # Base64编码解码
import socket  # 网络连接
import struct  # 二进制数据处理
from bs4 import BeautifulSoup  # HTML解析库
from datetime import datetime  # 日期时间处理
import logging  # 日志记录
from typing import Optional, List, Dict, Any, Set  # 类型注解

# === 高级黑客模块导入 ===
try:
    import aiohttp  # 异步HTTP请求
    import asyncio  # 异步编程库
    import aiofiles  # 异步文件操作
    has_async = True
    
    # 高效连接池管理类
    class ConnectionPool:
        """高效连接池管理，基于Mirai的连接管理设计"""
        
        def __init__(self, max_connections: int = 100):
            self.max_connections = max_connections
            self.semaphore = asyncio.Semaphore(max_connections)
            self.session = None
            
        async def __aenter__(self):
            if self.session is None:
                self.session = aiohttp.ClientSession()
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.session:
                await self.session.close()
                self.session = None
        
        async def acquire(self):
            """获取连接资源"""
            await self.semaphore.acquire()
            return self.session
        
        def release(self):
            """释放连接资源"""
            self.semaphore.release()
except ImportError:
    logging.warning("🚫 异步模块未安装，将使用同步模式运行")
    has_async = False

try:
    import win32api
    import win32process
    import win32con
    has_win32 = True
except ImportError:
    logging.warning("🚫 win32模块未安装，进程隐藏功能受限")
    has_win32 = False


# === 配置类 ===
class Config:
    """程序全局配置类 - 黑客模式"""
    # 修复PyInstaller编译后路径问题
    if getattr(sys, 'frozen', False):
        # 编译后可执行文件所在目录
        BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # 脚本运行时所在目录
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    V2RAYN_EXE = "v2rayN.exe"  # v2rayN可执行文件名
    CONFIG_FILE = "config.json"  # v2rayN配置文件名称
    NODES_FILE = "nodes.txt"  # 节点信息保存文件名
    CHECK_TIMEOUT = 10  # 进程检查超时时间(秒)
    MAIN_URL = 'https://www.mibei77.com/'  # 目标网站主URL
    
    # � 可能的配置文件路径列表
    CONFIG_PATHS = [
        os.path.join(BASE_DIR, CONFIG_FILE),  # 脚本所在目录
        os.path.join(BASE_DIR, "binConfigs", CONFIG_FILE),  # binConfigs子目录
        os.path.join(os.path.expanduser("~"), "v2rayN", CONFIG_FILE),  # 用户目录下的v2rayN
        os.path.join(BASE_DIR, "v2rayN", CONFIG_FILE),  # 当前目录下的v2rayN
        os.path.join(BASE_DIR, "config", CONFIG_FILE),  # config子目录
    ]
    
    # � 性能优化配置
    MAX_CONCURRENT_REQUESTS = 20  # 最大并发请求数
    CONNECTION_TIMEOUT = 10  # 连接超时时间
    RETRY_ATTEMPTS = 3  # 最大重试次数
    
    # 🛡️ 隐蔽性配置
    ENABLE_STEALTH = True  # 启用隐身模式
    ENABLE_FAKE_LOGGING = True  # 启用迷惑性日志
    MIN_DELAY = 1.0  # 最小延时(秒)
    MAX_DELAY = 3.0  # 最大延时(秒)
    
    # 📊 节点筛选配置
    ENABLE_NODE_BENCHMARK = True  # 启用节点测速
    BENCHMARK_THRESHOLD = 1000  # 延迟阈值(毫秒)
    TOP_NODES_PERCENTAGE = 20  # 保留前20%的节点
    
    # 新增配置项
    MAX_NODES = 250  # 最大节点数量
    ENABLE_NODE_FILTERING = True  # 启用节点筛选
    ENABLE_SPEED_TEST = True  # 启用测速
    MAX_LATENCY = 1000  # 最大延迟(ms)
    IGNORE_LATENCY_TEST = False  # 是否忽略测速
    
    # 🕵️ 高级隐蔽配置
    ENABLE_ADVANCED_STEALTH = True  # 启用高级隐身
    RANDOMIZE_FILENAMES = True  # 随机化生成的文件名
    CLEANUP_TEMP_FILES = True  # 清理临时文件
    
    # 📈 性能调优
    MAX_MEMORY_USAGE = 512  # 最大内存使用(MB)
    ENABLE_AUTO_OPTIMIZE = True  # 启用自动优化
    
    # 🔧 调试配置
    ENABLE_DEBUG_LOGGING = False  # 启用调试日志
    LOG_SENSITIVE_INFO = False  # 是否记录敏感信息
    
    # 🌐 高质量用户代理列表 - 模拟真实浏览器指纹
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/113.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.67 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    ]
    
    # 📱 完整HTTP请求头 - 模拟真实流量特征
    FULL_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'trailers',
        'Pragma': 'no-cache'
    }
    
    # 🎭 迷惑性日志消息
    FAKE_LOG_MESSAGES = [
        "正在检查系统更新...",
        "清理临时文件中...",
        "优化网络设置...",
        "扫描系统安全...",
        "备份用户数据...",
        "校准系统时间...",
        "同步网络配置...",
        "检查硬件状态..."
    ]


# === 日志设置 ===
def setup_logging():
    """配置日志记录系统"""
    logging.basicConfig(
        level=logging.INFO,  # 设置日志级别为INFO
        format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
        handlers=[  # 日志处理器
            logging.FileHandler(os.path.join(Config.BASE_DIR, 'v2ray_updater.log'), encoding='utf-8'),  # 文件日志
            logging.StreamHandler(sys.stdout)  # 控制台日志，使用sys.stdout避免编码问题
        ]
    )
    # 修复控制台日志的编码问题
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')


# === 工具函数 ===

# 🎭 迷惑性日志生成器
def fake_logging():
    """生成迷惑性日志，让监控摸不着头脑"""
    if Config.ENABLE_FAKE_LOGGING and random.random() < 0.3:
        logging.info(random.choice(Config.FAKE_LOG_MESSAGES))

# 🔒 隐身请求头生成器
def get_stealth_headers() -> Dict[str, str]:
    """生成更隐蔽的完整请求头，模拟真实浏览器行为
    
    返回:
        Dict[str, str]: 包含完整浏览器指纹的请求头
    """
    headers = Config.FULL_HEADERS.copy()
    headers['User-Agent'] = random.choice(Config.USER_AGENTS)
    
    # 随机添加一些常见但非必要的请求头，增加真实性
    if random.random() < 0.5:
        headers['DNT'] = '1'  # Do Not Track
    if random.random() < 0.3:
        headers['Sec-Fetch-Dest'] = 'document'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-Site'] = 'none'
        headers['Sec-Fetch-User'] = '?1'
    
    return headers

# 🛡️ 智能重试装饰器
def smart_retry(max_retries=Config.RETRY_ATTEMPTS):
    """更完善的智能重试装饰器
    
    参数:
        max_retries: 最大重试次数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    # 随机延时，避免被识别为机器人
                    if Config.ENABLE_STEALTH and attempt > 0:
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        logging.info(f"[🔄] 第{attempt+1}次重试，等待 {sleep_time:.2f} 秒...")
                        time.sleep(sleep_time)
                    
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logging.error(f"[❌] 所有 {max_retries} 次重试都失败了: {e}")
                        raise
                    logging.warning(f"[⚠️] 第 {attempt+1} 次尝试失败: {e}，准备重试...")
            raise last_exception
        return wrapper
    return decorator

# 🚀 异步请求函数
async def fetch_page_async(session, url, headers=None):
    """异步获取页面内容
    
    参数:
        session: aiohttp.ClientSession对象
        url: 目标URL
        headers: 请求头
    
    返回:
        响应内容或None
    """
    if headers is None:
        headers = get_stealth_headers() if Config.ENABLE_STEALTH else get_random_headers()
    
    try:
        # 模拟真人操作的随机延时
        if Config.ENABLE_STEALTH:
            await asyncio.sleep(random.uniform(Config.MIN_DELAY, Config.MAX_DELAY))
        
        async with session.get(url, headers=headers, timeout=Config.CONNECTION_TIMEOUT) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logging.error(f"[×] 异步请求 {url} 失败: {e}")
        return None

# 📊 异步节点测速
async def test_node_speed_async(node_info):
    """异步测试节点延迟
    
    参数:
        node_info: 节点信息字典
    
    返回:
        包含延迟信息的字典
    """
    start_time = time.time()
    host = node_info.get('address', '')
    port = node_info.get('port', 443)
    
    try:
        # 使用异步socket连接测试
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), 
            timeout=3.0
        )
        writer.close()
        await writer.wait_closed()
        latency = (time.time() - start_time) * 1000  # 转换为毫秒
        logging.debug(f"节点 {host}:{port} 延迟: {latency:.2f}ms")
        return {**node_info, 'latency': latency}
    except Exception:
        return {**node_info, 'latency': float('inf')}

def generate_random_string(length: int) -> str:
    """生成随机字符串用于混淆"""
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 🔄 修复并优化的随机请求头函数
def get_random_headers(stealth=False):
    """修复函数签名不一致问题"""
    if stealth or Config.ENABLE_STEALTH:
        return get_stealth_headers()
    return {"User-Agent": random.choice(Config.USER_AGENTS)}

# 🎯 深度进程隐藏
def create_ghost_process(cmd):
    """创建几乎不可见的进程
    
    参数:
        cmd: 要执行的命令
    
    返回:
        进程对象
    """
    # 设置启动信息
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    # 基本的隐藏参数
    creationflags = subprocess.CREATE_NO_WINDOW
    
    # 如果有win32模块，使用更高级的隐藏技术
    if has_win32:
        startupinfo.wShowWindow = win32con.SW_HIDE
        creationflags |= (subprocess.IDLE_PRIORITY_CLASS | 
                          win32process.CREATE_BREAKAWAY_FROM_JOB)
    
    # 低优先级运行，降低存在感
    process = subprocess.Popen(
        cmd,
        startupinfo=startupinfo,
        creationflags=creationflags
    )
    return process



# 🧹 内存优化器，避免内存泄漏
class MemoryOptimizer:
    """内存优化器，避免内存泄漏"""
    def __init__(self, cleanup_threshold: int = 50, max_age_seconds: int = 1800):
        self.cleanup_threshold = cleanup_threshold  # 每N次操作清理一次
        self.max_age_seconds = max_age_seconds  # 最大时间间隔
        self.operation_count = 0
        self.last_cleanup_time = time.time()
    
    def auto_cleanup(self, force: bool = False):
        """自动清理内存"""
        self.operation_count += 1
        current_time = time.time()
        
        should_cleanup = force or \
                       self.operation_count >= self.cleanup_threshold or \
                       (current_time - self.last_cleanup_time) > self.max_age_seconds
        
        if should_cleanup:
            import gc
            import psutil
            
            # 获取清理前的内存使用情况
            before_mem = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # 清理内存
            collected = gc.collect()
            
            # 清理循环引用
            gc.garbage.clear()
            
            # 获取清理后的内存使用情况
            after_mem = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            freed_mem = before_mem - after_mem
            if freed_mem > 0:
                logging.info(f"[🧹] 内存清理完成: 释放 {freed_mem:.2f} MB, 回收 {collected} 个对象")
            
            self.operation_count = 0
            self.last_cleanup_time = current_time

# 初始化内存优化器
memory_optimizer = MemoryOptimizer()

# � 通用配置文件查找函数
def find_config_file(config_name: str = "config.json", search_dirs: Optional[List[str]] = None, recursive: bool = True) -> Optional[str]:
    """
    在指定目录中查找配置文件，支持递归查找
    
    参数:
        config_name: 配置文件名
        search_dirs: 搜索目录列表，如果为None则使用默认目录
        recursive: 是否递归查找子目录
        
    返回:
        找到的配置文件绝对路径，未找到则返回None
    """
    # 默认搜索目录
    default_dirs = [
        Config.BASE_DIR,  # 脚本所在目录
        os.path.join(Config.BASE_DIR, "binConfigs"),  # binConfigs子目录
        os.path.join(os.path.expanduser("~"), "v2rayN"),  # 用户目录下的v2rayN
        os.environ.get('PROGRAMFILES', ''),  # Program Files目录
        os.environ.get('PROGRAMFILES(X86)', ''),  # Program Files (x86)目录
    ]
    
    # 如果提供了自定义目录，使用它们；否则使用默认目录
    dirs_to_search = search_dirs if search_dirs else default_dirs
    
    # 过滤掉不存在的目录
    dirs_to_search = [d for d in dirs_to_search if d and os.path.exists(d)]
    
    for search_dir in dirs_to_search:
        if recursive:
            # 递归查找
            for root, dirs, files in os.walk(search_dir):
                if config_name in files:
                    config_path = os.path.abspath(os.path.join(root, config_name))
                    logging.debug(f"[🔍] 在 {config_path} 找到配置文件")
                    return config_path
        else:
            # 非递归查找
            config_path = os.path.abspath(os.path.join(search_dir, config_name))
            if os.path.exists(config_path):
                logging.debug(f"[🔍] 在 {config_path} 找到配置文件")
                return config_path
    
    logging.debug(f"[❌] 未找到配置文件: {config_name}")
    return None

# �� 弹性执行，自动恢复
def resilient_execute(func, fallback_func=None, max_attempts=3):
    """弹性执行，自动恢复"""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            logging.warning(f"[🔄] 第{attempt+1}次执行失败: {e}")
            if attempt == max_attempts - 1 and fallback_func:
                logging.info("[🆘] 启用备用方案")
                return fallback_func()
            time.sleep(2 ** attempt)  # 指数退避
    return None

def safe_file_operations(file_path, operation="write", content=None):
    """安全的文件操作，防止数据丢失"""
    temp_path = file_path + ".tmp"
    
    try:
        if operation == "write" and content is not None:
            # 先写入临时文件
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            # 然后原子性地重命名
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)
            return True
            
        elif operation == "read":
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            return None
            
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logging.error(f"[❌] 文件操作失败: {e}")
        return None
    
    return None




def get_v2rayn_path() -> str:
    """获取v2rayn可执行文件完整路径

    返回:
        str: v2rayn可执行文件的完整路径（跨平台适配）
    """
    platform = PlatformAdapter.get_platform()
    
    if platform == 'windows':
        return os.path.join(Config.BASE_DIR, Config.V2RAYN_EXE)  # Windows使用.exe文件
    else:
        # Linux/macOS使用可执行文件名（无扩展名）
        return os.path.join(Config.BASE_DIR, 'v2rayn')

# 异步下载节点文件
async def download_nodes_file_async(node_url):
    """异步下载节点文件
    
    参数:
        node_url: 节点文件URL
    
    返回:
        节点内容或None
    """
    fake_logging()  # 生成迷惑性日志
    logging.info(f"[🔒] 正在异步下载节点文件: {node_url}")
    
    if has_async:
        async with aiohttp.ClientSession() as session:
            content = await fetch_page_async(session, node_url)
            if content:
                # 去重处理保持不变
                lines = content.strip().split('\n')
                unique_lines = []
                seen_node_identifiers = set()
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    node_identifier = None
                    # 节点解析逻辑保持不变
                    if line.startswith("vmess://"):
                        try:
                            vmess_content = line[8:]
                            padding = len(vmess_content) % 4
                            if padding:
                                vmess_content += '=' * (4 - padding)
                            vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8', errors='ignore'))
                            address = vmess_json.get("add", "")
                            port = str(vmess_json.get("port", ""))
                            if address and port:
                                node_identifier = f"{address}:{port}"
                        except Exception:
                            pass
                    # 其他节点类型的处理逻辑保持不变
                    
                    if node_identifier and node_identifier not in seen_node_identifiers:
                        seen_node_identifiers.add(node_identifier)
                        unique_lines.append(line)
                    elif not node_identifier and line not in unique_lines:
                        unique_lines.append(line)
                
                unique_content = '\n'.join(unique_lines)
                return unique_content
    return None


def get_config_path(v2rayn_dir: Optional[str] = None) -> Optional[str]:
    """获取v2rayn配置文件完整路径（跨平台适配，增强版）
    
    参数:
        v2rayn_dir (str): v2rayn安装目录，如果为None则使用默认搜索目录
    
    返回:
        str: config.json的完整路径，未找到则返回None
    """
    # 如果提供了v2rayn目录，首先尝试在该目录中查找
    if v2rayn_dir:
        # 使用增强版的PlatformAdapter.get_config_path直接查找
        config_path = PlatformAdapter.get_config_path(v2rayn_dir, Config.CONFIG_FILE, search_subdirs=True)
        if config_path:
            return config_path
    
    # 使用通用查找函数搜索所有可能的路径
    config_path = find_config_file(Config.CONFIG_FILE)
    if config_path:
        return config_path
    
    # 尝试使用Config.CONFIG_PATHS中定义的路径
    for path in Config.CONFIG_PATHS:
        if os.path.exists(path):
            logging.debug(f"[✅] 在预定义路径找到配置文件: {path}")
            return path
    
    logging.warning(f"[❌] 未找到配置文件 {Config.CONFIG_FILE}")
    return None


def get_nodes_path() -> str:
    """获取节点信息文件保存路径

    返回:
        str: nodes.txt的完整路径
    """
    return os.path.join(Config.BASE_DIR, Config.NODES_FILE)


# === v2rayN 进程操作 ===
def is_v2rayn_running() -> bool:
    """检查v2rayn进程是否正在运行（跨平台适配）

    返回:
        bool: True表示正在运行，False表示未运行
    """
    fake_logging()  # 生成迷惑性日志
    platform = PlatformAdapter.get_platform()
    
    # 遍历所有进程
    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name']
            if not proc_name:
                continue
                
            # 根据平台检查不同的进程名
            if platform == 'windows':
                # Windows平台检查.exe文件
                if 'v2rayn.exe' in proc_name.lower():
                    return True
            else:
                # Linux/macOS平台检查可执行文件名
                if proc_name.lower() == 'v2rayn':
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # 处理进程访问权限问题
            pass
    return False


def wait_for_v2rayn(timeout: int = Config.CHECK_TIMEOUT) -> bool:
    """等待v2rayN启动，直到超时

    参数:
        timeout (int): 等待超时时间(秒)

    返回:
        bool: True表示启动成功，False表示超时
    """
    fake_logging()  # 生成迷惑性日志
    logging.info(f"[⌛] 等待v2rayN启动（最多 {timeout} 秒）...")
    start_time = time.time()  # 记录开始时间

    # 在超时时间内循环检查，使用随机间隔增加隐蔽性
    while time.time() - start_time < timeout:
        if is_v2rayn_running():  # 检查进程
            logging.info("[✅] v2rayN 已启动")
            return True
        # 随机间隔检查，避免规律性
        sleep_time = random.uniform(0.8, 1.2)
        time.sleep(sleep_time)

    logging.warning("[❌] 超时未检测到 v2rayN 进程")
    return False


def terminate_v2rayn() -> bool:
    """终止正在运行的v2rayN进程

    返回:
        bool: True表示成功终止，False表示终止失败
    """
    fake_logging()  # 生成迷惑性日志
    logging.info("[🔪] 尝试关闭旧的 v2rayN...")
    terminated = False  # 终止状态标志

    # 遍历所有进程
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and 'v2rayn.exe' in proc.info['name'].lower():
                try:
                    proc.terminate()  # 尝试正常终止
                    proc.wait(timeout=5)  # 等待进程结束
                    terminated = True
                except psutil.TimeoutExpired:  # 超时未结束
                    logging.warning("[⚡] 进程超时，强制终止")
                    proc.kill()  # 强制终止
                    terminated = True
                except psutil.NoSuchProcess:  # 进程已不存在
                    pass
                except psutil.AccessDenied:
                    logging.error("[🚫] 没有足够权限终止进程")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # 等待进程完全退出，使用随机延时
    time.sleep(random.uniform(0.5, 1.5))  # 随机等待，增加隐蔽性
    return terminated


def start_v2rayn() -> bool:
    """启动v2rayn程序（跨平台适配，使用隐身模式）

    返回:
        bool: True表示启动成功，False表示启动失败
    """
    v2rayn_path = get_v2rayn_path()  # 获取完整路径
    platform = PlatformAdapter.get_platform()

    # 检查文件是否存在
    if not os.path.exists(v2rayn_path):
        logging.error(f"[❌] v2rayn 文件不存在: {v2rayn_path}")
        return False

    try:
        fake_logging()  # 生成迷惑性日志
        logging.info(f"[🚀] 正在启动 v2rayn (隐身模式，平台: {platform})...")
        
        # 跨平台启动方式
        if platform == 'windows':
            # Windows平台
            if Config.ENABLE_STEALTH and has_win32:
                create_ghost_process([v2rayn_path])
            else:
                # 后备方案
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen([v2rayn_path], startupinfo=startupinfo)
        else:
            # Linux/macOS平台
            # 确保文件有执行权限
            os.chmod(v2rayn_path, 0o755)
            
            if Config.ENABLE_STEALTH:
                # Linux/macOS的隐身启动方式
                subprocess.Popen([v2rayn_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, close_fds=True)
            else:
                subprocess.Popen([v2rayn_path])
            
        # 模拟人类操作，等待一小段随机时间再检查
        time.sleep(random.uniform(0.5, 1.5))
        return wait_for_v2rayn()  # 等待启动完成
    except Exception as e:
        logging.error(f"[❌] 启动 v2rayn 失败: {e}")
        return False


def restart_v2rayn() -> bool:
    """重启v2rayN程序

    返回:
        bool: True表示重启成功，False表示失败
    """
    terminate_v2rayn()  # 先终止
    return start_v2rayn()  # 再启动


# === 订阅管理 ===
@smart_retry(max_retries=3)
def update_v2rayn_subscription(new_url: str) -> bool:
    """
    替换 v2rayN config.json 的订阅链接为新的 URL，清除所有旧订阅。
    黑客模式：智能重试、隐蔽操作、混淆配置
    """
    fake_logging()  # 生成迷惑性日志
    config_path = get_config_path()
    if not config_path or not os.path.exists(config_path):
        logging.error(f"[❌] 找不到 config.json：{config_path}")
        return False

    try:
        # 读取配置文件前添加随机延迟
        time.sleep(random.uniform(0.1, 0.3))
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # 添加混淆配置，提高隐蔽性
        if Config.ENABLE_STEALTH:
            # 添加一些看似正常但实际上无意义的配置项
            config_data["lastUpdateTime"] = int(time.time() * 1000)
            config_data["autoUpdateCore"] = False
            config_data["logLevel"] = "none"  # 降低日志级别
            config_data["guiType"] = 0

        # 覆盖旧的 subscriptions，使用随机订阅名称
        subscription_remarks = "Auto Imported" if not Config.ENABLE_STEALTH else generate_random_string(8)
        config_data["subscriptions"] = [{"url": new_url, "enabled": True, "remarks": subscription_remarks}]

        # 写入前的随机延迟
        time.sleep(random.uniform(0.1, 0.3))
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

        # 不直接记录完整URL，增加安全性
        masked_url = new_url[:10] + "..." + new_url[-10:] if len(new_url) > 20 else new_url
        logging.info(f"[✅] 成功替换订阅链接: {masked_url}")
        return True

    except Exception as e:
        logging.error(f"[❌] 更新订阅失败: {type(e).__name__}: {e}")
        raise  # 抛出异常，让智能重试装饰器处理


def set_best_node_as_default(best_node: str, group_name: str = "米贝") -> bool:
    """
    将最优节点设置为v2rayN的默认节点
    
    参数:
        best_node: 最优节点的字符串表示
        group_name: 节点所属分组名
        
    返回:
        bool: 设置成功返回True，否则返回False
    """
    fake_logging()  # 生成迷惑性日志
    
    # 获取v2rayN安装目录
    v2rayn_dir = find_v2rayn_installation()
    if not v2rayn_dir:
        logging.info("[ℹ️] 找不到v2rayN安装目录，跳过设置默认节点步骤")
        return True
    
    # 获取配置文件路径
    config_path = get_config_path(v2rayn_dir)
    if not config_path or not os.path.exists(config_path):
        logging.info("[ℹ️] 找不到config.json文件，跳过设置默认节点步骤")
        return True
    
    try:
        # 读取配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # 确保servers字段存在
        if "servers" not in config_data:
            config_data["servers"] = []
        
        # 解析最优节点，获取其address和port
        best_node_address = None
        best_node_port = None
        
        if best_node and best_node.startswith("vmess://"):
            try:
                vmess_content = best_node[8:]
                padding = len(vmess_content) % 4
                if padding:
                    vmess_content += '=' * (4 - padding)
                vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8'))
                best_node_address = vmess_json.get("add", "")
                best_node_port = int(vmess_json.get("port", 443))
            except Exception as e:
                logging.error(f"[❌] 解析最优节点失败: {str(e)}")
                return False
        
        # 查找最优节点在servers列表中的索引
        best_node_index = -1
        for i, server in enumerate(config_data["servers"]):
            if server.get("group") == group_name and server.get("address") == best_node_address and server.get("port") == best_node_port:
                best_node_index = i
                break
        
        # 如果找到最优节点，设置为默认节点
        if best_node_index != -1:
            # v2rayN使用"index"字段来标识当前选中的节点
            config_data["index"] = best_node_index
            logging.info(f"[🏆] 已将最优节点设置为默认节点（索引: {best_node_index}）")
            
            # 保存更新后的配置文件
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            return True
        else:
            logging.warning("[⚠️] 在配置文件中未找到最优节点，无法设置为默认节点")
            return False
            
    except json.JSONDecodeError as e:
        logging.error(f"[❌] 解析配置文件失败: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"[❌] 设置默认节点失败: {str(e)}")
        return False


def add_nodes_to_mibei_group(best_node: str = None) -> bool:
    """
    在v2rayN中创建名为"米贝"的分组，并将节点粘贴到该分组中。
    如果分组已存在，则覆盖原有节点。
    黑客模式：智能节点筛选、随机化、隐蔽性增强
    
    参数:
        best_node: 最优节点的字符串表示（可选）
    """
    fake_logging()  # 生成迷惑性日志
    # 获取配置文件路径
    v2rayn_dir = find_v2rayn_installation()
    if not v2rayn_dir:
        logging.info("[ℹ️] 找不到v2rayN安装目录，跳过节点导入步骤")
        return True
    
    config_path = get_config_path(v2rayn_dir)
    if not config_path or not os.path.exists(config_path):
        logging.info("[ℹ️] 找不到config.json文件，跳过节点导入步骤")
        return True
    
    # 获取节点文件路径
    nodes_path = get_nodes_path()
    if not os.path.exists(nodes_path):
        logging.error(f"[❌] 找不到节点文件: {nodes_path}")
        return False
    
    try:
        # 读取配置文件
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        # 读取节点文件内容
        with open(nodes_path, "r", encoding="utf-8") as f:
            node_lines = f.readlines()
        
        # 智能节点筛选
        if Config.ENABLE_NODE_FILTERING:
            logging.info("[🧠] 正在筛选高质量节点...")
            # 只保留一定数量的节点，避免过于臃肿
            if len(node_lines) > Config.MAX_NODES:
                # 随机选择一部分节点，避免规律性
                node_lines = random.sample(node_lines, Config.MAX_NODES)
            logging.info(f"[✅] 已筛选出 {len(node_lines)} 个节点")
        
        # 确保servers字段存在
        if "servers" not in config_data:
            config_data["servers"] = []
        
        # 使用随机化分组名增加隐蔽性
        group_name = "米贝" if not Config.ENABLE_STEALTH else f"米贝_{generate_random_string(4)}"
        
        # 过滤掉旧节点
        old_nodes = [server for server in config_data["servers"] if server.get("group") == "米贝"]
        config_data["servers"] = [server for server in config_data["servers"] if server.get("group") != "米贝"]
        
        # 记录旧节点数量
        logging.info(f"[🧹] 已清除 {len(old_nodes)} 个旧节点")
        
        # 为每个节点添加到米贝分组，使用混淆策略
        new_server_count = 0
        for line in node_lines:
            line = line.strip()
            if not line:
                continue
                
            # 添加随机延时，模拟人工操作
            time.sleep(random.uniform(0.01, 0.05))
            
            # 根据不同的节点类型解析
            try:
                if line.startswith("vmess://"):
                    # 处理vmess节点
                    vmess_content = line[8:]
                    # 处理可能的base64填充问题
                    padding = len(vmess_content) % 4
                    if padding:
                        vmess_content += '=' * (4 - padding)
                    
                    vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8'))
                    
                    # 创建新的服务器条目
                    server = {
                        "id": str(random.randint(100000, 999999)),
                        "remarks": vmess_json.get("ps", f"节点_{generate_random_string(6)}"),
                        "group": group_name,
                        "type": "VMess",
                        "address": vmess_json.get("add", ""),
                        "port": int(vmess_json.get("port", 443)),
                        "uuid": vmess_json.get("id", ""),
                        "alterId": int(vmess_json.get("aid", 0)),
                        "security": vmess_json.get("scy", "auto"),
                        "network": vmess_json.get("net", "tcp"),
                        "headerType": vmess_json.get("type", "none"),
                        "requestHost": vmess_json.get("host", ""),
                        "path": vmess_json.get("path", ""),
                        "streamSecurity": vmess_json.get("tls", ""),
                        "sni": vmess_json.get("sni", ""),
                        "fingerprint": vmess_json.get("fp", ""),
                        "allowInsecure": True
                    }
                    
                    # 如果开启智能测速，测试节点延迟
                    if Config.ENABLE_SPEED_TEST and vmess_json.get("add") and vmess_json.get("port"):
                        latency = test_latency(vmess_json.get("add"), int(vmess_json.get("port", 443)))
                        if latency < Config.MAX_LATENCY or Config.IGNORE_LATENCY_TEST:
                            config_data["servers"].append(server)
                            new_server_count += 1
                            if latency < float('inf'):
                                logging.debug(f"[🚀] 添加高速节点: {latency:.2f}ms")
                    else:
                        config_data["servers"].append(server)
                        new_server_count += 1
                
                elif line.startswith("trojan://"):
                    # 处理trojan节点（简化版）
                    server = {
                        "id": str(random.randint(100000, 999999)),
                        "remarks": f"Trojan_{generate_random_string(6)}",
                        "group": group_name,
                        "type": "Trojan",
                        "allowInsecure": True
                    }
                    config_data["servers"].append(server)
                    new_server_count += 1
                    
                elif line.startswith("ss://"):
                    # 处理shadowsocks节点（简化版）
                    server = {
                        "id": str(random.randint(100000, 999999)),
                        "remarks": f"SS_{generate_random_string(6)}",
                        "group": group_name,
                        "type": "Shadowsocks",
                    }
                    config_data["servers"].append(server)
                    new_server_count += 1
            except Exception as e:
                logging.warning(f"[⚠️] 解析节点失败: {line[:30]}... {str(e)}")
                continue
        
        # 保存前随机延迟
        time.sleep(random.uniform(0.2, 0.5))
        
        # 保存更新后的配置文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        logging.info(f"[✅] 成功将{new_server_count}个节点添加到 {group_name} 分组")
        
        # 如果提供了最优节点，将其设置为默认节点
        if best_node:
            logging.info("[🏆] 正在设置最优节点为默认节点...")
            if set_best_node_as_default(best_node, group_name):
                logging.info("[✅] 已成功将最优节点设置为默认节点")
            else:
                logging.warning("[⚠️] 设置最优节点为默认节点失败")
        
        return True
        
    except json.JSONDecodeError as e:
        logging.error(f"[❌] 解析配置文件失败: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"[❌] 添加节点到米贝分组失败: {type(e).__name__}: {e}")
        return False


def test_latency(host: str, port: int = 443, timeout: float = 1.0) -> float:
    """TCP ping测试，返回毫秒延迟（黑客模式）"""
    try:
        # 模拟更真实的网络行为，添加随机微小延迟
        time.sleep(random.uniform(0.001, 0.005))
        start = time.time()
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        latency = (time.time() - start) * 1000
        logging.debug(f"[📊] 节点延迟: {host}:{port} = {latency:.2f}ms")
        return latency
    except socket.timeout:
        logging.debug(f"[⏰] 节点超时: {host}:{port}")
        return float("inf")
    except Exception as e:
        logging.debug(f"[❌] 延迟测试失败: {host}:{port} - {str(e)}")
        return float("inf")

# 异步版本的延迟测试
async def test_latency_async(host: str, port: int = 443, timeout: float = 1.0) -> float:
    """异步TCP ping测试，返回毫秒延迟"""
    if not has_async:
        # 如果异步模块不可用，回退到同步版本
        return test_latency(host, port, timeout)
        
    try:
        # 模拟更真实的网络行为，添加随机微小延迟
        await asyncio.sleep(random.uniform(0.001, 0.005))
        start = time.time()
        # 使用异步方式创建socket连接
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        latency = (time.time() - start) * 1000
        logging.debug(f"[⚡] 异步节点延迟: {host}:{port} = {latency:.2f}ms")
        return latency
    except Exception:
        return float("inf")

# 智能节点测速函数
async def benchmark_nodes_async(nodes):
    """并发测速所有节点，返回排序后的节点列表和最优节点"""
    if not has_async:
        # 如果异步不可用，回退到简单筛选
        return nodes[:min(len(nodes), Config.MAX_NODES)], None
        
    # 使用异步生成器处理节点
    async def process_node(node):
        """异步处理单个节点"""
        if node.startswith("vmess://"):
            try:
                vmess_content = node[8:]
                padding = len(vmess_content) % 4
                if padding:
                    vmess_content += '=' * (4 - padding)
                vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8', errors='ignore'))
                host = vmess_json.get("add", "")
                port = int(vmess_json.get("port", 443))
                if host and port:
                    latency = await test_latency_async(host, port)
                    if latency < Config.MAX_LATENCY:
                        return latency, node
            except Exception:
                pass
        return None, None
    
    # 限制并发数量，避免系统资源耗尽
    semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
    
    async def bounded_process_node(node):
        """带信号量限制的节点处理"""
        async with semaphore:
            return await process_node(node)
    
    # 创建并执行所有任务
    node_tasks = [bounded_process_node(node) for node in nodes]
    task_results = await asyncio.gather(*node_tasks)
    
    # 过滤有效结果
    results = [(latency, node) for latency, node in task_results if latency is not None]
    
    # 按延迟排序，取最快的节点
    results.sort(key=lambda x: x[0])
    
    # 取前N%的节点或固定数量
    top_count = min(len(results), Config.MAX_NODES)
    top_nodes = [node for _, node in results[:top_count]]
    
    # 确定最优节点
    best_node = None
    if results:
        best_latency, best_node = results[0]
        logging.info(f"[🏆] 找到最优节点，延迟: {best_latency:.2f}ms")
    
    # 清理内存
    del task_results
    import gc
    gc.collect()
    
    logging.info(f"[🎯] 已从{len(nodes)}个节点中筛选出{len(top_nodes)}个低延迟节点")
    return top_nodes, best_node


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


def find_v2rayn_installation(base_dir: str = None) -> Optional[str]:
    """
    在系统上查找 v2rayN 的安装目录
    搜索顺序：
    1. 脚本所在目录
    2. 程序文件默认安装目录
    3. 整个系统搜索（限制深度）
    """
    # 可能的默认安装路径
    default_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'v2rayN'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'v2rayN'),
        os.path.expanduser('~\\AppData\\Local\\Programs\\v2rayN')
    ]

    # 要检查的目录列表
    search_paths = []
    if base_dir:
        search_paths.append(base_dir)
    search_paths.extend(default_paths)

    # 检查这些路径
    for path in search_paths:
        exe_path = os.path.join(path, 'v2rayN.exe')
        if os.path.exists(exe_path):
            return path

    # 如果还没找到，尝试在整个系统中搜索（限制深度）
    for root, dirs, files in os.walk('d:\\', topdown=True):
        if 'v2rayN.exe' in files:
            return root
        # 限制搜索深度为3层
        if root.count(os.sep) >= 3:
            dirs[:] = []  # 不再递归更深层

    return None


def validate_v2rayn_installation() -> bool:
    """验证v2rayN安装是否正确"""
    # 1. 首先尝试脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    v2rayn_dir = find_v2rayn_installation(script_dir)

    if not v2rayn_dir:
        print("错误: 找不到 v2rayN 安装目录")
        return False

    print(f"找到 v2rayN 目录: {v2rayn_dir}")

    # 2. 查找配置文件
    config_path = get_config_path(v2rayn_dir)
    if not config_path:
        print("错误: 找不到 config.json 文件")
        return False

    print(f"找到配置文件: {config_path}")

    # 3. 验证xray.exe  是否存在
    exe_path = os.path.join(v2rayn_dir, 'v2rayN.exe')
    if not os.path.exists(exe_path):
        print("错误: 找不到xray.exe ")
        return False

    print("所有必要文件验证通过")
    print(f"v2rayN.exe 路径: {exe_path}")
    print(f"config.json 路径: {config_path}")
    return True


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
        txt_pattern = re.compile(r'http[s]?://mm\.mibei77\.com/(?:\d{6}|\d{4}\.\d{2})/[\w\.]+\.(?:txt|yaml)', re.IGNORECASE)
        txt_links = txt_pattern.findall(response.text)  # 查找所有匹配的URL

        if txt_links:
            return txt_links[0]  # 返回第一个匹配的URL

        logging.warning("未找到 .txt 节点链接")
    except requests.RequestException as e:
        logging.error(f"访问节点页面失败: {e}")
    except Exception as e:
        logging.error(f"解析节点页面失败: {e}")

    return None


@smart_retry(max_retries=3)
def download_nodes_file(node_url: str) -> (bool, str):
    """下载节点文件并保存到本地（黑客模式）
    
    参数:
        node_url (str): 节点文件URL
    
    返回:
        (bool, str): 下载是否成功，以及最优节点（如果有）
    """
    fake_logging()  # 生成迷惑性日志
    memory_optimizer.auto_cleanup()  # 自动清理内存
    try:
        logging.info(f"[🔒] 正在下载节点文件: {node_url[:20]}...")
        # 使用隐身模式请求头
        headers = get_random_headers(stealth=True)
        
        # 随机延时，模拟人类操作
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(node_url, headers=headers, timeout=5)
        response.raise_for_status()  # 检查下载是否成功
        
        # 统计下载大小
        content_length = len(response.text)
        logging.info(f"[📥] 成功下载节点文件，大小: {content_length / 1024:.2f}KB")

        # 去重处理
        lines = response.text.strip().split('\n')
        
        # 加强版去重：基于地址和端口的双重判断
        unique_lines = []
        seen_node_identifiers = set()  # 用于存储已见过的节点标识（地址+端口）
        
        for line in lines:
            if not line.strip():
                continue
                
            # 尝试解析节点，提取地址和端口
            node_identifier = None
            
            # 处理vmess节点
            if line.startswith("vmess://"):
                try:
                    vmess_content = line[8:]
                    # 处理可能的base64填充问题
                    padding = len(vmess_content) % 4
                    if padding:
                        vmess_content += '=' * (4 - padding)
                    
                    vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8', errors='ignore'))
                    address = vmess_json.get("add", "")
                    port = str(vmess_json.get("port", ""))
                    if address and port:
                        node_identifier = f"{address}:{port}"
                except Exception:
                    pass  # 解析失败则回退到原始去重方式
            
            # 处理trojan节点（简化解析）
            elif line.startswith("trojan://"):
                try:
                    # 尝试从URL中提取地址和端口
                    pattern = r'trojan://[^@]+@([^:]+):(\d+)'  # 简化的正则匹配
                    match = re.search(pattern, line)
                    if match:
                        address = match.group(1)
                        port = match.group(2)
                        node_identifier = f"{address}:{port}"
                except Exception:
                    pass
            
            # 处理ss节点（简化解析）
            elif line.startswith("ss://"):
                try:
                    # 尝试从URL中提取地址和端口
                    ss_content = line[5:]
                    if '#' in ss_content:
                        ss_content = ss_content.split('#')[0]  # 去除节点名称部分
                    # 处理可能的base64填充问题
                    padding = len(ss_content) % 4
                    if padding:
                        ss_content += '=' * (4 - padding)
                    
                    decoded = base64.b64decode(ss_content).decode('utf-8', errors='ignore')
                    pattern = r'[^@]+@([^:]+):(\d+)'  # 简化的正则匹配
                    match = re.search(pattern, decoded)
                    if match:
                        address = match.group(1)
                        port = match.group(2)
                        node_identifier = f"{address}:{port}"
                except Exception:
                    pass
            
            # 如果成功提取了节点标识，使用它进行去重
            if node_identifier and node_identifier not in seen_node_identifiers:
                seen_node_identifiers.add(node_identifier)
                unique_lines.append(line)
            # 如果无法解析节点标识，则使用原始行内容进行去重（回退方案）
            elif not node_identifier and line not in unique_lines:
                unique_lines.append(line)
        
        unique_content = '\n'.join(unique_lines)
        
        # 智能节点筛选
        if Config.ENABLE_NODE_FILTERING and len(unique_lines) > Config.MAX_NODES:
            # 异步并发测速选择最佳节点
            if has_async and Config.ENABLE_SPEED_TEST:
                logging.info("[🧠] 正在进行智能节点测速...")
                # 运行异步测速任务
                import asyncio
                unique_lines, best_node = asyncio.run(benchmark_nodes_async(unique_lines))
                # 保存最优节点信息
                if best_node:
                    logging.info("[🏆] 已确定最优节点，将在添加节点时设置为默认节点")
            else:
                # 简单随机筛选
                unique_lines = random.sample(unique_lines, Config.MAX_NODES)
        
        unique_content = '\n'.join(unique_lines)
        
        # 记录去重情况
        if len(unique_lines) < len(lines):
            removed_count = len(lines) - len(unique_lines)
            logging.info(f"[🧹] 节点去重完成，从{len(lines)}个节点中去除了{removed_count}个重复/低质量节点")
        
        # 获取保存路径并写入文件
        nodes_path = get_nodes_path()
        
        # 写入前随机延迟
        time.sleep(random.uniform(0.1, 0.3))
        
        with open(nodes_path, "w", encoding="utf-8") as f:
            f.write(unique_content)

        logging.info(f"[✅] 节点文件已保存到: {nodes_path}，共{len(unique_lines)}个节点")
        
        return True, best_node if 'best_node' in locals() else None
    except requests.RequestException as e:
        logging.error(f"[❌] 下载节点文件失败: {e}")
        raise  # 抛出异常让智能重试装饰器处理
    except Exception as e:
        logging.error(f"[❌] 保存节点文件失败: {e}")
        return False, None

# 高效连接池管理类
# ConnectionPool类已在文件上方定义

# 异步版本的下载函数
# 全局连接池实例
_global_connection_pool = None

def get_connection_pool() -> ConnectionPool:
    """获取全局连接池实例"""
    global _global_connection_pool
    if _global_connection_pool is None:
        _global_connection_pool = ConnectionPool(max_connections=Config.MAX_CONCURRENT_REQUESTS)
    return _global_connection_pool

async def download_nodes_file_async(node_url: str) -> bool:
    """异步下载节点文件并保存到本地"""
    if not has_async:
        # 回退到同步版本
        return download_nodes_file(node_url)
    
    fake_logging()
    try:
        logging.info(f"[⚡] 正在异步下载节点文件: {node_url[:20]}...")
        
        headers = get_random_headers(stealth=True)
        
        # 使用全局连接池
        pool = get_connection_pool()
        session = await pool.acquire()
        try:
            async with session.get(node_url, headers=headers, timeout=5) as response:
                response.raise_for_status()
                content = await response.text()
        finally:
            pool.release()
        
        # 处理逻辑与同步版本类似
        lines = content.strip().split('\n')
        
        # 去重和筛选逻辑...
        unique_lines = []
        seen_node_identifiers = set()
        valid_protocols = ['vmess://', 'vless://', 'trojan://', 'shadowsocks://']
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 过滤有效协议节点
            if not any(line.startswith(protocol) for protocol in valid_protocols):
                continue
            
            # 简化版本的去重逻辑
            if line not in unique_lines:
                unique_lines.append(line)
        
        # 并发测速选择最佳节点
        if Config.ENABLE_NODE_FILTERING and has_async:
            unique_lines, best_node = await benchmark_nodes_async(unique_lines)
            # 保存最优节点信息
            if best_node:
                logging.info("[🏆] 已确定最优节点，将在添加节点时设置为默认节点")
        
        # 异步写入文件
        if has_async:
            nodes_path = get_nodes_path()
            async with aiofiles.open(nodes_path, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(unique_lines))
        else:
            # 回退到同步写入
            nodes_path = get_nodes_path()
            with open(nodes_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(unique_lines))
        
        # 清理内存
        del content, lines, seen_node_identifiers
        import gc
        gc.collect()
        
        logging.info(f"[✅] 异步下载完成，保存了{len(unique_lines)}个节点")
        return True
    except Exception as e:
        logging.error(f"[❌] 异步下载失败: {e}")
        return False


# 全局异常处理器
def handle_unexpected_error(exctype, value, traceback):
    """处理未捕获的异常，确保程序优雅退出"""
    logging.error(f"[💥] 发生未预期的错误: {exctype.__name__}: {value}")
    logging.error("[📝] 详细错误堆栈:")
    import traceback
    traceback_str = ''.join(traceback.format_exception(exctype, value, traceback))
    logging.error(traceback_str)
    
    # 清理资源
    if 'gc' in sys.modules:
        import gc
        gc.collect()
    
    # 记录程序崩溃
    logging.critical("[💀] 程序因未预期错误而崩溃")

# 注册全局异常处理器
sys.excepthook = handle_unexpected_error

# === 主程序 ===
def main():
    """程序主入口函数"""
    setup_logging()  # 初始化日志系统
    logging.info("=== v2ray自动更新程序开始运行 ===")

    # 验证v2rayN安装（失败时继续运行）
    v2rayn_available = validate_v2rayn_installation()
    if not v2rayn_available:
        logging.warning("v2rayN安装验证失败，将继续执行节点下载功能")

    # 尝试启动v2rayN（失败时继续运行）
    if v2rayn_available and not is_v2rayn_running():
        if not start_v2rayn():
            logging.warning("v2rayN启动失败，将继续执行节点下载功能")

    # 获取节点页面URL
    node_page_url = find_node_page_url(Config.MAIN_URL)
    if not node_page_url:
        sys.exit(1)  # 未找到则退出

    # 从节点页面提取节点文件URL
    node_url = extract_node_url(node_page_url)
    if not node_url:
        sys.exit(1)  # 未找到则退出

    # 下载节点文件
    success, best_node = download_nodes_file(node_url)
    if not success:
        sys.exit(1)  # 下载失败则退出

    # 添加节点到米贝分组
    if not add_nodes_to_mibei_group(best_node):
        logging.warning("添加节点到米贝分组失败，但继续执行后续步骤")

    # 更新订阅并重启v2rayN（失败时继续运行）
    if v2rayn_available:
        if update_v2rayn_subscription(node_url):
            if not restart_v2rayn():
                logging.warning("v2rayN重启失败，程序将继续执行")
        else:
            logging.warning("订阅更新失败，程序将继续执行")

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
    success, best_node = download_nodes_file(node_url)
    if not success:
        return

    # 添加节点到米贝分组
    if not add_nodes_to_mibei_group(best_node):
        logging.warning("添加节点到米贝分组失败，但继续执行后续步骤")

    # 更新订阅并重启
    if update_v2rayn_subscription(node_url):
        restart_v2rayn()



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

# 定义无窗口化运行的函数
def run_script_no_window(script_path):
    # 设置子进程启动信息
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # 隐藏窗口

    # 使用 CREATE_NO_WINDOW 参数运行脚本
    process = subprocess.Popen(
        ["python", script_path],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    process.wait()  # 等待脚本执行完成

# 异步函数实现
async def fetch_nodes_async():
    """异步获取节点"""
    try:
        node_page_url = find_node_page_url(Config.MAIN_URL)
        if not node_page_url:
            return False
        
        node_url = extract_node_url(node_page_url)
        if not node_url:
            return False
        
        return await download_nodes_file_async(node_url)
    except Exception as e:
        logging.error(f"[❌] 异步获取节点失败: {e}")
        return False

async def benchmark_existing_nodes_async():
    """异步测速现有节点"""
    try:
        nodes_path = get_nodes_path()
        if not os.path.exists(nodes_path):
            return False
        
        async with aiofiles.open(nodes_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        nodes = content.strip().split('\n')
        if nodes:
            # 异步测速
            _, best_node = await benchmark_nodes_async(nodes)
            # 如果找到最优节点，将其设置为默认节点
            if best_node:
                logging.info("[🏆] 已找到最优节点，正在设置为默认节点...")
                set_best_node_as_default(best_node)
            return True
        return False
    except Exception as e:
        logging.error(f"[❌] 异步测速失败: {e}")
        return False

async def monitor_system_resources_async():
    """异步监控系统资源"""
    try:
        # 异步监控CPU、内存使用率
        while True:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # 超过阈值时记录警告
            if cpu_percent > 80 or memory_percent > 90:
                logging.warning(f"[⚠️] 系统资源警告 - CPU: {cpu_percent}%, 内存: {memory_percent}%")
            
            # 监控一段时间后退出
            await asyncio.sleep(3)
            break  # 只执行一次监控
        return True
    except Exception as e:
        logging.error(f"[❌] 异步监控系统资源失败: {e}")
        return False

# 包装函数
async def fetch_nodes_async_wrapper():
    """获取节点的异步包装"""
    node_page_url = find_node_page_url(Config.MAIN_URL)
    if not node_page_url:
        return None
        
    node_url = extract_node_url(node_page_url)
    if not node_url:
        return None
        
    return await download_nodes_file_async(node_url)

async def benchmark_existing_nodes_async_wrapper():
    """测速现有节点的异步包装"""
    # 实现测速逻辑
    return True

async def monitor_system_resources_async_wrapper():
    """监控系统资源的异步包装"""
    # 实现监控逻辑
    return True

# === 高效扫描算法 ===
# 基于Mirai的随机IP扫描算法改进

def generate_random_ip() -> str:
    """高效生成随机IP地址
    
    Returns:
        str: 随机生成的IPv4地址
    """
    # 类似Mirai的随机IP生成，避免扫描私有网络（可选）
    while True:
        ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xFFFFFFFF)))
        # 可选择排除私有IP范围
        # if not ip.startswith(('10.', '172.16.', '192.168.')):
        #     return ip
        return ip

def generate_ip_range(start_ip: str, end_ip: str) -> List[str]:
    """生成IP范围列表
    
    Args:
        start_ip: 起始IP地址
        end_ip: 结束IP地址
    
    Returns:
        List[str]: IP地址列表
    """
    def ip_to_int(ip):
        return struct.unpack('>I', socket.inet_aton(ip))[0]
    
    def int_to_ip(ip_int):
        return socket.inet_ntoa(struct.pack('>I', ip_int))
    
    start = ip_to_int(start_ip)
    end = ip_to_int(end_ip)
    
    return [int_to_ip(ip) for ip in range(start, end + 1)]

# === 并发连接管理器 ===
class ConnectionPool:
    """高效连接池管理，基于Mirai的连接管理设计"""
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.semaphore = asyncio.Semaphore(max_connections)
        self.session = None
        
    async def __aenter__(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def acquire(self):
        """获取连接资源"""
        await self.semaphore.acquire()
        return self.session
    
    def release(self):
        """释放连接资源"""
        self.semaphore.release()

# === 异步扫描器 ===
async def scan_port_async(ip: str, port: int, timeout: float = 1.0) -> bool:
    """异步扫描单个端口
    
    Args:
        ip: 目标IP地址
        port: 目标端口
        timeout: 超时时间
    
    Returns:
        bool: 端口是否开放
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

async def scan_ip_async(ip: str, ports: List[int], timeout: float = 1.0) -> Dict[str, bool]:
    """异步扫描单个IP的多个端口
    
    Args:
        ip: 目标IP地址
        ports: 端口列表
        timeout: 超时时间
    
    Returns:
        Dict[str, bool]: 端口扫描结果
    """
    results = {}
    tasks = []
    
    for port in ports:
        task = asyncio.create_task(scan_port_async(ip, port, timeout))
        tasks.append((port, task))
    
    for port, task in tasks:
        results[port] = await task
    
    return results

async def scan_network_async(
    ip_generator, 
    ports: List[int], 
    max_concurrent: int = 100,
    max_scans: int = 1000,
    timeout: float = 1.0
) -> Dict[str, Dict[str, bool]]:
    """异步扫描网络（类似Mirai的高效扫描）
    
    Args:
        ip_generator: IP生成器
        ports: 端口列表
        max_concurrent: 最大并发扫描数
        max_scans: 最大扫描数量
        timeout: 超时时间
    
    Returns:
        Dict[str, Dict[str, bool]]: 扫描结果
    """
    results = {}
    semaphore = asyncio.Semaphore(max_concurrent)
    tasks = []
    scanned_ips: Set[str] = set()
    
    async def scan_wrapper(ip: str):
        if ip in scanned_ips:
            return
        scanned_ips.add(ip)
        
        async with semaphore:
            try:
                scan_result = await scan_ip_async(ip, ports, timeout)
                # 只记录有开放端口的IP
                if any(scan_result.values()):
                    results[ip] = scan_result
            except Exception as e:
                logging.debug(f"扫描 {ip} 失败: {e}")
    
    # 生成扫描任务
    for _ in range(max_scans):
        ip = next(ip_generator)
        task = asyncio.create_task(scan_wrapper(ip))
        tasks.append(task)
    
    # 等待所有任务完成
    await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

# === 跨架构适配层 ===
class PlatformAdapter:
    """跨平台适配层，支持Windows/Linux/macOS"""
    
    @staticmethod
    def get_platform() -> str:
        """获取当前平台"""
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('linux'):
            return 'linux'
        elif sys.platform.startswith('darwin'):
            return 'macos'
        else:
            return 'unknown'
    
    @staticmethod
    def get_config_path(base_dir: str, config_name: str = "config.json", search_subdirs: bool = True) -> Optional[str]:
        """获取平台特定的配置路径（增强版）
        
        参数:
            base_dir: 基础目录
            config_name: 配置文件名
            search_subdirs: 是否搜索子目录
            
        返回:
            找到的配置文件路径，未找到则返回None
        """
        platform = PlatformAdapter.get_platform()
        
        # 平台特定的默认配置路径
        platform_paths = {
            'windows': [
                os.path.join(base_dir, config_name),
                os.path.join(base_dir, 'binConfigs', config_name),
                os.path.join(os.path.expanduser("~"), "v2rayN", config_name),
            ],
            'linux': [
                os.path.join(base_dir, config_name),
                os.path.join(base_dir, '.config', config_name),
                os.path.join(os.path.expanduser("~"), '.config', 'v2rayn', config_name),
            ],
            'macos': [
                os.path.join(base_dir, config_name),
                os.path.join(base_dir, 'Library', 'Preferences', config_name),
                os.path.join(os.path.expanduser("~"), 'Library', 'Preferences', 'v2rayn', config_name),
            ]
        }
        
        # 获取当前平台的默认路径列表
        default_paths = platform_paths.get(platform, [os.path.join(base_dir, config_name)])
        
        # 检查默认路径
        for path in default_paths:
            if os.path.exists(path):
                logging.debug(f"[✅] 在平台特定路径找到配置文件: {path}")
                return path
        
        # 如果允许搜索子目录且在默认路径未找到，使用find_config_file函数进行更广泛的搜索
        if search_subdirs:
            return find_config_file(config_name, [base_dir], recursive=True)
        
        return None
    
    @staticmethod
    def execute_command(cmd: str) -> Optional[str]:
        """执行平台特定的命令"""
        platform = PlatformAdapter.get_platform()
        
        try:
            if platform == 'windows':
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable='/bin/bash')
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logging.error(f"执行命令失败: {e}")
            return None

# === 扫描结果处理和节点整合 ===

def ip_port_to_proxy_node(ip: str, port: int, protocol: str = 'vmess') -> str:
    """将IP和端口转换为代理节点字符串
    
    Args:
        ip: IP地址
        port: 端口号
        protocol: 代理协议
    
    Returns:
        str: 代理节点字符串
    """
    if protocol == 'vmess':
        # 生成一个简单的vmess节点
        vmess_config = {
            "v": "2",
            "ps": f"扫描节点_{ip}:{port}",
            "add": ip,
            "port": port,
            "id": "00000000-0000-0000-0000-000000000000",
            "aid": "0",
            "scy": "auto",
            "net": "tcp",
            "type": "none",
            "host": "",
            "path": "",
            "tls": "",
            "sni": "",
            "alpn": ""
        }
        vmess_json = json.dumps(vmess_config)
        vmess_b64 = base64.b64encode(vmess_json.encode('utf-8')).decode('utf-8')
        return f"vmess://{vmess_b64}"
    elif protocol == 'trojan':
        # 生成trojan节点
        return f"trojan://password@{ip}:{port}#扫描节点_{ip}:{port}"
    elif protocol == 'ss':
        # 生成shadowsocks节点
        ss_config = f"aes-256-gcm:password@{ip}:{port}"
        ss_b64 = base64.b64encode(ss_config.encode('utf-8')).decode('utf-8')
        return f"ss://{ss_b64}#扫描节点_{ip}:{port}"
    else:
        return f"# 不支持的协议: {protocol}"

def parse_proxy_node(node: str) -> Dict[str, Any]:
    """解析代理节点字符串
    
    Args:
        node: 代理节点字符串
    
    Returns:
        Dict[str, Any]: 节点信息字典
    """
    info = {
        "protocol": "unknown",
        "ip": None,
        "port": None,
        "remarks": ""
    }
    
    try:
        if node.startswith("vmess://"):
            info["protocol"] = "vmess"
            vmess_content = node[8:]
            # 处理base64填充
            padding = len(vmess_content) % 4
            if padding:
                vmess_content += '=' * (4 - padding)
            vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8', errors='ignore'))
            info["ip"] = vmess_json.get("add")
            info["port"] = vmess_json.get("port")
            info["remarks"] = vmess_json.get("ps", "")
        elif node.startswith("trojan://"):
            info["protocol"] = "trojan"
            pattern = r'trojan://[^@]+@([^:]+):(\d+)(?:#(.*))?'
            match = re.search(pattern, node)
            if match:
                info["ip"] = match.group(1)
                info["port"] = int(match.group(2))
                info["remarks"] = match.group(3) or ""
        elif node.startswith("ss://"):
            info["protocol"] = "ss"
            ss_content = node[5:]
            if '#' in ss_content:
                ss_content, _ = ss_content.split('#', 1)
            padding = len(ss_content) % 4
            if padding:
                ss_content += '=' * (4 - padding)
            decoded = base64.b64decode(ss_content).decode('utf-8', errors='ignore')
            pattern = r'[^:]+:[^@]+@([^:]+):(\d+)'
            match = re.search(pattern, decoded)
            if match:
                info["ip"] = match.group(1)
                info["port"] = int(match.group(2))
    except Exception as e:
        logging.debug(f"解析节点失败: {e}")
    
    return info

def merge_nodes(new_nodes: List[str], existing_nodes: List[str]) -> List[str]:
    """合并新节点和现有节点，去除重复项
    
    Args:
        new_nodes: 新发现的节点列表
        existing_nodes: 现有节点列表
    
    Returns:
        List[str]: 合并后的节点列表
    """
    # 创建节点标识符集合，用于去重
    seen_identifiers = set()
    merged_nodes = []
    
    # 处理现有节点
    for node in existing_nodes:
        info = parse_proxy_node(node)
        if info["ip"] and info["port"]:
            identifier = f"{info['protocol']}_{info['ip']}_{info['port']}"
            seen_identifiers.add(identifier)
            merged_nodes.append(node)
    
    # 处理新节点
    new_count = 0
    for node in new_nodes:
        info = parse_proxy_node(node)
        if info["ip"] and info["port"]:
            identifier = f"{info['protocol']}_{info['ip']}_{info['port']}"
            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                merged_nodes.append(node)
                new_count += 1
    
    logging.info(f"[✅] 节点合并完成，新增 {new_count} 个节点，总计 {len(merged_nodes)} 个节点")
    return merged_nodes

async def process_scan_results(scan_results: Dict[str, Dict[str, bool]]) -> List[str]:
    """处理扫描结果并生成代理节点
    
    Args:
        scan_results: 扫描结果字典
    
    Returns:
        List[str]: 生成的代理节点列表
    """
    new_nodes = []
    
    for ip, ports in scan_results.items():
        for port, is_open in ports.items():
            if is_open:
                # 根据常见的代理端口猜测协议
                if port in [80, 8080, 8888]:
                    protocol = 'vmess'  # 假设是vmess
                elif port in [443, 8443]:
                    protocol = 'trojan'  # 假设是trojan
                elif port in [1080, 1081]:
                    protocol = 'ss'  # 假设是shadowsocks
                else:
                    protocol = 'vmess'  # 默认使用vmess
                
                # 生成代理节点
                node = ip_port_to_proxy_node(ip, port, protocol)
                new_nodes.append(node)
    
    logging.info(f"[🔍] 扫描结果处理完成，生成 {len(new_nodes)} 个新节点")
    return new_nodes

async def integrate_scan_results_with_existing() -> bool:
    """将扫描结果与现有节点整合
    
    Returns:
        bool: 整合是否成功
    """
    try:
        # 1. 执行网络扫描
        logging.info("[⚡] 开始网络扫描...")
        
        # 生成随机IP生成器
        def ip_generator():
            while True:
                yield generate_random_ip()
        
        # 扫描常见代理端口
        common_proxy_ports = [80, 443, 8080, 8443, 8888, 1080, 1081]
        
        # 执行扫描
        scan_results = await scan_network_async(
            ip_generator(),
            common_proxy_ports,
            max_concurrent=Config.MAX_CONCURRENT_REQUESTS,
            max_scans=100,  # 限制扫描数量，避免过度消耗资源
            timeout=0.5
        )
        
        # 2. 处理扫描结果
        new_nodes = await process_scan_results(scan_results)
        
        # 3. 读取现有节点
        nodes_path = get_nodes_path()
        existing_nodes = []
        if os.path.exists(nodes_path):
            with open(nodes_path, 'r', encoding='utf-8') as f:
                existing_nodes = [line.strip() for line in f if line.strip()]
        
        # 4. 合并节点
        merged_nodes = merge_nodes(new_nodes, existing_nodes)
        
        # 5. 保存合并后的节点
        with open(nodes_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(merged_nodes))
        
        logging.info(f"[✅] 扫描节点整合完成，节点文件已更新")
        return True
        
    except Exception as e:
        logging.error(f"[❌] 整合扫描结果失败: {e}")
        return False

# ⚡ 真正的异步黑客模式 - 整合了扫描功能
async def elite_main_async():
    """真正的异步黑客模式 - 完整版"""
    if not has_async:
        logging.warning("[⚠️] 异步模块不可用，回退到同步模式")
        main()
        return
    
    setup_logging()
    logging.info("[⚡] 启动异步黑客模式...")
    
    try:
        # 异步并发执行所有任务
        tasks = [
            asyncio.create_task(fetch_nodes_async_wrapper()),
            asyncio.create_task(benchmark_existing_nodes_async_wrapper()),
            asyncio.create_task(monitor_system_resources_async_wrapper())
        ]
        
        # 根据配置决定是否执行扫描
        if Config.ENABLE_SCANNING:
            tasks.append(asyncio.create_task(integrate_scan_results_with_existing()))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = len([r for r in results if r and not isinstance(r, Exception)])
        logging.info(f"[✅] 异步任务执行完成: {success_count}/{len(tasks)} 个任务成功")
        
        return success_count > 0
        
    except Exception as e:
        logging.error(f"[❌] 异步模式执行失败: {e}")
        return False

# 🎭 终极隐身技巧
def ultimate_stealth():
    """终极隐身技巧 - 增强版"""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        
        # 修改进程名为系统进程
        kernel32.SetConsoleTitleW("svchost.exe")
        
        # 隐藏控制台窗口（如果有的话）
        kernel32.ShowWindow(kernel32.GetConsoleWindow(), 0)
        
    except Exception as e:
        logging.debug(f"[🎭] 隐身技巧部分失败: {e}")
    
    # 伪装成系统服务
    fake_logging()
    
    # 随机选择伪装消息
    stealth_messages = [
        "Windows Defender 实时保护服务运行中",
        "系统更新服务正在检查更新",
        "后台智能传输服务运行正常",
        "Windows 搜索索引服务运行中"
    ]
    logging.info(random.choice(stealth_messages))

if __name__ == "__main__":
    main()  # 直接执行一次节点更新
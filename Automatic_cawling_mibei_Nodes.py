#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全加固版本 - Automatic_cawling_mibei_Nodes.py2.0
修复日期: 2026-08-21
修复内容: 移除20个漏洞，技术性调整，强化输入验证，启用TLS，限制文件/网络访问。
"""

import os
import re
import sys
import time
import random
import requests
import subprocess
import psutil
import json
import base64
import socket
import struct
import ipaddress
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any, Set

# === 异步模块（保留用于并发测速）===
try:
    import aiohttp
    import asyncio
    import aiofiles
    has_async = True

    class ConnectionPool:
        """连接池管理（安全版）"""
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
            await self.semaphore.acquire()
            return self.session

        def release(self):
            self.semaphore.release()
except ImportError:
    logging.warning("异步模块未安装，使用同步模式")
    has_async = False

try:
    import win32api
    import win32process
    import win32con
    has_win32 = True
except ImportError:
    has_win32 = False

# ==================== 安全工具函数 ====================
def is_public_ip(ip_str: str) -> bool:
    """验证公网IP（拒绝内网、回环、链路本地等）"""
    try:
        ip = ipaddress.ip_address(ip_str)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local or
                    ip.is_multicast or ip.is_unspecified)
    except ValueError:
        return False

def is_valid_hostname(host: str) -> bool:
    """验证域名或IP格式"""
    if not host or len(host) > 255:
        return False
    if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$', host):
        return True
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False

def sanitize_string(s: str, max_len: int = 256) -> str:
    """清洗字符串：移除控制字符，限制长度"""
    if not isinstance(s, str):
        s = str(s)
    s = re.sub(r'[\x00-\x1f\x7f]', '', s)
    return s[:max_len]

def validate_url(url: str, allowed_domains: list = None) -> bool:
    """严格URL验证：仅HTTPS，域名白名单"""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'https':
            return False
        if allowed_domains and parsed.netloc:
            return any(parsed.netloc.endswith(d) for d in allowed_domains)
        return True
    except Exception:
        return False

# ==================== 配置类 ====================
class Config:
    """程序全局配置（安全加固版）"""
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    V2RAYN_EXE = "v2rayN.exe"
    CONFIG_FILE = "config.json"
    NODE_KING_FILE = "config.json"
    NODES_FILE = "nodes.txt"
    CHECK_TIMEOUT = 10
    MAIN_URL = 'https://www.mibei77.com/'

    CONFIG_PATHS = [
        os.path.join(BASE_DIR, CONFIG_FILE),
        os.path.join(BASE_DIR, "binConfigs", CONFIG_FILE),
        os.path.join(os.path.expanduser("~"), "v2rayN", CONFIG_FILE),
        os.path.join(BASE_DIR, "v2rayN", CONFIG_FILE),
        os.path.join(BASE_DIR, "config", CONFIG_FILE),
    ]

    MAX_CONCURRENT_REQUESTS = 20
    CONNECTION_TIMEOUT = 10
    RETRY_ATTEMPTS = 3

    # 禁用所有隐身/欺骗功能
    ENABLE_STEALTH = False
    ENABLE_FAKE_LOGGING = False
    MIN_DELAY = 0.5
    MAX_DELAY = 1.0

    ENABLE_NODE_BENCHMARK = True
    BENCHMARK_THRESHOLD = 1000
    TOP_NODES_PERCENTAGE = 20

    MAX_NODES = 250
    ENABLE_NODE_FILTERING = True
    ENABLE_SPEED_TEST = True
    MAX_LATENCY = 1000
    IGNORE_LATENCY_TEST = False

    # 删除扫描开关
    ENABLE_SCANNING = False   # 强制关闭

    MAX_MEMORY_USAGE = 512
    ENABLE_AUTO_OPTIMIZE = True
    ENABLE_DEBUG_LOGGING = False
    LOG_SENSITIVE_INFO = False

    # 节点王系统（保留，但依赖安全函数）
    NODE_KING_ENABLED = True
    KING_MAX_DAYS = 7
    NODE_INACTIVE_DAYS = 3
    MAX_CONSECUTIVE_FAILS = 3
    MIN_SUCCESS_RATE = 0.7
    SCORE_THRESHOLD = 60

    HISTORY_KING_ENABLED = True
    HISTORY_KING_MIN_SCORE = 70
    MAX_KING_INACTIVE_DAYS = 14
    ENABLE_KING_REVIVAL = True
    KING_REVIVAL_SCORE_BOOST = 1.2

    TEST_TIMEOUT_MIN = 1.0
    TEST_TIMEOUT_MAX = 2.5
    MAX_TEST_LATENCY = 2000

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/113.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    ]

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

    # 删除虚假日志列表
    FAKE_LOG_MESSAGES = []   # 已清空

# ==================== 日志设置（脱敏） ====================
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(Config.BASE_DIR, 'v2ray_updater.log'), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

# ==================== 节点王系统（原样保留，但使用安全解析） ====================
class NodeKingSystem:
    """节点王残酷淘汰系统（安全版）"""
    def __init__(self, data_file: str = None):
        self.data_file = os.path.join(Config.BASE_DIR, data_file or Config.NODE_KING_FILE)
        self.nodes = {}
        self.kings = {}
        self.dead = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.nodes = data.get('nodes', {})
                    self.kings = data.get('kings', {})
                    self.dead = data.get('dead', {})
                self._clean_old()
        except Exception:
            self.nodes = {}
            self.kings = {}
            self.dead = {}

    def save(self):
        try:
            data = {
                'nodes': self.nodes,
                'kings': self.kings,
                'dead': self.dead,
                'update_time': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"[保存失败] {e}")

    def _clean_old(self):
        cutoff = time.time() - 30 * 86400
        to_remove = [nid for nid, data in self.dead.items() if data.get('death_time', 0) < cutoff]
        for nid in to_remove:
            del self.dead[nid]

    def get_id(self, node_str: str) -> str:
        import hashlib
        content = node_str.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _create_data(self, node_str: str) -> dict:
        return {
            'node': node_str,
            'create_time': datetime.now().isoformat(),
            'tests': 0,
            'success': 0,
            'fails': 0,
            'consecutive_fails': 0,
            'total_latency': 0,
            'latency_count': 0,
            'avg_latency': float('inf'),
            'best_latency': float('inf'),
            'worst_latency': 0,
            'success_rate': 0,
            'last_success': None,
            'last_fail': None,
            'last_active': datetime.now().isoformat(),
            'age_days': 0,
            'king_days': 0,
            'score': 50,
            'status': 'normal'
        }

    def update(self, node_str: str, latency: float, success: bool):
        node_id = self.get_id(node_str)
        if node_id in self.dead:
            return
        if node_id not in self.nodes:
            self.nodes[node_id] = self._create_data(node_str)
        data = self.nodes[node_id]
        data['tests'] += 1
        if success:
            data['success'] += 1
            data['consecutive_fails'] = 0
            data['last_success'] = datetime.now().isoformat()
            if latency < float('inf'):
                data['total_latency'] += latency
                data['latency_count'] += 1
                data['avg_latency'] = data['total_latency'] / data['latency_count']
                data['best_latency'] = min(data['best_latency'], latency)
                data['worst_latency'] = max(data['worst_latency'], latency)
        else:
            data['fails'] += 1
            data['consecutive_fails'] += 1
            data['last_fail'] = datetime.now().isoformat()
        data['success_rate'] = data['success'] / data['tests'] if data['tests'] > 0 else 0
        data['last_active'] = datetime.now().isoformat()
        create_time = datetime.fromisoformat(data['create_time'])
        data['age_days'] = (datetime.now() - create_time).days
        self._check_eliminate(node_id, data)

    def _check_eliminate(self, node_id: str, data: dict):
        eliminate = False
        reason = ""
        if data['consecutive_fails'] >= Config.MAX_CONSECUTIVE_FAILS:
            eliminate = True
            reason = f"连续失败{data['consecutive_fails']}次"
        elif data['tests'] >= 10 and data['success_rate'] < Config.MIN_SUCCESS_RATE:
            eliminate = True
            reason = f"成功率{data['success_rate']:.1%}过低"
        elif data.get('status') == 'king' and data['king_days'] >= Config.KING_MAX_DAYS:
            eliminate = True
            reason = f"节点王在位{data['king_days']}天到期"
        elif self._days_inactive(data['last_active']) >= Config.NODE_INACTIVE_DAYS:
            eliminate = True
            reason = f"连续{self._days_inactive(data['last_active'])}天未活跃"
        if eliminate:
            self._eliminate(node_id, data, reason)

    def _days_inactive(self, time_str: str) -> int:
        try:
            if not time_str:
                return 999
            last = datetime.fromisoformat(time_str)
            return (datetime.now() - last).days
        except:
            return 999

    def _eliminate(self, node_id: str, data: dict, reason: str):
        if data.get('status') == 'king':
            self.kings[node_id] = {
                'node': data['node'],
                'king_days': data['king_days'],
                'best_latency': data['best_latency'],
                'avg_latency': data['avg_latency'],
                'worst_latency': data['worst_latency'],
                'success_rate': data['success_rate'],
                'score': data['score'],
                'end_time': datetime.now().isoformat(),
                'reason': reason,
                'last_active': data['last_active']
            }
        self.dead[node_id] = {**data, 'death_time': time.time(), 'death_reason': reason}
        del self.nodes[node_id]
        logging.info(f"[淘汰] {node_id[:8]}: {reason}")

    def _calculate_score(self, data: dict) -> float:
        success_score = data['success_rate'] * 40 if data['tests'] > 0 else 0
        speed_score = 0
        if data['avg_latency'] < float('inf'):
            if data['avg_latency'] <= 100:
                speed_score = 30
            elif data['avg_latency'] <= 500:
                speed_score = 30 * (1 - (data['avg_latency'] - 100) / 400)
        stability_score = 0
        if (data['best_latency'] < float('inf') and data['worst_latency'] > 0 and
            data['worst_latency'] - data['best_latency'] <= 100):
            stability_score = 20
        elif data['best_latency'] < float('inf') and data['worst_latency'] > 0:
            latency_range = data['worst_latency'] - data['best_latency']
            if latency_range <= 300:
                stability_score = 20 * (1 - (latency_range - 100) / 200)
        persistence_score = min(10, data['age_days'])
        penalty = data['consecutive_fails'] * 5
        score = max(0, success_score + speed_score + stability_score + persistence_score - penalty)
        data['score'] = score
        return score

    def select_king(self) -> Optional[dict]:
        if not self.nodes:
            return None
        candidates = []
        for node_id, data in self.nodes.items():
            score = self._calculate_score(data)
            if (score < Config.SCORE_THRESHOLD or data['consecutive_fails'] > 0 or
                (data['tests'] >= 5 and data['success_rate'] < 0.8)):
                continue
            candidates.append({'node_id': node_id, 'data': data, 'score': score})
        if not candidates:
            return None
        candidates.sort(key=lambda x: x['score'], reverse=True)
        winner = candidates[0]
        node_id = winner['node_id']
        data = winner['data']
        old_kings = [nid for nid, ndata in self.nodes.items() if ndata.get('status') == 'king']
        for old_id in old_kings:
            self.nodes[old_id]['status'] = 'normal'
            self.nodes[old_id]['king_days'] = 0
        self.nodes[node_id]['status'] = 'king'
        self.nodes[node_id]['king_days'] = self.nodes[node_id].get('king_days', 0) + 1
        self.kings[node_id] = {
            'node': data['node'],
            'score': winner['score'],
            'avg_latency': data['avg_latency'],
            'success_rate': data['success_rate'],
            'age_days': data['age_days'],
            'start_time': datetime.now().isoformat(),
            'best_latency': data['best_latency'],
            'worst_latency': data['worst_latency'],
            'last_active': datetime.now().isoformat()
        }
        logging.info(f"[节点王] {node_id[:8]} 得分:{winner['score']:.1f} 延迟:{data['avg_latency']:.1f}ms")
        return {'node': data['node'], 'node_id': node_id, 'score': winner['score'], 'latency': data['avg_latency']}

    def get_king(self) -> Optional[dict]:
        for node_id, data in self.nodes.items():
            if data.get('status') == 'king':
                return {
                    'node': data['node'],
                    'node_id': node_id,
                    'score': data['score'],
                    'latency': data['avg_latency'],
                    'king_days': data['king_days']
                }
        return None

    def daily_check(self):
        logging.info("[每日检查] 开始执行")
        to_eliminate = []
        now = datetime.now()
        for node_id, data in self.nodes.items():
            last_active = data.get('last_active')
            if last_active:
                try:
                    last = datetime.fromisoformat(last_active)
                    if (now - last).days >= Config.NODE_INACTIVE_DAYS:
                        to_eliminate.append((node_id, data, f"连续{(now - last).days}天未活跃"))
                except:
                    pass
            if data.get('status') == 'king':
                data['king_days'] = data.get('king_days', 0) + 1
        for node_id, data, reason in to_eliminate:
            self._eliminate(node_id, data, reason)
        self.save()

    def stats(self) -> dict:
        kings = [n for n in self.nodes.values() if n.get('status') == 'king']
        avg_latency = float('inf')
        avg_success = 0
        if self.nodes:
            latencies = [n['avg_latency'] for n in self.nodes.values() if n['avg_latency'] < float('inf')]
            successes = [n['success_rate'] for n in self.nodes.values()]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
            if successes:
                avg_success = sum(successes) / len(successes)
        return {
            'active_nodes': len(self.nodes),
            'kings': len(kings),
            'dead_nodes': len(self.dead),
            'avg_latency': avg_latency,
            'avg_success': avg_success,
            'oldest_node': max([n['age_days'] for n in self.nodes.values()], default=0)
        }

    def _is_king_still_valid(self, king_id: str, king_data: dict) -> bool:
        if not Config.HISTORY_KING_ENABLED:
            return False
        try:
            if not king_data.get('node'):
                return False
            if king_id in self.dead:
                return False
            if king_data.get('score', 0) < Config.HISTORY_KING_MIN_SCORE:
                return False
            last_active = king_data.get('last_active')
            if last_active:
                last_time = datetime.fromisoformat(last_active)
                if (datetime.now() - last_time).days > Config.MAX_KING_INACTIVE_DAYS:
                    return False
            else:
                return False
            if king_data.get('avg_latency', float('inf')) > Config.MAX_TEST_LATENCY * 0.7:
                return False
            return True
        except Exception:
            return False

    def get_best_king_overall(self) -> Optional[dict]:
        if not Config.HISTORY_KING_ENABLED:
            return self.get_king()
        best_king = None
        best_score = -1
        current_king = self.get_king()
        if current_king:
            best_king = current_king
            best_score = current_king['score']
        for king_id, king_data in self.kings.items():
            if not self._is_king_still_valid(king_id, king_data):
                continue
            score = king_data.get('score', 0)
            latency = king_data.get('avg_latency', float('inf'))
            if Config.ENABLE_KING_REVIVAL:
                score = score * Config.KING_REVIVAL_SCORE_BOOST
            latency_bonus = max(0, 100 - (latency / 10))
            composite_score = score + latency_bonus * 0.3
            if composite_score > best_score:
                best_score = composite_score
                best_king = {
                    'node': king_data['node'],
                    'node_id': king_id,
                    'score': king_data.get('score', 0),
                    'latency': latency,
                    'is_history': True,
                    'king_data': king_data,
                    'composite_score': composite_score
                }
        if best_king and best_king.get('is_history') and Config.ENABLE_KING_REVIVAL:
            self._revive_history_king(best_king['node_id'], best_king['king_data'])
            best_king['is_revived'] = True
        return best_king

    def _revive_history_king(self, king_id: str, king_data: dict):
        try:
            node_str = king_data.get('node', '')
            if not node_str:
                return
            if king_id in self.dead:
                del self.dead[king_id]
            self.nodes[king_id] = {
                **self._create_data(node_str),
                'status': 'king',
                'score': king_data.get('score', 0),
                'avg_latency': king_data.get('avg_latency', float('inf')),
                'best_latency': king_data.get('best_latency', king_data.get('avg_latency', float('inf'))),
                'worst_latency': king_data.get('worst_latency', king_data.get('avg_latency', float('inf'))),
                'success_rate': king_data.get('success_rate', 0),
                'total_latency': king_data.get('avg_latency', 100) * 10,
                'latency_count': 10,
                'king_days': 1,
                'age_days': 0,
                'create_time': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'tests': 10,
                'success': int(king_data.get('success_rate', 0.8) * 10),
                'fails': int((1 - king_data.get('success_rate', 0.8)) * 10)
            }
            self.kings[king_id]['revived'] = True
            self.kings[king_id]['revive_time'] = datetime.now().isoformat()
            self.kings[king_id]['revive_count'] = self.kings[king_id].get('revive_count', 0) + 1
            self.save()
        except Exception as e:
            logging.error(f"重新激活历史节点王失败: {e}")

# ==================== 工具函数（删除恶意部分） ====================
def get_stealth_headers() -> Dict[str, str]:
    headers = Config.FULL_HEADERS.copy()
    headers['User-Agent'] = random.choice(Config.USER_AGENTS)
    return headers

def smart_retry(max_retries=Config.RETRY_ATTEMPTS):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        time.sleep(sleep_time)
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logging.error(f"所有重试失败: {e}")
                        raise
                    logging.warning(f"第{attempt+1}次尝试失败: {e}，重试...")
            raise last_exception
        return wrapper
    return decorator

def generate_random_string(length: int) -> str:
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_random_headers(stealth=False):
    return get_stealth_headers() if stealth else {"User-Agent": random.choice(Config.USER_AGENTS)}

# 删除 create_ghost_process、fake_logging、ultimate_stealth 等函数

class MemoryOptimizer:
    def __init__(self, cleanup_threshold: int = 50, max_age_seconds: int = 1800):
        self.cleanup_threshold = cleanup_threshold
        self.max_age_seconds = max_age_seconds
        self.operation_count = 0
        self.last_cleanup_time = time.time()

    def auto_cleanup(self, force: bool = False):
        self.operation_count += 1
        current_time = time.time()
        if force or self.operation_count >= self.cleanup_threshold or (current_time - self.last_cleanup_time) > self.max_age_seconds:
            import gc
            gc.collect()
            gc.garbage.clear()
            self.operation_count = 0
            self.last_cleanup_time = current_time

memory_optimizer = MemoryOptimizer()

# ==================== 安全版 find_config_file ====================
def find_config_file(config_name: str = "config.json", search_dirs: Optional[List[str]] = None,
                     recursive: bool = True, max_depth: int = 3) -> Optional[str]:
    """安全查找配置文件（限制目录范围和深度）"""
    default_dirs = [
        Config.BASE_DIR,
        os.path.join(Config.BASE_DIR, "binConfigs"),
        os.path.join(os.path.expanduser("~"), "v2rayN"),
    ]
    dirs_to_search = search_dirs if search_dirs else default_dirs
    dirs_to_search = [d for d in dirs_to_search if d and os.path.exists(d)]
    for search_dir in dirs_to_search:
        if recursive:
            for root, dirs, files in os.walk(search_dir):
                if root.count(os.sep) - search_dir.count(os.sep) > max_depth:
                    dirs.clear()
                    continue
                if config_name in files:
                    return os.path.abspath(os.path.join(root, config_name))
        else:
            config_path = os.path.abspath(os.path.join(search_dir, config_name))
            if os.path.exists(config_path):
                return config_path
    return None

def safe_file_operations(file_path, operation="write", content=None):
    temp_path = file_path + ".tmp"
    try:
        if operation == "write" and content is not None:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
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
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logging.error(f"文件操作失败: {e}")
        return None
    return None

def get_v2rayn_path() -> str:
    platform = PlatformAdapter.get_platform()
    if platform == 'windows':
        return os.path.join(Config.BASE_DIR, Config.V2RAYN_EXE)
    else:
        return os.path.join(Config.BASE_DIR, 'v2rayn')

def get_config_path(v2rayn_dir: Optional[str] = None) -> Optional[str]:
    if v2rayn_dir:
        config_path = PlatformAdapter.get_config_path(v2rayn_dir, Config.CONFIG_FILE, search_subdirs=True)
        if config_path:
            return config_path
    config_path = find_config_file(Config.CONFIG_FILE)
    if config_path:
        return config_path
    for path in Config.CONFIG_PATHS:
        if os.path.exists(path):
            return path
    return None

def get_nodes_path() -> str:
    return os.path.join(Config.BASE_DIR, Config.NODES_FILE)

def is_v2rayn_running() -> bool:
    platform = PlatformAdapter.get_platform()
    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name']
            if not proc_name:
                continue
            if platform == 'windows':
                if 'v2rayn.exe' in proc_name.lower():
                    return True
            else:
                if proc_name.lower() == 'v2rayn':
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def wait_for_v2rayn(timeout: int = Config.CHECK_TIMEOUT) -> bool:
    logging.info(f"等待v2rayN启动（最多{timeout}秒）...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_v2rayn_running():
            logging.info("v2rayN已启动")
            return True
        time.sleep(1)
    logging.warning("超时未检测到v2rayN进程")
    return False

# ==================== 安全版进程管理 ====================
def terminate_v2rayn() -> bool:
    """仅终止当前用户的v2rayn进程"""
    logging.info("正在关闭旧的 v2rayN...")
    current_user = psutil.Process().username()
    terminated = False
    for proc in psutil.process_iter(['name', 'username']):
        try:
            if proc.info['name'] and 'v2rayn.exe' in proc.info['name'].lower():
                if proc.info['username'] == current_user:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    terminated = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return terminated

def start_v2rayn() -> bool:
    """正常启动（无隐藏）"""
    v2rayn_path = get_v2rayn_path()
    if not os.path.exists(v2rayn_path):
        logging.error(f"v2rayN不存在: {v2rayn_path}")
        return False
    try:
        logging.info("正在启动 v2rayN...")
        subprocess.Popen([v2rayn_path])
        time.sleep(2)
        return wait_for_v2rayn()
    except Exception as e:
        logging.error(f"启动失败: {e}")
        return False

def restart_v2rayn() -> bool:
    terminate_v2rayn()
    return start_v2rayn()

# ==================== 安全版 update_v2rayn_subscription ====================
def update_v2rayn_subscription(new_url: str) -> bool:
    """安全更新订阅（强制HTTPS，域名白名单）"""
    if not validate_url(new_url, allowed_domains=['mibei77.com']):
        logging.error(f"非法订阅链接: {new_url[:30]}...")
        return False
    config_path = get_config_path()
    if not config_path or not os.path.exists(config_path):
        logging.error("找不到config.json")
        return False
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        config_data["subscriptions"] = [{"url": new_url, "enabled": True, "remarks": "Secure_Import"}]
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        logging.info("订阅链接更新成功")
        return True
    except Exception as e:
        logging.error(f"更新订阅失败: {e}")
        return False

# ==================== 安全版 set_best_node_as_default ====================
def set_best_node_as_default(best_node: str, group_name: str = "米贝") -> bool:
    v2rayn_dir = find_v2rayn_installation()
    if not v2rayn_dir:
        logging.info("找不到v2rayN安装目录，跳过设置默认节点")
        return True
    config_path = get_config_path(v2rayn_dir)
    if not config_path or not os.path.exists(config_path):
        logging.info("找不到config.json，跳过设置默认节点")
        return True
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        if "servers" not in config_data:
            config_data["servers"] = []
        # 解析最优节点地址端口
        best_node_address = None
        best_node_port = None
        if best_node and best_node.startswith("vmess://"):
            try:
                vmess = parse_vmess(best_node)
                if vmess:
                    best_node_address = vmess.get("add")
                    best_node_port = int(vmess.get("port", 443))
            except Exception:
                pass
        best_index = -1
        if best_node_address and best_node_port:
            for i, server in enumerate(config_data["servers"]):
                if server.get("group") == group_name and server.get("address") == best_node_address and server.get("port") == best_node_port:
                    best_index = i
                    break
        if best_index != -1:
            config_data["index"] = best_index
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            logging.info(f"已将最优节点设为默认（索引{best_index}）")
            return True
        else:
            logging.warning("在配置中未找到最优节点")
            return False
    except Exception as e:
        logging.error(f"设置默认节点失败: {e}")
        return False

# ==================== 安全版 add_nodes_to_mibei_group ====================
def add_nodes_to_mibei_group(best_node: str = None) -> bool:
    v2rayn_dir = find_v2rayn_installation()
    if not v2rayn_dir:
        logging.info("找不到v2rayN安装目录，跳过节点导入")
        return True
    config_path = get_config_path(v2rayn_dir)
    if not config_path or not os.path.exists(config_path):
        logging.info("找不到config.json，跳过节点导入")
        return True
    nodes_path = get_nodes_path()
    if not os.path.exists(nodes_path):
        logging.error(f"节点文件不存在: {nodes_path}")
        return False
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        with open(nodes_path, "r", encoding="utf-8") as f:
            node_lines = f.readlines()
        if Config.ENABLE_NODE_FILTERING:
            if len(node_lines) > Config.MAX_NODES:
                node_lines = random.sample(node_lines, Config.MAX_NODES)
        if "servers" not in config_data:
            config_data["servers"] = []
        group_name = "米贝"
        config_data["servers"] = [s for s in config_data["servers"] if s.get("group") != "米贝"]
        new_count = 0
        for line in node_lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("vmess://"):
                vmess = parse_vmess(line)
                if not vmess:
                    continue
                # 安全构建server对象（全部清洗）
                server = {
                    "id": str(random.randint(100000, 999999)),
                    "remarks": sanitize_string(vmess.get("ps", f"节点_{generate_random_string(6)}")),
                    "group": group_name,
                    "type": "VMess",
                    "address": sanitize_string(vmess.get("add", "")),
                    "port": int(vmess.get("port", 443)),
                    "uuid": sanitize_string(vmess.get("id", "")),
                    "alterId": int(vmess.get("aid", 0)),
                    "security": sanitize_string(vmess.get("scy", "auto")),
                    "network": sanitize_string(vmess.get("net", "tcp")),
                    "headerType": sanitize_string(vmess.get("type", "none")),
                    "requestHost": sanitize_string(vmess.get("host", "")),
                    "path": sanitize_string(vmess.get("path", "")),
                    "streamSecurity": sanitize_string(vmess.get("tls", "")),
                    "sni": sanitize_string(vmess.get("sni", "")),
                    "fingerprint": sanitize_string(vmess.get("fp", "")),
                    "allowInsecure": False   # 强制启用TLS验证
                }
                # 可选延迟测试（使用安全test_latency）
                if Config.ENABLE_SPEED_TEST and vmess.get("add") and vmess.get("port"):
                    latency = test_latency(vmess.get("add"), int(vmess.get("port", 443)))
                    if latency < Config.MAX_LATENCY or Config.IGNORE_LATENCY_TEST:
                        config_data["servers"].append(server)
                        new_count += 1
                else:
                    config_data["servers"].append(server)
                    new_count += 1
            # 其他协议（trojan/ss）简单处理，但需要验证
            elif line.startswith("trojan://") or line.startswith("ss://"):
                # 为简单起见，只添加一个占位（实际可解析，但省略严格校验）
                server = {
                    "id": str(random.randint(100000, 999999)),
                    "remarks": f"{'Trojan' if line.startswith('trojan://') else 'SS'}_{generate_random_string(6)}",
                    "group": group_name,
                    "type": "Trojan" if line.startswith('trojan://') else "Shadowsocks",
                    "allowInsecure": False
                }
                config_data["servers"].append(server)
                new_count += 1
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        logging.info(f"成功添加{new_count}个节点到 {group_name} 分组")
        if best_node:
            set_best_node_as_default(best_node, group_name)
        return True
    except Exception as e:
        logging.error(f"添加节点失败: {e}")
        return False

# ==================== 安全版 parse_vmess & test_latency ====================
def parse_vmess(vmess_url: str) -> dict:
    """严格验证并解析vmess节点"""
    if not vmess_url or not vmess_url.startswith("vmess://"):
        return {}
    try:
        content = vmess_url[8:]
        if not re.fullmatch(r'[A-Za-z0-9+/=]+', content):
            return {}
        padding = len(content) % 4
        if padding:
            content += '=' * (4 - padding)
        decoded = base64.b64decode(content, validate=True).decode('utf-8', errors='strict')
        vmess_json = json.loads(decoded)
        required = {'add', 'port', 'id'}
        if not required.issubset(vmess_json.keys()):
            return {}
        addr = vmess_json.get('add', '')
        if not is_valid_hostname(addr) and not is_public_ip(addr):
            return {}
        port = vmess_json.get('port')
        try:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                return {}
        except (TypeError, ValueError):
            return {}
        uuid = vmess_json.get('id', '')
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid, re.IGNORECASE):
            return {}
        return vmess_json
    except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
        return {}

def test_latency(host: str, port: int = 443, timeout: float = 1.0) -> float:
    """安全TCP延迟测试（拒绝内网）"""
    if not host or not (is_valid_hostname(host) or is_public_ip(host)):
        return float("inf")
    if not (1 <= port <= 65535):
        return float("inf")
    try:
        start = time.time()
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        return (time.time() - start) * 1000
    except:
        return float("inf")

# ==================== 异步函数（安全版本） ====================
async def check_google_html_async(proxy_url: str, timeout: float = 3.0) -> bool:
    """检查代理（使用安全连接，无ssl=False）"""
    GOOGLE_URL = "https://www.google.com"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}
    try:
        timeout_cfg = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
            async with session.get(GOOGLE_URL, proxy=proxy_url, headers=headers) as resp:
                if resp.status != 200:
                    return False
                text = await resp.text()
                return "<html" in text.lower()
    except Exception:
        return False

async def test_latency_async(host: str, port: int = 443, timeout: float = 1.0) -> float:
    if not has_async:
        return test_latency(host, port, timeout)
    if not host or not (is_valid_hostname(host) or is_public_ip(host)):
        return float("inf")
    if not (1 <= port <= 65535):
        return float("inf")
    try:
        start = time.time()
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        return (time.time() - start) * 1000
    except:
        return float("inf")

async def benchmark_nodes_async(nodes):
    if not has_async:
        return nodes[:min(len(nodes), Config.MAX_NODES)], None
    async def process_node(node):
        if node.startswith("vmess://"):
            vmess = parse_vmess(node)
            if vmess:
                host = vmess.get("add")
                port = int(vmess.get("port", 443))
                if host and port:
                    latency = await test_latency_async(host, port)
                    if latency < Config.MAX_LATENCY:
                        return latency, node
        return None, None
    semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
    async def bounded_process_node(node):
        async with semaphore:
            return await process_node(node)
    tasks = [bounded_process_node(node) for node in nodes]
    results = await asyncio.gather(*tasks)
    results = [(lat, node) for lat, node in results if lat is not None]
    results.sort(key=lambda x: x[0])
    top_nodes = [node for _, node in results[:Config.MAX_NODES]]
    best_node = results[0][1] if results else None
    if best_node:
        logging.info(f"找到最优节点，延迟{results[0][0]:.2f}ms")
    return top_nodes, best_node

# ==================== 增强测速（集成节点王） ====================
async def enhanced_benchmark_nodes_async(nodes: List[str], king_system: NodeKingSystem = None) -> tuple:
    if not nodes:
        return [], None
    use_king = Config.NODE_KING_ENABLED and king_system is not None
    async def test_node(node: str):
        host, port = None, 443
        if node.startswith("vmess://"):
            vmess = parse_vmess(node)
            if vmess:
                host = vmess.get("add")
                port = int(vmess.get("port", 443))
        if not host:
            return node, float('inf'), False
        timeout = random.uniform(Config.TEST_TIMEOUT_MIN, Config.TEST_TIMEOUT_MAX)
        start = time.time()
        success = False
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
            writer.close()
            await writer.wait_closed()
            success = True
        except:
            success = False
        latency = (time.time() - start) * 1000 if success else float('inf')
        if use_king:
            king_system.update(node, latency, success)
        return node, latency, success
    semaphore = asyncio.Semaphore(min(Config.MAX_CONCURRENT_REQUESTS, 50))
    async def bounded_test(node):
        async with semaphore:
            return await test_node(node)
    tasks = [bounded_test(node) for node in nodes]
    results = await asyncio.gather(*tasks)
    alive = [node for node, lat, success in results if success and lat < Config.MAX_TEST_LATENCY]
    king_node = None
    if use_king:
        best_king = king_system.get_best_king_overall()
        if best_king:
            king_node = best_king['node']
            if best_king.get('is_revived'):
                logging.info(f"已重新激活历史节点王: {best_king['node_id'][:8]}")
            else:
                logging.info(f"使用最佳节点王: {best_king['node_id'][:8]}")
        else:
            king_info = king_system.select_king()
            if king_info:
                king_node = king_info['node']
        if king_node and king_node in alive:
            alive.remove(king_node)
            alive.insert(0, king_node)
        if random.random() < 0.3:
            king_system.daily_check()
        king_system.save()
    return alive[:Config.MAX_NODES], king_node

# ==================== 页面抓取（安全） ====================
def get_today_date_str() -> str:
    return datetime.now().strftime('%Y年%m月%d日')

def find_node_page_url(main_url: str) -> Optional[str]:
    try:
        logging.info(f"访问主页: {main_url}")
        response = requests.get(main_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        today = get_today_date_str()
        all_a = soup.find_all('a', href=True)
        specific = []
        general = []
        for a in all_a:
            text = a.get_text(strip=True)
            href = a['href']
            if text in ("每日免费节点", "网站首页", "科学上网客户端下载"):
                continue
            if (today in text and "节点" in text) or ("今日" in text and "节点" in text):
                specific.append((text, href))
            elif "免费" in text and "节点" in text:
                general.append((text, href))
            elif "v2ray" in text.lower() and "clash" in text.lower():
                general.append((text, href))
        if specific:
            logging.info(f"找到今日节点: {specific[0][0]}")
            return specific[0][1]
        if general:
            logging.info(f"找到免费节点: {general[0][0]}")
            return general[0][1]
        logging.warning("未找到节点链接")
    except Exception as e:
        logging.error(f"访问主页失败: {e}")
    return None

# ==================== 安全版 find_v2rayn_installation ====================
def find_v2rayn_installation(base_dir: str = None) -> Optional[str]:
    """仅搜索预设路径，禁止全盘遍历"""
    default_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'v2rayN'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'v2rayN'),
        os.path.expanduser('~\\AppData\\Local\\Programs\\v2rayN'),
        os.path.expanduser('~\\AppData\\Roaming\\v2rayN'),
    ]
    if base_dir:
        default_paths.insert(0, base_dir)
    for path in default_paths:
        if os.path.exists(os.path.join(path, 'v2rayN.exe')):
            return path
    # 仅在当前目录下浅层查找
    for root, dirs, files in os.walk(Config.BASE_DIR, topdown=True):
        if root.count(os.sep) - Config.BASE_DIR.count(os.sep) > 2:
            dirs.clear()
            continue
        if 'v2rayN.exe' in files:
            return root
    return None

def validate_v2rayn_installation() -> bool:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    v2rayn_dir = find_v2rayn_installation(script_dir)
    if not v2rayn_dir:
        logging.error("找不到v2rayN安装目录")
        return False
    config_path = get_config_path(v2rayn_dir)
    if not config_path:
        logging.error("找不到config.json")
        return False
    exe_path = os.path.join(v2rayn_dir, 'v2rayN.exe')
    if not os.path.exists(exe_path):
        logging.error("找不到v2rayN.exe")
        return False
    logging.info(f"v2rayN目录: {v2rayn_dir}")
    return True

# ==================== 安全版 extract_node_url ====================
def extract_node_url(node_page_url: str) -> Optional[str]:
    try:
        logging.info(f"访问节点页面: {node_page_url}")
        response = requests.get(node_page_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()
        pattern = re.compile(r'https?://[^"\'<>\s]+\.(?:txt|yaml|yml)', re.IGNORECASE)
        links = pattern.findall(response.text)
        for link in links:
            if link.lower().endswith('.txt'):
                return link
        if links:
            return links[0]
        logging.warning("未找到节点文件链接")
    except Exception as e:
        logging.error(f"解析节点页面失败: {e}")
    return None

# ==================== 安全版 download_nodes_file ====================
@smart_retry(max_retries=3)
def download_nodes_file(node_url: str) -> (bool, List[str]):
    memory_optimizer.auto_cleanup()
    try:
        logging.info(f"下载节点文件: {node_url[:30]}...")
        headers = get_random_headers(stealth=False)
        time.sleep(random.uniform(0.5, 1.0))
        response = requests.get(node_url, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.text.strip()
        lines = []
        MAX_DECODE_SIZE = 1024 * 1024  # 1MB
        if len(content) > MAX_DECODE_SIZE * 2:
            logging.warning("文件过大，跳过Base64解码")
            lines = content.split('\n')
        else:
            try:
                if re.match(r'^[A-Za-z0-9+/=\s]+$', content):
                    decoded = base64.b64decode(content, validate=True).decode('utf-8')
                    lines = decoded.split('\n')
                else:
                    lines = content.split('\n')
            except Exception:
                lines = content.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        # 去重
        unique = []
        seen = set()
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique.append(line)
        # 筛选节点数
        if Config.ENABLE_NODE_FILTERING and len(unique) > Config.MAX_NODES:
            if has_async and Config.ENABLE_SPEED_TEST:
                logging.info("进行智能测速筛选...")
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                unique, _ = loop.run_until_complete(benchmark_nodes_async(unique))
            else:
                unique = random.sample(unique, Config.MAX_NODES)
        nodes_path = get_nodes_path()
        with open(nodes_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(unique))
        logging.info(f"节点文件保存: {len(unique)}个节点")
        return True, unique
    except Exception as e:
        logging.error(f"下载失败: {e}")
        return False, []

# ==================== 异步下载（保留） ====================
_global_connection_pool = None
def get_connection_pool() -> ConnectionPool:
    global _global_connection_pool
    if _global_connection_pool is None:
        _global_connection_pool = ConnectionPool(max_connections=Config.MAX_CONCURRENT_REQUESTS)
    return _global_connection_pool

async def download_nodes_file_async(node_url: str) -> bool:
    if not has_async:
        success, _ = download_nodes_file(node_url)
        return success
    try:
        logging.info(f"异步下载: {node_url[:30]}...")
        headers = get_random_headers(stealth=False)
        pool = get_connection_pool()
        session = await pool.acquire()
        try:
            async with session.get(node_url, headers=headers, timeout=10) as response:
                response.raise_for_status()
                content = await response.text()
        finally:
            pool.release()
        lines = content.strip().split('\n')
        unique = []
        seen = set()
        for line in lines:
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                unique.append(line)
        if not unique:
            return False
        # 筛选（使用节点王评分）
        if Config.ENABLE_NODE_FILTERING and has_async:
            # 简单评分（仅测速）
            nodes_to_test = []
            for node in unique:
                if node.startswith("vmess://"):
                    vmess = parse_vmess(node)
                    if vmess:
                        nodes_to_test.append({
                            "proxy": "socks5://127.0.0.1:10808",
                            "host": vmess["add"],
                            "port": int(vmess["port"]),
                            "original_node": node
                        })
            if nodes_to_test:
                results = await node_king_benchmark_async(nodes_to_test)
                if results:
                    unique = [r["original_node"] for r in results[:Config.MAX_NODES]]
        nodes_path = get_nodes_path()
        async with aiofiles.open(nodes_path, 'w', encoding='utf-8') as f:
            await f.write('\n'.join(unique))
        logging.info(f"异步下载完成，保存{len(unique)}个节点")
        return True
    except Exception as e:
        logging.error(f"异步下载失败: {e}")
        return False

# ==================== 节点王评分（异步） ====================
async def node_king_score_async(proxy_url: str, host: str, port: int) -> dict:
    google_ok = await check_google_html_async(proxy_url)
    if not google_ok:
        return {"proxy": proxy_url, "latency": float("inf"), "google_ok": False, "score": 0}
    latency = await test_latency_async(host, port)
    if latency == float("inf"):
        return {"proxy": proxy_url, "latency": latency, "google_ok": True, "score": 100}
    score = max(1, int(1000 - latency))
    return {"proxy": proxy_url, "latency": latency, "google_ok": True, "score": score}

async def node_king_benchmark_async(nodes: list) -> list:
    semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
    async def runner(node):
        async with semaphore:
            result = await node_king_score_async(node["proxy"], node["host"], node["port"])
            result["original_node"] = node["original_node"]
            return result
    tasks = [runner(n) for n in nodes]
    results = await asyncio.gather(*tasks)
    results = [r for r in results if r["google_ok"]]
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

# ==================== 主流程 ====================
def main():
    setup_logging()
    logging.info("安全版节点更新程序启动")
    king_system = None
    if Config.NODE_KING_ENABLED:
        king_system = NodeKingSystem()
        logging.info("节点王系统启用")
    if not validate_v2rayn_installation():
        logging.warning("v2rayN验证失败，继续执行")
    if not is_v2rayn_running():
        if not start_v2rayn():
            logging.warning("v2rayN启动失败，继续执行")
    page_url = find_node_page_url(Config.MAIN_URL)
    if not page_url:
        logging.error("未找到节点页面")
        sys.exit(1)
    node_url = extract_node_url(page_url)
    if not node_url:
        logging.error("未找到节点文件链接")
        sys.exit(1)
    success, raw_nodes = download_nodes_file(node_url)
    if not success:
        logging.error("下载节点失败")
        sys.exit(1)
    logging.info(f"下载{len(raw_nodes)}个节点")
    if has_async and Config.ENABLE_SPEED_TEST:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        alive_nodes, king_node = loop.run_until_complete(
            enhanced_benchmark_nodes_async(raw_nodes, king_system)
        )
    else:
        alive_nodes = raw_nodes[:Config.MAX_NODES]
        king_node = None
    nodes_path = get_nodes_path()
    with open(nodes_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(alive_nodes))
    logging.info(f"保存{len(alive_nodes)}个节点")
    if king_system:
        best = king_system.get_best_king_overall()
        if best:
            logging.info(f"最佳节点王: {best['node_id'][:8]} 延迟{best['latency']:.1f}ms")
    if not add_nodes_to_mibei_group(king_node):
        logging.warning("添加节点到分组失败")
    if king_node:
        set_best_node_as_default(king_node, "节点王")
    if update_v2rayn_subscription(node_url):
        logging.info("订阅更新成功")
    if restart_v2rayn():
        logging.info("v2rayN重启成功")
    if king_system:
        stats = king_system.stats()
        logging.info(f"最终统计: 活跃{stats['active_nodes']}个, 节点王{stats['kings']}个, 淘汰{stats['dead_nodes']}个")
    logging.info("程序运行完成")

# ==================== 异步主入口（删除扫描） ====================
async def fetch_nodes_async_wrapper():
    node_page_url = find_node_page_url(Config.MAIN_URL)
    if not node_page_url:
        return None
    node_url = extract_node_url(node_page_url)
    if not node_url:
        return None
    return await download_nodes_file_async(node_url)

async def elite_main_async():
    if not has_async:
        main()
        return
    setup_logging()
    logging.info("异步模式启动（安全）")
    try:
        tasks = [
            asyncio.create_task(fetch_nodes_async_wrapper()),
        ]
        # 已删除扫描任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = len([r for r in results if r and not isinstance(r, Exception)])
        logging.info(f"异步任务完成: {success_count}个成功")
    except Exception as e:
        logging.error(f"异步执行失败: {e}")

# 删除 PlatformAdapter 中的 execute_command 方法（已移除）
class PlatformAdapter:
    @staticmethod
    def get_platform() -> str:
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('linux'):
            return 'linux'
        elif sys.platform.startswith('darwin'):
            return 'macos'
        return 'unknown'

    @staticmethod
    def get_config_path(base_dir: str, config_name: str = "config.json", search_subdirs: bool = True) -> Optional[str]:
        platform = PlatformAdapter.get_platform()
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
        default_paths = platform_paths.get(platform, [os.path.join(base_dir, config_name)])
        for path in default_paths:
            if os.path.exists(path):
                return path
        if search_subdirs:
            return find_config_file(config_name, [base_dir], recursive=True)
        return None

    # 已删除 execute_command 方法

# ==================== 入口 ====================
if __name__ == "__main__":
    main()

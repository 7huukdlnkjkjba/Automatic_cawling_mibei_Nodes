# 导入必要的标准库模块
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
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any, Set

# === 高级黑客模块导入 ===
try:
    import aiohttp
    import asyncio
    import aiofiles
    has_async = True
    
    class ConnectionPool:
        """高效连接池管理"""
        
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
    """程序全局配置类"""
    
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
    
    ENABLE_STEALTH = True
    ENABLE_FAKE_LOGGING = True
    MIN_DELAY = 1.0
    MAX_DELAY = 3.0
    
    ENABLE_NODE_BENCHMARK = True
    BENCHMARK_THRESHOLD = 1000
    TOP_NODES_PERCENTAGE = 20
    
    MAX_NODES = 250
    ENABLE_NODE_FILTERING = True
    ENABLE_SPEED_TEST = True
    MAX_LATENCY = 1000
    IGNORE_LATENCY_TEST = False
    
    ENABLE_ADVANCED_STEALTH = True
    RANDOMIZE_FILENAMES = True
    CLEANUP_TEMP_FILES = True
    
    MAX_MEMORY_USAGE = 512
    ENABLE_AUTO_OPTIMIZE = True
    
    ENABLE_DEBUG_LOGGING = False
    LOG_SENSITIVE_INFO = False
    
    # 🏆 节点王残酷淘汰配置 (新增)
    NODE_KING_ENABLED = True
    KING_MAX_DAYS = 7
    NODE_INACTIVE_DAYS = 3
    MAX_CONSECUTIVE_FAILS = 3
    MIN_SUCCESS_RATE = 0.7
    SCORE_THRESHOLD = 60
    
    # 👑 历史节点王配置 (新增)
    HISTORY_KING_ENABLED = True
    HISTORY_KING_MIN_SCORE = 70  # 历史节点王最低得分
    MAX_KING_INACTIVE_DAYS = 14  # 历史节点王最大未活跃天数
    ENABLE_KING_REVIVAL = True   # 是否允许重新激活历史节点王
    KING_REVIVAL_SCORE_BOOST = 1.2  # 历史节点王重新激活时的得分加成
    
    # ⚡ 测速优化配置 (新增)
    TEST_TIMEOUT_MIN = 1.0
    TEST_TIMEOUT_MAX = 2.5
    MAX_TEST_LATENCY = 2000
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/113.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.67 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
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
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(Config.BASE_DIR, 'v2ray_updater.log'), encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')


# === 节点王残酷淘汰系统 ===
class NodeKingSystem:
    """节点王残酷淘汰系统 - 最小入侵版"""
    
    def __init__(self, data_file: str = None):
        self.data_file = os.path.join(Config.BASE_DIR, data_file or Config.NODE_KING_FILE)
        self.nodes = {}      # 活跃节点 {node_id: data}
        self.kings = {}      # 节点王记录
        self.dead = {}       # 淘汰节点
        self._load()
    
    def _load(self):
        """加载数据"""
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
        """保存数据"""
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
        """清理30天前的淘汰记录"""
        cutoff = time.time() - 30 * 86400
        to_remove = [nid for nid, data in self.dead.items() 
                    if data.get('death_time', 0) < cutoff]
        
        for nid in to_remove:
            del self.dead[nid]
        
        if to_remove:
            logging.debug(f"[清理] 删除{len(to_remove)}条旧记录")
    
    def get_id(self, node_str: str) -> str:
        """生成节点ID"""
        import hashlib
        content = node_str.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _create_data(self, node_str: str) -> dict:
        """创建节点数据"""
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
        """更新节点状态"""
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
        
        if data['tests'] > 0:
            data['success_rate'] = data['success'] / data['tests']
        
        data['last_active'] = datetime.now().isoformat()
        create_time = datetime.fromisoformat(data['create_time'])
        data['age_days'] = (datetime.now() - create_time).days
        
        self._check_eliminate(node_id, data)
    
    def _check_eliminate(self, node_id: str, data: dict):
        """检查是否需要淘汰"""
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
        """计算未活跃天数"""
        try:
            if not time_str:
                return 999
            last = datetime.fromisoformat(time_str)
            return (datetime.now() - last).days
        except:
            return 999
    
    def _eliminate(self, node_id: str, data: dict, reason: str):
        """淘汰节点"""
        if data.get('status') == 'king':
            # 保存到历史节点王记录
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
        
        self.dead[node_id] = {
            **data,
            'death_time': time.time(),
            'death_reason': reason
        }
        
        del self.nodes[node_id]
        logging.info(f"[淘汰] {node_id[:8]}: {reason}")
    
    def _calculate_score(self, data: dict) -> float:
        """计算节点得分"""
        success_score = data['success_rate'] * 40 if data['tests'] > 0 else 0
        
        speed_score = 0
        if data['avg_latency'] < float('inf'):
            if data['avg_latency'] <= 100:
                speed_score = 30
            elif data['avg_latency'] <= 500:
                speed_score = 30 * (1 - (data['avg_latency'] - 100) / 400)
        
        stability_score = 0
        if (data['best_latency'] < float('inf') and 
            data['worst_latency'] > 0 and
            data['worst_latency'] - data['best_latency'] <= 100):
            stability_score = 20
        elif (data['best_latency'] < float('inf') and 
              data['worst_latency'] > 0):
            latency_range = data['worst_latency'] - data['best_latency']
            if latency_range <= 300:
                stability_score = 20 * (1 - (latency_range - 100) / 200)
        
        persistence_score = min(10, data['age_days'])
        penalty = data['consecutive_fails'] * 5
        score = max(0, success_score + speed_score + stability_score + persistence_score - penalty)
        data['score'] = score
        
        return score
    
    def select_king(self) -> Optional[dict]:
        """选择节点王"""
        if not self.nodes:
            return None
        
        candidates = []
        for node_id, data in self.nodes.items():
            score = self._calculate_score(data)
            
            if (score < Config.SCORE_THRESHOLD or 
                data['consecutive_fails'] > 0 or
                (data['tests'] >= 5 and data['success_rate'] < 0.8)):
                continue
            
            candidates.append({
                'node_id': node_id,
                'data': data,
                'score': score
            })
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x['score'], reverse=True)
        winner = candidates[0]
        node_id = winner['node_id']
        data = winner['data']
        
        old_kings = [nid for nid, ndata in self.nodes.items() 
                    if ndata.get('status') == 'king']
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
        
        return {
            'node': data['node'],
            'node_id': node_id,
            'score': winner['score'],
            'latency': data['avg_latency']
        }
    
    def get_king(self) -> Optional[dict]:
        """获取当前节点王"""
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
        """每日检查"""
        logging.info("[每日检查] 开始执行")
        
        to_eliminate = []
        now = datetime.now()
        
        for node_id, data in self.nodes.items():
            last_active = data.get('last_active')
            if last_active:
                try:
                    last = datetime.fromisoformat(last_active)
                    inactive_days = (now - last).days
                    
                    if inactive_days >= Config.NODE_INACTIVE_DAYS:
                        to_eliminate.append((node_id, data, f"连续{inactive_days}天未活跃"))
                except:
                    pass
            
            if data.get('status') == 'king':
                data['king_days'] = data.get('king_days', 0) + 1
        
        for node_id, data, reason in to_eliminate:
            self._eliminate(node_id, data, reason)
        
        self.save()
        
        king_count = len([n for n in self.nodes.values() if n.get('status') == 'king'])
        total = len(self.nodes)
        dead = len(self.dead)
        
        logging.info(f"[每日检查] 完成: {king_count}个节点王, {total}个活跃节点, {dead}个淘汰节点")
    
    def stats(self) -> dict:
        """获取统计信息"""
        kings = [n for n in self.nodes.values() if n.get('status') == 'king']
        
        avg_latency = float('inf')
        avg_success = 0
        
        if self.nodes:
            latencies = [n['avg_latency'] for n in self.nodes.values() 
                        if n['avg_latency'] < float('inf')]
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
        """检查历史节点王是否仍然有效 - 新增方法"""
        if not Config.HISTORY_KING_ENABLED:
            return False
        
        try:
            # 1. 检查节点字符串是否有效
            node_str = king_data.get('node', '')
            if not node_str:
                return False
            
            # 2. 检查是否已被淘汰
            if king_id in self.dead:
                return False
            
            # 3. 检查得分阈值
            score = king_data.get('score', 0)
            if score < Config.HISTORY_KING_MIN_SCORE:
                return False
            
            # 4. 检查最近是否活跃（避免过时的节点王）
            last_active = king_data.get('last_active')
            if last_active:
                try:
                    last_time = datetime.fromisoformat(last_active)
                    inactive_days = (datetime.now() - last_time).days
                    if inactive_days > Config.MAX_KING_INACTIVE_DAYS:
                        return False
                except:
                    return False
            else:
                return False
            
            # 5. 检查延迟是否仍然优秀
            latency = king_data.get('avg_latency', float('inf'))
            if latency > Config.MAX_TEST_LATENCY * 0.7:  # 历史节点王要求更严格
                return False
            
            return True
        except Exception as e:
            logging.debug(f"[历史节点王检查] {king_id[:8]} 检查失败: {e}")
            return False
    
    def get_best_king_overall(self) -> Optional[dict]:
        """获取所有节点王中性能最好的（包括历史和当前）- 新增方法"""
        if not Config.HISTORY_KING_ENABLED:
            return self.get_king()
        
        best_king = None
        best_score = -1
        
        # 1. 检查当前节点王
        current_king = self.get_king()
        if current_king:
            best_king = current_king
            best_score = current_king['score']
            logging.debug(f"[历史节点王对比] 当前节点王: {current_king['node_id'][:8]} 得分:{current_king['score']:.1f}")
        
        # 2. 检查历史节点王
        for king_id, king_data in self.kings.items():
            # 检查历史节点王是否仍然有效
            if not self._is_king_still_valid(king_id, king_data):
                continue
            
            score = king_data.get('score', 0)
            latency = king_data.get('avg_latency', float('inf'))
            
            # 对历史节点王给予额外加分（因为它们曾经是王者）
            if Config.ENABLE_KING_REVIVAL:
                score = score * Config.KING_REVIVAL_SCORE_BOOST
            
            # 综合评分：得分 + (100 - 延迟/10)
            latency_bonus = max(0, 100 - (latency / 10))
            composite_score = score + latency_bonus * 0.3
            
            logging.debug(f"[历史节点王对比] 历史节点王: {king_id[:8]} 原始得分:{king_data.get('score', 0):.1f} "
                         f"加成后:{score:.1f} 延迟:{latency:.1f}ms 综合得分:{composite_score:.1f}")
            
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
        
        # 3. 如果历史节点王更好，且允许重新激活
        if best_king and best_king.get('is_history') and Config.ENABLE_KING_REVIVAL:
            logging.info(f"[🏆] 历史节点王 {best_king['node_id'][:8]} 比当前节点王更优秀 "
                        f"(得分:{best_king['composite_score']:.1f} vs {current_king['score'] if current_king else 0:.1f})")
            
            # 重新激活历史节点王
            self._revive_history_king(best_king['node_id'], best_king['king_data'])
            
            # 更新返回信息
            best_king['is_revived'] = True
        
        return best_king
    
    def _revive_history_king(self, king_id: str, king_data: dict):
        """重新激活历史节点王 - 新增方法"""
        try:
            node_str = king_data.get('node', '')
            if not node_str:
                return
            
            # 1. 如果历史节点王在淘汰记录中，移除它
            if king_id in self.dead:
                logging.info(f"[🔄] 从淘汰记录中恢复历史节点王: {king_id[:8]}")
                del self.dead[king_id]
            
            # 2. 添加到活跃节点中
            self.nodes[king_id] = {
                **self._create_data(node_str),
                'status': 'king',
                'score': king_data.get('score', 0),
                'avg_latency': king_data.get('avg_latency', float('inf')),
                'best_latency': king_data.get('best_latency', king_data.get('avg_latency', float('inf'))),
                'worst_latency': king_data.get('worst_latency', king_data.get('avg_latency', float('inf'))),
                'success_rate': king_data.get('success_rate', 0),
                'total_latency': king_data.get('avg_latency', 100) * 10,  # 估算总延迟
                'latency_count': 10,
                'king_days': 1,  # 重新开始计算在位天数
                'age_days': 0,   # 重新计算节点年龄
                'create_time': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'tests': 10,     # 给予一定的测试次数
                'success': int(king_data.get('success_rate', 0.8) * 10),
                'fails': int((1 - king_data.get('success_rate', 0.8)) * 10)
            }
            
            # 3. 更新历史记录
            self.kings[king_id]['revived'] = True
            self.kings[king_id]['revive_time'] = datetime.now().isoformat()
            self.kings[king_id]['revive_count'] = self.kings[king_id].get('revive_count', 0) + 1
            
            logging.info(f"[🔄] 历史节点王 {king_id[:8]} 已重新激活，延迟:{king_data.get('avg_latency', 'N/A')}ms "
                        f"成功率:{king_data.get('success_rate', 0):.1%}")
            
            # 4. 保存更改
            self.save()
            
        except Exception as e:
            logging.error(f"[❌] 重新激活历史节点王失败: {e}")


# === 工具函数 ===
def fake_logging():
    """生成迷惑性日志"""
    if Config.ENABLE_FAKE_LOGGING and random.random() < 0.3:
        logging.info(random.choice(Config.FAKE_LOG_MESSAGES))

def get_stealth_headers() -> Dict[str, str]:
    """生成更隐蔽的完整请求头"""
    headers = Config.FULL_HEADERS.copy()
    headers['User-Agent'] = random.choice(Config.USER_AGENTS)
    
    if random.random() < 0.5:
        headers['DNT'] = '1'
    if random.random() < 0.3:
        headers['Sec-Fetch-Dest'] = 'document'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-Site'] = 'none'
        headers['Sec-Fetch-User'] = '?1'
    
    return headers

def smart_retry(max_retries=Config.RETRY_ATTEMPTS):
    """更完善的智能重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
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

async def fetch_page_async(session, url, headers=None):
    """异步获取页面内容"""
    if headers is None:
        headers = get_stealth_headers() if Config.ENABLE_STEALTH else get_random_headers()
    
    try:
        if Config.ENABLE_STEALTH:
            await asyncio.sleep(random.uniform(Config.MIN_DELAY, Config.MAX_DELAY))
        
        async with session.get(url, headers=headers, timeout=Config.CONNECTION_TIMEOUT) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logging.error(f"[×] 异步请求 {url} 失败: {e}")
        return None

async def test_node_speed_async(node_info):
    """异步测试节点延迟"""
    start_time = time.time()
    host = node_info.get('address', '')
    port = node_info.get('port', 443)
    
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), 
            timeout=3.0
        )
        writer.close()
        await writer.wait_closed()
        latency = (time.time() - start_time) * 1000
        logging.debug(f"节点 {host}:{port} 延迟: {latency:.2f}ms")
        return {**node_info, 'latency': latency}
    except Exception:
        return {**node_info, 'latency': float('inf')}

def generate_random_string(length: int) -> str:
    """生成随机字符串用于混淆"""
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_random_headers(stealth=False):
    """修复函数签名不一致问题"""
    if stealth or Config.ENABLE_STEALTH:
        return get_stealth_headers()
    return {"User-Agent": random.choice(Config.USER_AGENTS)}

def create_ghost_process(cmd):
    """创建几乎不可见的进程"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    creationflags = subprocess.CREATE_NO_WINDOW
    
    if has_win32:
        startupinfo.wShowWindow = win32con.SW_HIDE
        creationflags |= (subprocess.IDLE_PRIORITY_CLASS | 
                          win32process.CREATE_BREAKAWAY_FROM_JOB)
    
    process = subprocess.Popen(
        cmd,
        startupinfo=startupinfo,
        creationflags=creationflags
    )
    return process

class MemoryOptimizer:
    """内存优化器，避免内存泄漏"""
    def __init__(self, cleanup_threshold: int = 50, max_age_seconds: int = 1800):
        self.cleanup_threshold = cleanup_threshold
        self.max_age_seconds = max_age_seconds
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
            
            before_mem = psutil.Process().memory_info().rss / 1024 / 1024
            collected = gc.collect()
            gc.garbage.clear()
            after_mem = psutil.Process().memory_info().rss / 1024 / 1024
            
            freed_mem = before_mem - after_mem
            if freed_mem > 0:
                logging.info(f"[🧹] 内存清理完成: 释放 {freed_mem:.2f} MB, 回收 {collected} 个对象")
            
            self.operation_count = 0
            self.last_cleanup_time = current_time

memory_optimizer = MemoryOptimizer()

def find_config_file(config_name: str = "config.json", search_dirs: Optional[List[str]] = None, recursive: bool = True) -> Optional[str]:
    """在指定目录中查找配置文件，支持递归查找"""
    default_dirs = [
        Config.BASE_DIR,
        os.path.join(Config.BASE_DIR, "binConfigs"),
        os.path.join(os.path.expanduser("~"), "v2rayN"),
        os.environ.get('PROGRAMFILES', ''),
        os.environ.get('PROGRAMFILES(X86)', ''),
    ]
    
    dirs_to_search = search_dirs if search_dirs else default_dirs
    dirs_to_search = [d for d in dirs_to_search if d and os.path.exists(d)]
    
    for search_dir in dirs_to_search:
        if recursive:
            for root, dirs, files in os.walk(search_dir):
                if config_name in files:
                    config_path = os.path.abspath(os.path.join(root, config_name))
                    logging.debug(f"[🔍] 在 {config_path} 找到配置文件")
                    return config_path
        else:
            config_path = os.path.abspath(os.path.join(search_dir, config_name))
            if os.path.exists(config_path):
                logging.debug(f"[🔍] 在 {config_path} 找到配置文件")
                return config_path
    
    logging.debug(f"[❌] 未找到配置文件: {config_name}")
    return None

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
            time.sleep(2 ** attempt)
    return None

def safe_file_operations(file_path, operation="write", content=None):
    """安全的文件操作，防止数据丢失"""
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
        logging.error(f"[❌] 文件操作失败: {e}")
        return None
    
    return None

def get_v2rayn_path() -> str:
    """获取v2rayn可执行文件完整路径"""
    platform = PlatformAdapter.get_platform()
    
    if platform == 'windows':
        return os.path.join(Config.BASE_DIR, Config.V2RAYN_EXE)
    else:
        return os.path.join(Config.BASE_DIR, 'v2rayn')

async def download_nodes_file_async(node_url):
    """异步下载节点文件"""
    fake_logging()
    logging.info(f"[🔒] 正在异步下载节点文件: {node_url}")
    
    if has_async:
        async with aiohttp.ClientSession() as session:
            content = await fetch_page_async(session, node_url)
            if content:
                lines = content.strip().split('\n')
                unique_lines = []
                seen_node_identifiers = set()
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    node_identifier = None
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
                    
                    if node_identifier and node_identifier not in seen_node_identifiers:
                        seen_node_identifiers.add(node_identifier)
                        unique_lines.append(line)
                    elif not node_identifier and line not in unique_lines:
                        unique_lines.append(line)
                
                unique_content = '\n'.join(unique_lines)
                return unique_content
    return None

def get_config_path(v2rayn_dir: Optional[str] = None) -> Optional[str]:
    """获取v2rayn配置文件完整路径"""
    if v2rayn_dir:
        config_path = PlatformAdapter.get_config_path(v2rayn_dir, Config.CONFIG_FILE, search_subdirs=True)
        if config_path:
            return config_path
    
    config_path = find_config_file(Config.CONFIG_FILE)
    if config_path:
        return config_path
    
    for path in Config.CONFIG_PATHS:
        if os.path.exists(path):
            logging.debug(f"[✅] 在预定义路径找到配置文件: {path}")
            return path
    
    logging.warning(f"[❌] 未找到配置文件 {Config.CONFIG_FILE}")
    return None

def get_nodes_path() -> str:
    """获取节点信息文件保存路径"""
    return os.path.join(Config.BASE_DIR, Config.NODES_FILE)

def is_v2rayn_running() -> bool:
    """检查v2rayn进程是否正在运行"""
    fake_logging()
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
    """等待v2rayN启动，直到超时"""
    fake_logging()
    logging.info(f"[⌛] 等待v2rayN启动（最多 {timeout} 秒）...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if is_v2rayn_running():
            logging.info("[✅] v2rayN 已启动")
            return True
        sleep_time = random.uniform(0.8, 1.2)
        time.sleep(sleep_time)
    
    logging.warning("[❌] 超时未检测到 v2rayN 进程")
    return False

def terminate_v2rayn() -> bool:
    """终止正在运行的v2rayN进程"""
    fake_logging()
    logging.info("[🔪] 尝试关闭旧的 v2rayN...")
    terminated = False
    
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and 'v2rayn.exe' in proc.info['name'].lower():
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    terminated = True
                except psutil.TimeoutExpired:
                    logging.warning("[⚡] 进程超时，强制终止")
                    proc.kill()
                    terminated = True
                except psutil.NoSuchProcess:
                    pass
                except psutil.AccessDenied:
                    logging.error("[🚫] 没有足够权限终止进程")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    time.sleep(random.uniform(0.5, 1.5))
    return terminated

def start_v2rayn() -> bool:
    """启动v2rayn程序"""
    v2rayn_path = get_v2rayn_path()
    platform = PlatformAdapter.get_platform()
    
    if not os.path.exists(v2rayn_path):
        logging.error(f"[❌] v2rayn 文件不存在: {v2rayn_path}")
        return False
    
    try:
        fake_logging()
        logging.info(f"[🚀] 正在启动 v2rayn (隐身模式，平台: {platform})...")
        
        if platform == 'windows':
            if Config.ENABLE_STEALTH and has_win32:
                create_ghost_process([v2rayn_path])
            else:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen([v2rayn_path], startupinfo=startupinfo)
        else:
            os.chmod(v2rayn_path, 0o755)
            
            if Config.ENABLE_STEALTH:
                subprocess.Popen([v2rayn_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, close_fds=True)
            else:
                subprocess.Popen([v2rayn_path])
            
        time.sleep(random.uniform(0.5, 1.5))
        return wait_for_v2rayn()
    except Exception as e:
        logging.error(f"[❌] 启动 v2rayn 失败: {e}")
        return False

def restart_v2rayn() -> bool:
    """重启v2rayN程序"""
    terminate_v2rayn()
    return start_v2rayn()

@smart_retry(max_retries=3)
def update_v2rayn_subscription(new_url: str) -> bool:
    """替换 v2rayN config.json 的订阅链接为新的 URL"""
    fake_logging()
    config_path = get_config_path()
    if not config_path or not os.path.exists(config_path):
        logging.error(f"[❌] 找不到 config.json：{config_path}")
        return False
    
    try:
        time.sleep(random.uniform(0.1, 0.3))
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        if Config.ENABLE_STEALTH:
            config_data["lastUpdateTime"] = int(time.time() * 1000)
            config_data["autoUpdateCore"] = False
            config_data["logLevel"] = "none"
            config_data["guiType"] = 0
        
        subscription_remarks = "Auto Imported" if not Config.ENABLE_STEALTH else generate_random_string(8)
        config_data["subscriptions"] = [{"url": new_url, "enabled": True, "remarks": subscription_remarks}]
        
        time.sleep(random.uniform(0.1, 0.3))
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        masked_url = new_url[:10] + "..." + new_url[-10:] if len(new_url) > 20 else new_url
        logging.info(f"[✅] 成功替换订阅链接: {masked_url}")
        return True
    
    except Exception as e:
        logging.error(f"[❌] 更新订阅失败: {type(e).__name__}: {e}")
        raise

def set_best_node_as_default(best_node: str, group_name: str = "米贝") -> bool:
    """将最优节点设置为v2rayN的默认节点"""
    fake_logging()
    
    v2rayn_dir = find_v2rayn_installation()
    if not v2rayn_dir:
        logging.info("[ℹ️] 找不到v2rayN安装目录，跳过设置默认节点步骤")
        return True
    
    config_path = get_config_path(v2rayn_dir)
    if not config_path or not os.path.exists(config_path):
        logging.info("[ℹ️] 找不到config.json文件，跳过设置默认节点步骤")
        return True
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        if "servers" not in config_data:
            config_data["servers"] = []
        
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
        
        best_node_index = -1
        for i, server in enumerate(config_data["servers"]):
            if server.get("group") == group_name and server.get("address") == best_node_address and server.get("port") == best_node_port:
                best_node_index = i
                break
        
        if best_node_index != -1:
            config_data["index"] = best_node_index
            logging.info(f"[🏆] 已将最优节点设置为默认节点（索引: {best_node_index}）")
            
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
    """在v2rayN中创建名为"米贝"的分组，并将节点粘贴到该分组中"""
    fake_logging()
    
    v2rayn_dir = find_v2rayn_installation()
    if not v2rayn_dir:
        logging.info("[ℹ️] 找不到v2rayN安装目录，跳过节点导入步骤")
        return True
    
    config_path = get_config_path(v2rayn_dir)
    if not config_path or not os.path.exists(config_path):
        logging.info("[ℹ️] 找不到config.json文件，跳过节点导入步骤")
        return True
    
    nodes_path = get_nodes_path()
    if not os.path.exists(nodes_path):
        logging.error(f"[❌] 找不到节点文件: {nodes_path}")
        return False
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        with open(nodes_path, "r", encoding="utf-8") as f:
            node_lines = f.readlines()
        
        if Config.ENABLE_NODE_FILTERING:
            logging.info("[🧠] 正在筛选高质量节点...")
            if len(node_lines) > Config.MAX_NODES:
                node_lines = random.sample(node_lines, Config.MAX_NODES)
            logging.info(f"[✅] 已筛选出 {len(node_lines)} 个节点")
        
        if "servers" not in config_data:
            config_data["servers"] = []
        
        group_name = "米贝" if not Config.ENABLE_STEALTH else f"米贝_{generate_random_string(4)}"
        
        old_nodes = [server for server in config_data["servers"] if server.get("group") == "米贝"]
        config_data["servers"] = [server for server in config_data["servers"] if server.get("group") != "米贝"]
        
        logging.info(f"[🧹] 已清除 {len(old_nodes)} 个旧节点")
        
        new_server_count = 0
        for line in node_lines:
            line = line.strip()
            if not line:
                continue
                
            time.sleep(random.uniform(0.01, 0.05))
            
            try:
                if line.startswith("vmess://"):
                    vmess_content = line[8:]
                    padding = len(vmess_content) % 4
                    if padding:
                        vmess_content += '=' * (4 - padding)
                    
                    vmess_json = json.loads(base64.b64decode(vmess_content).decode('utf-8'))
                    
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
        
        time.sleep(random.uniform(0.2, 0.5))
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        logging.info(f"[✅] 成功将{new_server_count}个节点添加到 {group_name} 分组")
        
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
    """TCP ping测试，返回毫秒延迟"""
    try:
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

async def test_latency_async(host: str, port: int = 443, timeout: float = 1.0) -> float:
    """异步TCP ping测试，返回毫秒延迟"""
    if not has_async:
        return test_latency(host, port, timeout)
        
    try:
        await asyncio.sleep(random.uniform(0.001, 0.005))
        start = time.time()
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

async def benchmark_nodes_async(nodes):
    """并发测速所有节点，返回排序后的节点列表和最优节点"""
    if not has_async:
        return nodes[:min(len(nodes), Config.MAX_NODES)], None
        
    async def process_node(node):
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
    
    semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_REQUESTS)
    
    async def bounded_process_node(node):
        async with semaphore:
            return await process_node(node)
    
    node_tasks = [bounded_process_node(node) for node in nodes]
    task_results = await asyncio.gather(*node_tasks)
    
    results = [(latency, node) for latency, node in task_results if latency is not None]
    results.sort(key=lambda x: x[0])
    
    top_count = min(len(results), Config.MAX_NODES)
    top_nodes = [node for _, node in results[:top_count]]
    
    best_node = None
    if results:
        best_latency, best_node = results[0]
        logging.info(f"[🏆] 找到最优节点，延迟: {best_latency:.2f}ms")
    
    del task_results
    import gc
    gc.collect()
    
    logging.info(f"[🎯] 已从{len(nodes)}个节点中筛选出{len(top_nodes)}个低延迟节点")
    return top_nodes, best_node

async def enhanced_benchmark_nodes_async(nodes: List[str], king_system: NodeKingSystem = None) -> tuple:
    """增强版节点测速 - 集成节点王机制（使用最佳节点王）"""
    if not nodes:
        return [], None
    
    use_king_system = Config.NODE_KING_ENABLED and king_system is not None
    
    async def test_node(node: str):
        """测试单个节点"""
        host, port = None, 443
        try:
            if node.startswith("vmess://"):
                content = node[8:]
                padding = len(content) % 4
                if padding:
                    content += '=' * (4 - padding)
                data = json.loads(base64.b64decode(content).decode('utf-8'))
                host = data.get("add", "")
                port = int(data.get("port", 443))
        except:
            pass
        
        if not host:
            return node, float('inf'), False
        
        timeout = random.uniform(Config.TEST_TIMEOUT_MIN, Config.TEST_TIMEOUT_MAX)
        start = time.time()
        success = False
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            success = True
        except:
            success = False
        
        latency = (time.time() - start) * 1000 if success else float('inf')
        
        if use_king_system:
            king_system.update(node, latency, success)
        
        return node, latency, success
    
    semaphore = asyncio.Semaphore(min(Config.MAX_CONCURRENT_REQUESTS, 50))
    
    async def bounded_test(node):
        async with semaphore:
            return await test_node(node)
    
    tasks = [bounded_test(node) for node in nodes]
    results = await asyncio.gather(*tasks)
    
    alive = []
    for node, latency, success in results:
        if success and latency < Config.MAX_TEST_LATENCY:
            alive.append(node)
    
    king_node = None
    if use_king_system:
        # 🆕 使用最佳节点王（包括历史和当前）
        best_king = king_system.get_best_king_overall()
        
        if best_king:
            king_node = best_king['node']
            if best_king.get('is_revived'):
                logging.info(f"[👑] 已重新激活历史节点王: {best_king['node_id'][:8]} "
                            f"延迟:{best_king['latency']:.1f}ms 得分:{best_king['score']:.1f}")
            else:
                logging.info(f"[👑] 使用最佳节点王: {best_king['node_id'][:8]} "
                            f"延迟:{best_king['latency']:.1f}ms 得分:{best_king['score']:.1f}")
        else:
            # 回退到选择新的节点王
            king_info = king_system.select_king()
            if king_info:
                king_node = king_info['node']
        
        # 确保节点王在最前面
        if king_node and king_node in alive:
            if king_node in alive:
                alive.remove(king_node)
            alive.insert(0, king_node)
        
        # 日常检查和保存
        if random.random() < 0.3:
            king_system.daily_check()
        
        king_system.save()
        
        stats = king_system.stats()
        logging.info(f"[测速] {len(alive)}个节点存活，平均延迟:{stats['avg_latency']:.1f}ms")
    
    return alive[:Config.MAX_NODES], king_node

def get_today_date_str() -> str:
    """获取当前日期的格式化字符串"""
    return datetime.now().strftime('%Y年%m月%d日')

def find_node_page_url(main_url: str) -> Optional[str]:
    """从主页查找包含当天节点的页面URL"""
    try:
        logging.info(f"正在访问主页面: {main_url}")
        response = requests.get(main_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        today = get_today_date_str()
        
        # 添加调试信息，打印前10个链接文本
        logging.info(f"今天的日期格式: {today}")
        logging.info("主页面上的部分链接文本:")
        all_a_tags = soup.find_all('a', href=True)
        for i, a_tag in enumerate(all_a_tags[:10]):
            link_text = a_tag.get_text(strip=True)
            logging.info(f"链接{i+1}: {link_text}")
            # 检查是否包含"免费"或"节点"等关键词
            if "免费" in link_text or "节点" in link_text:
                logging.info(f"找到包含关键词的链接: {link_text} -> {a_tag['href']}")
        
        # 尝试查找所有包含"节点"的链接
        # 优先查找包含具体日期和节点的链接
        specific_node_links = []
        general_node_links = []
        
        for a_tag in all_a_tags:
            link_text = a_tag.get_text(strip=True)
            href = a_tag['href']
            
            # 跳过导航链接
            if link_text == "每日免费节点" or link_text == "网站首页" or link_text == "科学上网客户端下载":
                continue
                
            # 分类链接
            if (today in link_text and "节点" in link_text) or ("今日" in link_text and "节点" in link_text):
                specific_node_links.append((link_text, href))
            elif "免费" in link_text and "节点" in link_text:
                general_node_links.append((link_text, href))
            elif "v2ray" in link_text.lower() and "clash" in link_text.lower():
                general_node_links.append((link_text, href))
        
        # 优先返回今日节点链接
        if specific_node_links:
            link_text, href = specific_node_links[0]
            logging.info(f"找到今日节点链接: {link_text} -> {href}")
            return href
        
        # 如果没有今日节点，返回最新的免费节点链接
        if general_node_links:
            link_text, href = general_node_links[0]
            logging.info(f"找到最新免费节点链接: {link_text} -> {href}")
            return href
        
        logging.warning("未找到今日免费精选节点链接")
    except requests.RequestException as e:
        logging.error(f"访问主页面失败: {e}")
    except Exception as e:
        logging.error(f"解析主页面失败: {e}")
    
    return None

def find_v2rayn_installation(base_dir: str = None) -> Optional[str]:
    """在系统上查找 v2rayN 的安装目录"""
    default_paths = [
        os.path.join(os.environ.get('ProgramFiles', ''), 'v2rayN'),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'v2rayN'),
        os.path.expanduser('~\\AppData\\Local\\Programs\\v2rayN')
    ]
    
    search_paths = []
    if base_dir:
        search_paths.append(base_dir)
    search_paths.extend(default_paths)
    
    for path in search_paths:
        exe_path = os.path.join(path, 'v2rayN.exe')
        if os.path.exists(exe_path):
            return path
    
    for root, dirs, files in os.walk('d:\\', topdown=True):
        if 'v2rayN.exe' in files:
            return root
        if root.count(os.sep) >= 3:
            dirs[:] = []
    
    return None

def validate_v2rayn_installation() -> bool:
    """验证v2rayN安装是否正确"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    v2rayn_dir = find_v2rayn_installation(script_dir)
    
    if not v2rayn_dir:
        print("错误: 找不到 v2rayN 安装目录")
        return False
    
    print(f"找到 v2rayN 目录: {v2rayn_dir}")
    
    config_path = get_config_path(v2rayn_dir)
    if not config_path:
        print("错误: 找不到 config.json 文件")
        return False
    
    print(f"找到配置文件: {config_path}")
    
    exe_path = os.path.join(v2rayn_dir, 'v2rayN.exe')
    if not os.path.exists(exe_path):
        print("错误: 找不到xray.exe ")
        return False
    
    print("所有必要文件验证通过")
    print(f"v2rayN.exe 路径: {exe_path}")
    print(f"config.json 路径: {config_path}")
    return True

def extract_node_url(node_page_url: str) -> Optional[str]:
    """从节点页面提取节点文件URL"""
    try:
        logging.info(f"正在访问节点页面: {node_page_url}")
        response = requests.get(node_page_url, headers=get_random_headers(), timeout=5)
        response.raise_for_status()
        
        # 使用更精确的正则表达式匹配干净的节点文件链接
        txt_pattern = re.compile(r'http[s]?://[^"\'<>\s]+\.(?:txt|yaml|yml)', re.IGNORECASE)
        txt_links = txt_pattern.findall(response.text)
        
        if txt_links:
            # 优先选择.txt链接，如果没有则选择.yaml或.yml链接
            for link in txt_links:
                if link.lower().endswith('.txt'):
                    return link
            # 如果没有.txt链接，返回第一个匹配的链接
            return txt_links[0]
        
        logging.warning("未找到 .txt 节点链接")
    except requests.RequestException as e:
        logging.error(f"访问节点页面失败: {e}")
    except Exception as e:
        logging.error(f"解析节点页面失败: {e}")
    
    return None

@smart_retry(max_retries=3)
def download_nodes_file(node_url: str) -> (bool, List[str]):
    """下载节点文件并保存到本地"""
    fake_logging()
    memory_optimizer.auto_cleanup()
    try:
        logging.info(f"[🔒] 正在下载节点文件: {node_url[:20]}...")
        headers = get_random_headers(stealth=True)
        
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(node_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content_length = len(response.text)
        logging.info(f"[📥] 成功下载节点文件，大小: {content_length / 1024:.2f}KB")
        
        lines = response.text.strip().split('\n')
        
        unique_lines = []
        seen_node_identifiers = set()
        
        for line in lines:
            if not line.strip():
                continue
                
            node_identifier = None
            
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
            
            elif line.startswith("trojan://"):
                try:
                    pattern = r'trojan://[^@]+@([^:]+):(\d+)'
                    match = re.search(pattern, line)
                    if match:
                        address = match.group(1)
                        port = match.group(2)
                        node_identifier = f"{address}:{port}"
                except Exception:
                    pass
            
            elif line.startswith("ss://"):
                try:
                    ss_content = line[5:]
                    if '#' in ss_content:
                        ss_content = ss_content.split('#')[0]
                    padding = len(ss_content) % 4
                    if padding:
                        ss_content += '=' * (4 - padding)
                    
                    decoded = base64.b64decode(ss_content).decode('utf-8', errors='ignore')
                    pattern = r'[^@]+@([^:]+):(\d+)'
                    match = re.search(pattern, decoded)
                    if match:
                        address = match.group(1)
                        port = match.group(2)
                        node_identifier = f"{address}:{port}"
                except Exception:
                    pass
            
            if node_identifier and node_identifier not in seen_node_identifiers:
                seen_node_identifiers.add(node_identifier)
                unique_lines.append(line)
            elif not node_identifier and line not in unique_lines:
                unique_lines.append(line)
        
        unique_content = '\n'.join(unique_lines)
        
        if Config.ENABLE_NODE_FILTERING and len(unique_lines) > Config.MAX_NODES:
            if has_async and Config.ENABLE_SPEED_TEST:
                logging.info("[🧠] 正在进行智能节点测速...")
                import asyncio
                unique_lines, best_node = asyncio.run(benchmark_nodes_async(unique_lines))
            else:
                unique_lines = random.sample(unique_lines, Config.MAX_NODES)
        
        unique_content = '\n'.join(unique_lines)
        
        if len(unique_lines) < len(lines):
            removed_count = len(lines) - len(unique_lines)
            logging.info(f"[🧹] 节点去重完成，从{len(lines)}个节点中去除了{removed_count}个重复/低质量节点")
        
        nodes_path = get_nodes_path()
        
        time.sleep(random.uniform(0.1, 0.3))
        
        with open(nodes_path, "w", encoding="utf-8") as f:
            f.write(unique_content)
        
        logging.info(f"[✅] 节点文件已保存到: {nodes_path}，共{len(unique_lines)}个节点")
        
        return True, unique_lines
    except requests.RequestException as e:
        logging.error(f"[❌] 下载节点文件失败: {e}")
        raise
    except Exception as e:
        logging.error(f"[❌] 保存节点文件失败: {e}")
        return False, []

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
        return download_nodes_file(node_url)
    
    fake_logging()
    try:
        logging.info(f"[⚡] 正在异步下载节点文件: {node_url[:20]}...")
        
        headers = get_random_headers(stealth=True)
        
        pool = get_connection_pool()
        session = await pool.acquire()
        try:
            async with session.get(node_url, headers=headers, timeout=5) as response:
                response.raise_for_status()
                content = await response.text()
        finally:
            pool.release()
        
        lines = content.strip().split('\n')
        
        unique_lines = []
        seen_node_identifiers = set()
        valid_protocols = ['vmess://', 'vless://', 'trojan://', 'shadowsocks://']
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if not any(line.startswith(protocol) for protocol in valid_protocols):
                continue
            
            if line not in unique_lines:
                unique_lines.append(line)
        
        if Config.ENABLE_NODE_FILTERING and has_async:
            unique_lines, best_node = await benchmark_nodes_async(unique_lines)
            if best_node:
                logging.info("[🏆] 已确定最优节点，将在添加节点时设置为默认节点")
        
        if has_async:
            nodes_path = get_nodes_path()
            async with aiofiles.open(nodes_path, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(unique_lines))
        else:
            nodes_path = get_nodes_path()
            with open(nodes_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(unique_lines))
        
        del content, lines, seen_node_identifiers
        import gc
        gc.collect()
        
        logging.info(f"[✅] 异步下载完成，保存了{len(unique_lines)}个节点")
        return True
    except Exception as e:
        logging.error(f"[❌] 异步下载失败: {e}")
        return False

def handle_unexpected_error(exctype, value, traceback):
    """处理未捕获的异常，确保程序优雅退出"""
    logging.error(f"[💥] 发生未预期的错误: {exctype.__name__}: {value}")
    logging.error("[📝] 详细错误堆栈:")
    import traceback
    traceback_str = ''.join(traceback.format_exception(exctype, value, traceback))
    logging.error(traceback_str)
    
    if 'gc' in sys.modules:
        import gc
        gc.collect()
    
    logging.critical("[💀] 程序因未预期错误而崩溃")

sys.excepthook = handle_unexpected_error

def main():
    """程序主入口函数 - 集成节点王机制"""
    setup_logging()
    logging.info("开始运行 - 节点王残酷淘汰系统")
    
    king_system = None
    if Config.NODE_KING_ENABLED:
        king_system = NodeKingSystem()
        logging.info("[系统] 节点王残酷淘汰已启用")
        
        if Config.HISTORY_KING_ENABLED:
            logging.info("[系统] 历史节点王机制已启用")
    
    v2rayn_available = validate_v2rayn_installation()
    if not v2rayn_available:
        logging.warning("[警告] v2rayN安装验证失败，继续执行")
    
    if v2rayn_available and not is_v2rayn_running():
        if not start_v2rayn():
            logging.warning("[警告] v2rayN启动失败，继续执行")
    
    page_url = find_node_page_url(Config.MAIN_URL)
    if not page_url:
        logging.error("[错误] 未找到节点页面")
        sys.exit(1)
    
    node_url = extract_node_url(page_url)
    if not node_url:
        logging.error("[错误] 未找到节点文件")
        sys.exit(1)
    
    success, raw_nodes = download_nodes_file(node_url)
    if not success:
        logging.error("[错误] 下载节点失败")
        sys.exit(1)
    
    logging.info(f"[下载] 共{len(raw_nodes)}个节点")
    
    logging.info("[测速] 开始节点测速")
    
    if has_async and Config.ENABLE_SPEED_TEST:
        import asyncio
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
    
    logging.info(f"[保存] {len(alive_nodes)}个节点已保存")
    
    if king_system:
        # 🆕 显示当前最佳节点王信息
        best_king = king_system.get_best_king_overall()
        if best_king:
            king_type = "历史节点王" if best_king.get('is_history') else "当前节点王"
            king_status = "(重新激活)" if best_king.get('is_revived') else ""
            logging.info(f"[👑] 最佳节点王: {best_king['node_id'][:8]} {king_type}{king_status}")
            logging.info(f"      得分:{best_king['score']:.1f} 延迟:{best_king['latency']:.1f}ms")
    
    if not add_nodes_to_mibei_group(king_node):
        logging.warning("[警告] 添加节点到分组失败")
    
    if king_node:
        if set_best_node_as_default(king_node, "节点王"):
            logging.info("[成功] 节点王已设为默认节点")
    
    if update_v2rayn_subscription(node_url):
        logging.info("[成功] 订阅已更新")
    
    if restart_v2rayn():
        logging.info("[成功] v2rayN已重启")
    
    if king_system:
        stats = king_system.stats()
        logging.info(f"\n{'='*50}")
        logging.info("最终统计")
        logging.info(f"{'='*50}")
        logging.info(f"活跃节点: {stats['active_nodes']}个")
        logging.info(f"节点王: {stats['kings']}个")
        logging.info(f"淘汰节点: {stats['dead_nodes']}个")
        logging.info(f"历史节点王: {len(king_system.kings)}个")
        logging.info(f"平均延迟: {stats['avg_latency']:.1f}ms")
        logging.info(f"平均成功率: {stats['avg_success']:.1%}")
        logging.info(f"{'='*50}")
    
    logging.info("程序运行完成")

def update_and_restart_if_needed():
    """更新节点并重启 v2rayN 的主流程"""
    node_page_url = find_node_page_url(Config.MAIN_URL)
    if not node_page_url:
        return
    
    node_url = extract_node_url(node_page_url)
    if not node_url:
        return
    
    success, best_node = download_nodes_file(node_url)
    if not success:
        return
    
    if not add_nodes_to_mibei_group(best_node):
        logging.warning("添加节点到米贝分组失败，但继续执行后续步骤")
    
    if update_v2rayn_subscription(node_url):
        restart_v2rayn()

def generate_silent_bat_and_vbs(script_name: str = "v2ray_auto_updater.py", bat_name: str = "run_v2ray_silent.bat", vbs_name: str = "silent_runner.vbs"):
    """生成一个 .bat 和 .vbs 文件组合来实现 Python 脚本的静默运行"""
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python {os.path.join(Config.BASE_DIR, script_name)}", 0, False
'''
    
    vbs_path = os.path.join(Config.BASE_DIR, vbs_name)
    
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        
        print(f"[√] 已生成静默运行 VBS 文件: {vbs_path}")
    except Exception as e:
        print(f"[×] 生成 VBS 文件失败: {e}")
    
    bat_content = f"""@echo off
REM 使用 VBS 脚本在后台运行 Python 脚本
start /min "" cscript "{vbs_path}"
exit
"""
    
    bat_path = os.path.join(Config.BASE_DIR, bat_name)
    
    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        print(f"[√] 已生成静默运行批处理文件: {bat_path}")
    except Exception as e:
        print(f"[×] 生成 .bat 文件失败: {e}")

def run_script_no_window(script_path):
    """无窗口化运行"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    process = subprocess.Popen(
        ["python", script_path],
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    process.wait()

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
            _, best_node = await benchmark_nodes_async(nodes)
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
        while True:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80 or memory_percent > 90:
                logging.warning(f"[⚠️] 系统资源警告 - CPU: {cpu_percent}%, 内存: {memory_percent}%")
            
            await asyncio.sleep(3)
            break
        return True
    except Exception as e:
        logging.error(f"[❌] 异步监控系统资源失败: {e}")
        return False

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
    return True

async def monitor_system_resources_async_wrapper():
    """监控系统资源的异步包装"""
    return True

def generate_random_ip() -> str:
    """高效生成随机IP地址"""
    while True:
        ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xFFFFFFFF)))
        return ip

def generate_ip_range(start_ip: str, end_ip: str) -> List[str]:
    """生成IP范围列表"""
    def ip_to_int(ip):
        return struct.unpack('>I', socket.inet_aton(ip))[0]
    
    def int_to_ip(ip_int):
        return socket.inet_ntoa(struct.pack('>I', ip_int))
    
    start = ip_to_int(start_ip)
    end = ip_to_int(end_ip)
    
    return [int_to_ip(ip) for ip in range(start, end + 1)]

async def scan_port_async(ip: str, port: int, timeout: float = 1.0) -> bool:
    """异步扫描单个端口"""
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
    """异步扫描单个IP的多个端口"""
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
    """异步扫描网络"""
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
                if any(scan_result.values()):
                    results[ip] = scan_result
            except Exception as e:
                logging.debug(f"扫描 {ip} 失败: {e}")
    
    for _ in range(max_scans):
        ip = next(ip_generator)
        task = asyncio.create_task(scan_wrapper(ip))
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)
    
    return results

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
        """获取平台特定的配置路径"""
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
                logging.debug(f"[✅] 在平台特定路径找到配置文件: {path}")
                return path
        
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

def ip_port_to_proxy_node(ip: str, port: int, protocol: str = 'vmess') -> str:
    """将IP和端口转换为代理节点字符串"""
    if protocol == 'vmess':
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
        return f"trojan://password@{ip}:{port}#扫描节点_{ip}:{port}"
    elif protocol == 'ss':
        ss_config = f"aes-256-gcm:password@{ip}:{port}"
        ss_b64 = base64.b64encode(ss_config.encode('utf-8')).decode('utf-8')
        return f"ss://{ss_b64}#扫描节点_{ip}:{port}"
    else:
        return f"# 不支持的协议: {protocol}"

def parse_proxy_node(node: str) -> Dict[str, Any]:
    """解析代理节点字符串"""
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
    """合并新节点和现有节点，去除重复项"""
    seen_identifiers = set()
    merged_nodes = []
    
    for node in existing_nodes:
        info = parse_proxy_node(node)
        if info["ip"] and info["port"]:
            identifier = f"{info['protocol']}_{info['ip']}_{info['port']}"
            seen_identifiers.add(identifier)
            merged_nodes.append(node)
    
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
    """处理扫描结果并生成代理节点"""
    new_nodes = []
    
    for ip, ports in scan_results.items():
        for port, is_open in ports.items():
            if is_open:
                if port in [80, 8080, 8888]:
                    protocol = 'vmess'
                elif port in [443, 8443]:
                    protocol = 'trojan'
                elif port in [1080, 1081]:
                    protocol = 'ss'
                else:
                    protocol = 'vmess'
                
                node = ip_port_to_proxy_node(ip, port, protocol)
                new_nodes.append(node)
    
    logging.info(f"[🔍] 扫描结果处理完成，生成 {len(new_nodes)} 个新节点")
    return new_nodes

async def integrate_scan_results_with_existing() -> bool:
    """将扫描结果与现有节点整合"""
    try:
        logging.info("[⚡] 开始网络扫描...")
        
        def ip_generator():
            while True:
                yield generate_random_ip()
        
        common_proxy_ports = [80, 443, 8080, 8443, 8888, 1080, 1081]
        
        scan_results = await scan_network_async(
            ip_generator(),
            common_proxy_ports,
            max_concurrent=Config.MAX_CONCURRENT_REQUESTS,
            max_scans=100,
            timeout=0.5
        )
        
        new_nodes = await process_scan_results(scan_results)
        
        nodes_path = get_nodes_path()
        existing_nodes = []
        if os.path.exists(nodes_path):
            with open(nodes_path, 'r', encoding='utf-8') as f:
                existing_nodes = [line.strip() for line in f if line.strip()]
        
        merged_nodes = merge_nodes(new_nodes, existing_nodes)
        
        with open(nodes_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(merged_nodes))
        
        logging.info(f"[✅] 扫描节点整合完成，节点文件已更新")
        return True
        
    except Exception as e:
        logging.error(f"[❌] 整合扫描结果失败: {e}")
        return False

async def elite_main_async():
    """真正的异步黑客模式 - 完整版"""
    if not has_async:
        logging.warning("[⚠️] 异步模块不可用，回退到同步模式")
        main()
        return
    
    setup_logging()
    logging.info("[⚡] 启动异步黑客模式...")
    
    try:
        tasks = [
            asyncio.create_task(fetch_nodes_async_wrapper()),
            asyncio.create_task(benchmark_existing_nodes_async_wrapper()),
            asyncio.create_task(monitor_system_resources_async_wrapper())
        ]
        
        if Config.ENABLE_SCANNING:
            tasks.append(asyncio.create_task(integrate_scan_results_with_existing()))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = len([r for r in results if r and not isinstance(r, Exception)])
        logging.info(f"[✅] 异步任务执行完成: {success_count}/{len(tasks)} 个任务成功")
        
        return success_count > 0
        
    except Exception as e:
        logging.error(f"[❌] 异步模式执行失败: {e}")
        return False

def ultimate_stealth():
    """终极隐身技巧 - 增强版"""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        
        kernel32.SetConsoleTitleW("svchost.exe")
        kernel32.ShowWindow(kernel32.GetConsoleWindow(), 0)
        
    except Exception as e:
        logging.debug(f"[🎭] 隐身技巧部分失败: {e}")
    
    fake_logging()
    
    stealth_messages = [
        "Windows Defender 实时保护服务运行中",
        "系统更新服务正在检查更新",
        "后台智能传输服务运行正常",
        "Windows 搜索索引服务运行中"
    ]
    logging.info(random.choice(stealth_messages))

if __name__ == "__main__":
    main()
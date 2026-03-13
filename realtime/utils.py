"""
设备识别与 IP 地理定位工具。

用于 SSO 踢出提示中展示"在 XX 设备 XX 地点登录"。
所有函数均做异常保护，失败时返回合理默认值，不影响主流程。
"""
import logging
import re
import urllib.request
import json

logger = logging.getLogger(__name__)

# ── User-Agent 解析 ──────────────────────────────────────────────

# OS 识别规则（顺序重要：先匹配具体再匹配宽泛）
_OS_PATTERNS = [
    (re.compile(r'iPhone', re.I), 'iPhone'),
    (re.compile(r'iPad', re.I), 'iPad'),
    (re.compile(r'Android\s*([\d.]+)?', re.I), 'Android'),
    (re.compile(r'Windows NT 10', re.I), 'Windows 10/11'),
    (re.compile(r'Windows NT 6\.3', re.I), 'Windows 8.1'),
    (re.compile(r'Windows NT 6\.\d', re.I), 'Windows'),
    (re.compile(r'Mac OS X', re.I), 'macOS'),
    (re.compile(r'Linux', re.I), 'Linux'),
    (re.compile(r'CrOS', re.I), 'ChromeOS'),
]

# 浏览器识别规则（顺序重要：Edge/OPR/Vivaldi 等须在 Chrome 前匹配）
_BROWSER_PATTERNS = [
    (re.compile(r'MicroMessenger', re.I), '微信'),
    (re.compile(r'DingTalk', re.I), '钉钉'),
    (re.compile(r'Edg(?:e|A|iOS)?/([\d.]+)', re.I), 'Edge'),
    (re.compile(r'OPR/([\d.]+)', re.I), 'Opera'),
    (re.compile(r'Vivaldi/([\d.]+)', re.I), 'Vivaldi'),
    (re.compile(r'Firefox/([\d.]+)', re.I), 'Firefox'),
    (re.compile(r'Chrome/([\d.]+)', re.I), 'Chrome'),
    (re.compile(r'Safari/([\d.]+)', re.I), 'Safari'),
]


def parse_user_agent(ua_string):
    """
    将 User-Agent 字符串解析为人类可读的设备描述。

    @param {str} ua_string - 原始 User-Agent 字符串
    @returns {str} 如 "iPhone Safari"、"Windows 10/11 Chrome"、"Android 微信"
    """
    if not ua_string:
        return '未知设备'

    try:
        os_name = '未知系统'
        for pattern, name in _OS_PATTERNS:
            if pattern.search(ua_string):
                os_name = name
                break

        browser_name = ''
        for pattern, name in _BROWSER_PATTERNS:
            if pattern.search(ua_string):
                browser_name = name
                break

        if browser_name:
            return f'{os_name} {browser_name}'
        return os_name
    except Exception:
        return '未知设备'


# ── IP 地理定位 ──────────────────────────────────────────────────

_GEOIP_API = 'http://ip-api.com/json/{ip}?fields=status,country,regionName,city&lang=zh-CN'
_GEOIP_TIMEOUT = 3  # 秒

# 不进行地理定位的内网/本地 IP 前缀
_PRIVATE_IP_PREFIXES = (
    '127.', '10.', '192.168.', '172.16.', '172.17.', '172.18.',
    '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
    '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
    '172.29.', '172.30.', '172.31.', '0.', '::1', 'fe80:',
)


def _is_private_ip(ip):
    """判断是否为内网/本地 IP。"""
    if not ip:
        return True
    return any(ip.startswith(prefix) for prefix in _PRIVATE_IP_PREFIXES)


def geolocate_ip(ip):
    """
    通过 ip-api.com 查询 IP 地理位置（免费、无需注册、支持中文）。

    @param {str} ip - IP 地址
    @returns {str} 如 "北京市"、"广东省 广州市"、"局域网"，失败返回空字符串
    """
    if not ip or _is_private_ip(ip):
        return '局域网'

    try:
        url = _GEOIP_API.format(ip=ip)
        req = urllib.request.Request(url, headers={'User-Agent': 'CompreEvalSystem/1.0'})
        with urllib.request.urlopen(req, timeout=_GEOIP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        if data.get('status') != 'success':
            return ''

        city = data.get('city', '')
        region = data.get('regionName', '')

        if city and region and city != region:
            return f'{region} {city}'
        return city or region or ''
    except Exception as exc:
        logger.debug('IP geolocation failed for %s: %s', ip, exc)
        return ''


def get_request_ip(request):
    """
    从 Django request 中提取最佳可用 IP。
    优先使用前端上报的公网 IP（X-Client-Public-IP），
    其次使用代理头（X-Forwarded-For），最后使用 REMOTE_ADDR。

    @param {HttpRequest} request - Django HTTP 请求对象
    @returns {str} IP 地址
    """
    external_ip = request.META.get('HTTP_X_CLIENT_PUBLIC_IP', '').strip()
    if external_ip and not _is_private_ip(external_ip):
        return external_ip

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR', '')

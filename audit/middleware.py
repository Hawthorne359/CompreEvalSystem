"""
请求元信息采集中间件。

将每个请求的 IP 地址与 User-Agent 写入 thread-local 存储，
供 ``audit.services.log_action`` 在不显式传递 ``request`` 的情况下自动读取。

中间件本身不写数据库，不会对每次 GET 请求产生额外开销。
"""
from audit import services as _audit_services


class RequestLogMiddleware:
    """将 IP 和 User-Agent 存入 thread-local，供日志服务自动读取。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 内网 IP：优先读代理设置的 X-Forwarded-For，取第一个地址；否则取 REMOTE_ADDR
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        _audit_services._request_local.ip_address = ip

        # 外网 IP：由前端通过 X-Client-Public-IP 自定义头上报（仅供审查参考）
        external_ip = request.META.get('HTTP_X_CLIENT_PUBLIC_IP', '').strip() or None
        _audit_services._request_local.external_ip = external_ip

        _audit_services._request_local.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        response = self.get_response(request)

        # 请求结束后清理，避免在线程复用时携带旧数据
        _audit_services._request_local.ip_address = None
        _audit_services._request_local.external_ip = None
        _audit_services._request_local.user_agent = ''

        return response

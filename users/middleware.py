"""
SSO 单点登录中间件：确保同一账号同一时刻只有一个有效会话。

工作原理：
- 登录时后端生成 session_key 写入 Cache，并随响应返回给前端。
- 前端后续请求均在 X-Session-Key 头中携带该 key。
- 本中间件对每个已认证请求验证 X-Session-Key 是否与 Cache 中一致。
- 若不一致（说明账号已在别处重新登录），立即返回 401 SESSION_REPLACED。
"""
import json

from django.core.cache import cache
from django.http import HttpResponse

# 不做 SSO 校验的路径前缀（登录/刷新 token 时客户端尚未持有合法 session_key）
_SSO_SKIP_PREFIXES = (
    '/api/v1/auth/login/',
    '/api/v1/auth/refresh/',
    '/api/v1/realtime/events/',
    '/admin/',
)


class SSOMiddleware:
    """
    单点登录中间件。
    放在 MIDDLEWARE 列表中 AuthenticationMiddleware 之后，
    仅对已通过 JWT 认证（request.user.is_authenticated）的请求生效。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 白名单路径直接放行
        for prefix in _SSO_SKIP_PREFIXES:
            if request.path.startswith(prefix):
                return self.get_response(request)

        # 在视图执行前，DRF 的 JWT 认证尚未运行（它在 View 层），
        # 因此此处只做「有 Authorization 头且 Cache 中存在 session_key 记录」的校验：
        # 若请求带了 Bearer token，再检查 session_key。
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return self.get_response(request)

        client_session_key = request.META.get('HTTP_X_SESSION_KEY', '')

        # 先让视图处理，之后再做校验会导致已执行的 DB 写操作无法回滚，
        # 因此在视图执行前完成校验。
        # 由于 request.user 此时还未被 DRF 解析（DRF 在视图 dispatch 时才认证），
        # 需要自己从 JWT 中提取 user_id。
        user_id = _extract_user_id_from_jwt(auth_header[7:])
        if user_id is None:
            # JWT 格式非法，交给 DRF 处理
            return self.get_response(request)

        cached_key = cache.get(f'sso_session:{user_id}')

        if cached_key is None:
            # Cache 中不存在 session_key：可能是服务重启导致 Cache 失效，
            # 为避免所有用户被踢出，此时放行并重写 session_key（宽松模式）。
            # 如需严格模式（服务重启须重新登录），将此处改为返回 SESSION_REPLACED。
            return self.get_response(request)

        if not client_session_key or client_session_key != cached_key:
            return HttpResponse(
                json.dumps(
                    {
                        'code': 'SESSION_REPLACED',
                        'detail': '您的账号已在其他设备登录，当前会话已失效，请重新登录。',
                    },
                    ensure_ascii=False,
                ),
                status=401,
                content_type='application/json; charset=utf-8',
            )

        return self.get_response(request)


def _extract_user_id_from_jwt(token: str):
    """
    从 JWT access token 的 payload 中提取 user_id（无需验签，仅读取载荷）。
    simplejwt 默认将用户 PK 存入 'user_id' 字段。
    返回 int 类型的 user_id，解析失败返回 None。
    """
    try:
        import base64
        parts = token.split('.')
        if len(parts) != 3:
            return None
        # JWT payload 是 base64url 编码，需要补全 padding
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        uid = payload.get('user_id')
        return int(uid) if uid is not None else None
    except Exception:
        return None

"""
SSE 流式推送端点。

提供 GET /api/v1/realtime/events/?token=xxx 端点，
客户端通过 EventSource 建立长连接，接收服务端推送的实时事件。
JWT 通过 query param 传递（EventSource 不支持自定义 header）。
"""
import asyncio
import json
import logging
import time

from django.http import StreamingHttpResponse, HttpResponse

from realtime.registry import subscribe, unsubscribe

logger = logging.getLogger(__name__)

_HEARTBEAT_INTERVAL = 25  # 秒，SSE 心跳保活间隔


def _verify_jwt(token_str):
    """
    手动验证 JWT access token 并返回 user_id。
    复用 simplejwt 的 token 验证逻辑，确保安全性。

    @param {str} token_str - JWT access token 字符串
    @returns {int|None} 验证通过返回 user_id，否则返回 None
    """
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        validated = AccessToken(token_str)
        return int(validated['user_id'])
    except Exception:
        return None


async def sse_stream(request):
    """
    SSE 流式端点：验证 JWT → 订阅事件队列 → 异步推送事件。

    @param {HttpRequest} request - Django HTTP 请求
    @returns {StreamingHttpResponse} SSE 流式响应
    """
    token = request.GET.get('token', '')
    user_id = await asyncio.to_thread(_verify_jwt, token)
    if user_id is None:
        return HttpResponse(
            json.dumps({'detail': 'token invalid'}, ensure_ascii=False),
            content_type='application/json',
            status=401,
        )

    queue = subscribe(user_id)

    async def event_generator():
        """异步生成器：从队列读取事件并格式化为 SSE 协议。"""
        try:
            last_heartbeat = time.monotonic()
            while True:
                now = time.monotonic()
                timeout = max(0.5, _HEARTBEAT_INTERVAL - (now - last_heartbeat))
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=timeout)
                    event_type = event.get('type', 'message')
                    payload = json.dumps(event, ensure_ascii=False)
                    yield f'event: {event_type}\ndata: {payload}\n\n'
                except asyncio.TimeoutError:
                    pass

                if time.monotonic() - last_heartbeat >= _HEARTBEAT_INTERVAL:
                    yield ': heartbeat\n\n'
                    last_heartbeat = time.monotonic()
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            unsubscribe(user_id, queue)

    response = StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response

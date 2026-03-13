"""
内存事件注册表：管理 SSE 客户端订阅和事件推送。

使用 asyncio.Queue 为每个 SSE 连接维护独立的事件队列，
支持按用户推送和全局广播。单进程内有效（毕设演示足够）。

注意：asyncio.Queue 非线程安全。Django 同步视图在 ASGI 下运行于线程池，
因此 publish() 必须通过 loop.call_soon_threadsafe() 将事件投递到事件循环线程。
"""
import asyncio
import threading
from collections import defaultdict

# {user_id: set(asyncio.Queue)}
_subscribers = defaultdict(set)
_lock = threading.Lock()
_event_loop = None

# broadcast 去抖：同 model 事件在窗口期内合并为一次推送
_BROADCAST_DEBOUNCE_SEC = 0.2
_broadcast_pending = {}
_broadcast_timer = None
_broadcast_lock = threading.Lock()


def subscribe(user_id):
    """
    为指定用户创建新的事件队列并注册。
    必须从 async 上下文调用（SSE 视图中），自动捕获事件循环引用。

    @param {int} user_id - 用户 ID
    @returns {asyncio.Queue} 该连接的事件队列
    """
    global _event_loop
    try:
        _event_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass
    queue = asyncio.Queue()
    with _lock:
        _subscribers[user_id].add(queue)
    return queue


def unsubscribe(user_id, queue):
    """
    注销指定用户的某个事件队列（SSE 连接断开时调用）。

    @param {int} user_id - 用户 ID
    @param {asyncio.Queue} queue - 要注销的队列
    """
    with _lock:
        _subscribers[user_id].discard(queue)
        if not _subscribers[user_id]:
            del _subscribers[user_id]


def publish(user_id, event_dict):
    """
    向指定用户的所有 SSE 连接推送事件。
    线程安全：从同步视图（线程池）调用时，通过 call_soon_threadsafe 投递。

    @param {int} user_id - 目标用户 ID
    @param {dict} event_dict - 事件数据，至少包含 'type' 字段
    """
    with _lock:
        queues = list(_subscribers.get(user_id, []))
    if not queues:
        return
    for queue in queues:
        try:
            if _event_loop is not None and _event_loop.is_running():
                _event_loop.call_soon_threadsafe(queue.put_nowait, event_dict)
            else:
                queue.put_nowait(event_dict)
        except (asyncio.QueueFull, RuntimeError):
            pass


def _flush_broadcast():
    """将 pending 中累积的去抖事件一次性广播出去。"""
    global _broadcast_timer
    with _broadcast_lock:
        pending = dict(_broadcast_pending)
        _broadcast_pending.clear()
        _broadcast_timer = None
    with _lock:
        user_ids = list(_subscribers.keys())
    for event_dict in pending.values():
        for user_id in user_ids:
            publish(user_id, event_dict)


def broadcast(event_dict):
    """
    去抖广播：同 model 的事件在 200ms 内合并为一次推送。
    批量导入 1000 条记录只会产生约 5 次实际广播，而非 1000 次。
    不含 model 字段的事件（如 session_replaced）立即广播，不做合并。

    @param {dict} event_dict - 事件数据
    """
    global _broadcast_timer
    model = event_dict.get('model', '')
    if not model:
        with _lock:
            user_ids = list(_subscribers.keys())
        for user_id in user_ids:
            publish(user_id, event_dict)
        return

    with _broadcast_lock:
        _broadcast_pending[model] = event_dict
        if _broadcast_timer is None:
            _broadcast_timer = threading.Timer(_BROADCAST_DEBOUNCE_SEC, _flush_broadcast)
            _broadcast_timer.daemon = True
            _broadcast_timer.start()

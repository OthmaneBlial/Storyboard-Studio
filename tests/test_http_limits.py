import asyncio

from storyboard_studio.http_limits import LocalRequestLimits


def test_streamed_bytes_are_counted_before_downstream_parser():
    async def run():
        called = []

        async def downstream(scope, receive, send):
            called.append(await receive())

        middleware = LocalRequestLimits(downstream, max_bytes=10)
        scope = {"type": "http", "method": "POST", "scheme": "http", "headers": [(b"host", b"127.0.0.1")]}
        messages = iter(
            [
                {"type": "http.request", "body": b"123456", "more_body": True},
                {"type": "http.request", "body": b"78901", "more_body": False},
            ]
        )

        async def receive():
            return next(messages)

        sent = []

        async def send(message):
            sent.append(message)

        await middleware(scope, receive, send)
        assert not called
        assert sent[0]["status"] == 413
        assert middleware.active == 0

    asyncio.run(run())


def test_body_timeout_and_capacity_release_after_disconnect():
    async def run():
        async def downstream(*args):
            raise AssertionError("Body should never reach the app")

        middleware = LocalRequestLimits(downstream, max_active=1, body_timeout=0.01)
        scope = {"type": "http", "method": "POST", "scheme": "http", "headers": [(b"host", b"localhost")]}
        sent = []

        async def send(message):
            sent.append(message)

        async def slow_receive():
            await asyncio.sleep(1)

        await middleware(scope, slow_receive, send)
        assert sent[0]["status"] == 408
        assert middleware.active == 0
        middleware.active = 1
        sent.clear()
        await middleware(scope, slow_receive, send)
        assert sent[0]["status"] == 429
        middleware.active = 0

        async def disconnect():
            return {"type": "http.disconnect"}

        await middleware(scope, disconnect, send)
        assert middleware.active == 0

    asyncio.run(run())


def test_concurrent_request_capacity_recovers_when_first_request_finishes():
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()

        async def downstream(scope, receive, send):
            assert (await receive())["body"] == b"{}"
            entered.set()
            await release.wait()

        middleware = LocalRequestLimits(downstream, max_active=1)
        scope = {"type": "http", "method": "POST", "scheme": "http", "headers": [(b"host", b"localhost")]}

        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}

        sent = []

        async def send(message):
            sent.append(message)

        first = asyncio.create_task(middleware(scope, receive, send))
        await entered.wait()
        await middleware(scope, receive, send)
        assert sent[0]["status"] == 429
        release.set()
        await first
        sent.clear()
        await middleware(scope, receive, send)
        assert not sent
        assert middleware.active == 0

    asyncio.run(run())


def test_larger_project_limit_applies_only_to_explicit_paths():
    async def run():
        received = []

        async def downstream(scope, receive, send):
            received.append((await receive())["body"])

        middleware = LocalRequestLimits(downstream, max_bytes=10, path_limits={"/projects/open": 20})
        for path, expected in [
            ("/projects/open", None),
            ("/projects/open/other", 413),
            ("/api/content", 413),
        ]:
            scope = {
                "type": "http",
                "method": "POST",
                "path": path,
                "scheme": "http",
                "headers": [(b"host", b"localhost")],
            }
            sent = []

            async def receive():
                return {"type": "http.request", "body": b"123456789012345", "more_body": False}

            async def send(message, target=sent):
                target.append(message)

            await middleware(scope, receive, send)
            assert (sent[0]["status"] if sent else None) == expected
        assert received == [b"123456789012345"]

    asyncio.run(run())

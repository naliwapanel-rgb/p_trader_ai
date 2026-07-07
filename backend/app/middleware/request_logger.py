import time
import uuid

from fastapi import Request


async def request_logger_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)

    print(
        f"[{request_id}] "
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"time={process_time}ms"
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-MS"] = str(process_time)

    return response
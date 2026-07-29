from fastapi import (
    Request,
)


SECURITY_HEADERS = {
    "Strict-Transport-Security": (
        "max-age=31536000; "
        "includeSubDomains"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": (
        "camera=(), "
        "geolocation=(), "
        "microphone=()"
    ),
    "Content-Security-Policy": (
        "default-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'none'"
    ),
    (
        "X-Permitted-"
        "Cross-Domain-Policies"
    ): "none",
}


async def security_headers_middleware(
    request: Request,
    call_next,
):
    response = await call_next(
        request
    )

    for name, value in (
        SECURITY_HEADERS.items()
    ):
        response.headers[name] = value

    return response

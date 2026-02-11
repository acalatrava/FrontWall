from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Extract the real client IP from proxy headers.

    Priority: CF-Connecting-IP (Cloudflare) > X-Real-IP (Nginx/NPM)
    > first entry in X-Forwarded-For > direct connection IP.
    """
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "0.0.0.0"

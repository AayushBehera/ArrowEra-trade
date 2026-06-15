from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "arrowera_http_requests_total", "HTTP requests", ["method", "path", "status"]
)
REQUEST_DURATION = Histogram(
    "arrowera_http_request_duration_seconds", "HTTP request duration", ["method", "path"]
)

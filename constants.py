MAX_CONCURRENT_PER_DOMAIN = 2
TIMEOUT_SECONDS = 20
DELAY_BETWEEN_REQUESTS = 0.5

ALLOWED_CONTENT_TYPES = [
    'text/html',
    'application/xhtml+xml',
    'application/xml',
    'text/xml'
]

HTTP_STATUS_CODES = {
    200: "OK",
    301: "Moved Permanently",
    302: "Found",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    503: "Service Unavailable"
}
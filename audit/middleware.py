from .context import audit_request


class AuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with audit_request(request):
            return self.get_response(request)

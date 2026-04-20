import base64
from django.contrib.auth import authenticate
from django.http import HttpResponse


class DjangoBasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        auth = request.META.get("HTTP_AUTHORIZATION")

        if not auth or not auth.startswith("Basic "):
            return self.unauthorized()

        try:
            encoded = auth.split(" ")[1]
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return self.unauthorized()

        user = authenticate(username=username, password=password)

        if user is None or not user.is_active:
            return self.unauthorized()

        request.user = user
        return self.get_response(request)

    def unauthorized(self):
        resp = HttpResponse("Unauthorized", status=401)
        resp["WWW-Authenticate"] = 'Basic realm="CardDAV"'
        return resp
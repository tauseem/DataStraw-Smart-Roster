from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import FileResponse
from django.urls import re_path


def frontend_app(request, *args, **kwargs):
    return FileResponse(
        open(settings.WHITENOISE_ROOT / "index.html", "rb"),
        content_type="text/html",
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    re_path(r"^(?!api/|admin/).*$", frontend_app),
]
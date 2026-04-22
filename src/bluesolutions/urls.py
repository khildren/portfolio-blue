from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/help/', admin.site.admin_view(
        TemplateView.as_view(template_name='admin/help.html')
    ), name='admin_help'),
    path('admin/', admin.site.urls),
    path('portfolio/', include('apps.portfolio.urls', namespace='portfolio')),
    path('', include('apps.main.urls', namespace='main')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

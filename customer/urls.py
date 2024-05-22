from django.urls import path

from django.conf.urls.static import static
from HelloDjango import settings
from .views import search_result, show_all, all_drivers

urlpatterns = [
    path('search/', search_result),
    path('all_drivers/', all_drivers),
    path('show_all/', show_all),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
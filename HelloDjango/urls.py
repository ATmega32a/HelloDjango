"""carrier_viberbot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from botviber.views import viber_events, set_driver, enable_client, make_all_drivers, \
    make_all_clients, unblocking_car_for_all_selected_drivers, enable_car, \
    blocking_car_for_all_selected_drivers
from HelloDjango import settings
from customer.views import all_drivers, choice_documents

urlpatterns = [
                  path('admin/customer/driver/', csrf_exempt(all_drivers)),
                  path('choice_doc/', csrf_exempt(choice_documents)),
                  path("admin/", admin.site.urls),
                  path('', include('customer.urls')),
                  path('664cbd05f0b26bc3', csrf_exempt(viber_events)),

                  path('driver_or_client/<str:subscriber_id>/<str:searched_phones>/<str:search_by>', set_driver),
                  path('driver_or_client/<str:subscriber_id>//<str:search_by>', set_driver),

                  path('enable_client/<str:subscriber_id>/<str:searched_phones>/<str:search_by>', enable_client),
                  path('enable_client/<str:subscriber_id>//<str:search_by>', enable_client),
                  path('enable_car/<str:subscriber_id>/<str:car_number>/<str:searched_phones>/<str:search_by>',
                       enable_car),
                  path('enable_car/<str:subscriber_id>/<str:car_number>//<str:search_by>', enable_car),

                  path('make_all_drivers/<str:searched_phones>/<str:search_by>', make_all_drivers),
                  path('make_all_drivers//<str:search_by>', make_all_drivers),

                  path('make_all_clients/<str:searched_phones>/<str:search_by>', make_all_clients),
                  path('make_all_clients//<str:search_by>', make_all_clients),

                  path('unlock_car_for_all_selected_drivers/<str:searched_phones>/<str:search_by>',
                       unblocking_car_for_all_selected_drivers),
                  path('unlock_car_for_all_selected_drivers//<str:search_by>', unblocking_car_for_all_selected_drivers),
                  path('lock_car_for_all_selected_drivers/<str:searched_phones>/<str:search_by>',
                       blocking_car_for_all_selected_drivers),
                  path('lock_car_for_all_selected_drivers//<str:search_by>', blocking_car_for_all_selected_drivers),

                  # ****************************************************************************************************

                  path('make_all_drivers/', make_all_drivers),
                  path('make_all_drivers/<str:searched_phones>', make_all_drivers),

                  path('make_all_clients/', make_all_clients),
                  path('make_all_clients/<str:searched_phones>', make_all_clients)

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
admin.site.site_header = "ТТК Маруся"
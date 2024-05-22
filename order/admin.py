from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import QuerySet

from order.models import Order, Questionnaire, LicensingQuestionnaire, WaybillEntry, WaybillJournal, WaybillNote, Car, \
    Organization, Doctor, Mechanic, Dispatcher, SelfEmployed, DCard


@admin.register(Order)
class ViewOrder(admin.ModelAdmin):
    list_display = (
        'owner',
        'service',
        'tariff',
        'from_location',
        'to_location',
        'comment',
        'order_cost',
        'ord_success'
    )


@admin.register(Questionnaire)
class ViewQuestionnaire(admin.ModelAdmin):
    list_display = (
        'applicant',
        'city',
        'name',
        'phone',
        'car_number',
        'car_model',
        'number_of_seats',
        'car_year_made',
        'car_type',
        'car_color'
    )


@admin.register(LicensingQuestionnaire)
class ViewLicensingQuestionnaire(admin.ModelAdmin):
    list_display = (
        'surname',
        'name',
        'phone',
        'car_brand',
        'car_model',
        'car_number',
    )


@admin.register(WaybillEntry)
class ViewWaybillEntry(admin.ModelAdmin):
    list_display = (
        'tr_reg_num',
        'surname',
        'name',
        'patronymic',
        'tr_mark',
        'tr_model',
        'ser_doc',
        'num_doc',
    )


@admin.register(WaybillNote)
class ViewWaybillNote(admin.ModelAdmin):
    list_display = (
        'number',
        'tr_reg_num',
        'surname',
        'name',
        'patronymic',
        'tr_mark',
        'tr_model',
        'date',
        'time',
        'time_zone',
        'start_tech_state',
        'odometer_value',
        'arrival_time',
        'finish_tech_state',
        'final_odometer_value',
        'fuel_residue',
        'special_marks',
        'mechanic_signature',
        'driver_signature'
    )


@admin.register(Car)
class ViewCar(admin.ModelAdmin):
    list_display = (
        'car_brand',
        'car_model',
        'car_number',
        'vin_code',
        'permission_create_date',
#        'permission_cancel_date',
        'Дата_аннулирования_разрешения',
        'car_licensing_number',
        'revoke_license_button',
        'vehicle_class',
        'blocked_button',
        'is_available',
        'link_for_payment',
        'permission_pdf'
    )
    search_fields = ['car_brand', 'car_model', 'car_number', 'car_licensing_number']
    exclude = ('color_for_license',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('car_blocking/<str:car_pk>',
                 self.admin_site.admin_view(self.car_blocking),
                 name='car_pk'
                 ),
            path('revoke_lic/<str:car_pk_lic>',
                 self.admin_site.admin_view(self.revoke_license),
                 name='car_pk_lic'
                 )
        ]
        return custom_urls + urls

    @staticmethod
    def car_blocking(request, car_pk):
        if request.user.is_superuser:
            car = Car.objects.get(pk=car_pk)
            if car.is_available:
                car.is_available = False
            else:
                car.is_available = True
            car.save()
        return redirect('/admin/order/car')

    @staticmethod
    def revoke_license(request, car_pk_lic):
        if request.user.is_superuser:
            car = Car.objects.get(pk=car_pk_lic)
            if car.is_active_license:
                car.is_active_license = False
            else:
                car.is_active_license = True
            car.permission_cancel_date = timezone.now()
            car.save()
        return redirect('/admin/order/car')

    def blocked_button(self, obj):
        car = Car.objects.get(pk=obj.pk)
        if car.is_available:
            text = "Заблокировать авто"
        else:
            text = "Разблокировать авто"
        return format_html('<a class="button" href="{}">' + text + '</a>', reverse('admin:car_pk', args=[obj.pk]))

    def revoke_license_button(self, obj):
        car = Car.objects.get(pk=obj.pk)
        if car.is_active_license:
            text = "Аннулировать"
            return format_html('<a class="button" href="{}">' + text + '</a>', reverse('admin:car_pk_lic', args=[obj.pk]))
        else:
            text = "Разрешить"
            return format_html('<a class="button" style="background-color: red" href="{}">' + text + '</a>', reverse('admin:car_pk_lic', args=[obj.pk]))
        

    blocked_button.short_description = 'Блокировка автомобиля'
    revoke_license_button.short_description = 'Статус лицензии'


@admin.register(Doctor)
class ViewDoctor(admin.ModelAdmin):
    list_display = (
        'surname',
        'name',
        'patronymic',
        'EDS_number',
        'EDS_valid_from',
        'EDS_valid_to',
        'EDS_address'
    )


@admin.register(Mechanic)
class ViewMechanic(admin.ModelAdmin):
    list_display = (
        'surname',
        'name',
        'patronymic',
        'EDS_number',
        'EDS_valid_from',
        'EDS_valid_to',
        'EDS_address'
    )


@admin.register(Dispatcher)
class ViewDispatcher(admin.ModelAdmin):
    list_display = (
        'surname',
        'name',
        'patronymic',
        'EDS_number',
        'EDS_valid_from',
        'EDS_valid_to',
        'EDS_address'
    )


@admin.register(Organization)
class ViewOrganization(admin.ModelAdmin):
    list_display = (
        'organizational_and_legal_forms',
        'name',
        'legal_address',
        'contract_number',
        'EDS_org_name',
        'EDS_valid_from',
        'EDS_valid_to',
        'INN',
        'OGRN',
        'doctor',
        'mechanic'
    )


class SelfEmployedInline(admin.TabularInline):
    model = Car.permission_related_pairs.through
    extra = 0


class ViewSelfEmployed(admin.ModelAdmin):
    inlines = [SelfEmployedInline]
    
    list_display = (
        'user',
        'name',
        'legal_address',
        'contract_number',
        'EDS_org_name',
        'EDS_valid_from',
        'EDS_valid_to',
        'INN',
        'OGRN',
        # 'SNILS',
        'doctor',
        'mechanic'
    )
    search_fields = ['user']


admin.site.register(SelfEmployed, ViewSelfEmployed)


@admin.register(DCard)
class ViewDCard(admin.ModelAdmin):
    list_display = (
        "owner",
        # "checking_dc",
        'change_checked_dc_button',
        'change_tech_inspection_button',
        "car",
        "vin_code",
        "dc_expiration_date",
        "series_and_number_pts"
    )
    search_fields = ["vin_code", "owner__phone"]
    actions = ['enable_dc_blocking', 'disable_dc_blocking', 'confirm_tech_inspection', 'cancel_tech_inspection']
    exclude = ['is_active']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('change_checked_dc/<str:dc_pk>',
                 self.admin_site.admin_view(self.dc_blocking),
                 name='dc_pk'
                 ),
            path('change_tech_inspection/<str:ti_pk>',
                 self.admin_site.admin_view(self.ti_blocking),
                 name='ti_pk'
                 )
        ]
        return custom_urls + urls

    @staticmethod
    def dc_blocking(request, dc_pk):
        if request.user.is_superuser:
            dc = DCard.objects.get(pk=dc_pk)
            if dc.checking_dc:
                dc.checking_dc = False
            else:
                dc.checking_dc = True
            dc.save()
        return redirect('/admin/order/dcard')

    @staticmethod
    def ti_blocking(request, ti_pk):
        if request.user.is_superuser:
            dc = DCard.objects.get(pk=ti_pk)
            if dc.is_active:
                dc.is_active = False
            else:
                dc.is_active = True
            dc.save()
        return redirect('/admin/order/dcard')

    def change_checked_dc_button(self, obj):
        dc = DCard.objects.get(pk=obj.pk)
        if dc.checking_dc:
            text = "С проверкой"
        else:
            text = "Без проверки"
        return format_html('<a class="button" href="{}">' + text + '</a>', reverse('admin:dc_pk', args=[obj.pk]))

    def change_tech_inspection_button(self, obj):
        dc = DCard.objects.get(pk=obj.pk)
        if dc.is_active:
            text = "Заблокировать"
        else:
            text = "Разблокировать"
        return format_html('<a class="button" href="{}">' + text + '</a>', reverse('admin:ti_pk', args=[obj.pk]))

    def enable_dc_blocking(self, request, queryset: QuerySet):
        if request.user.is_superuser:
            self.set_value_for_dc_checking(queryset, True)

    def disable_dc_blocking(self, request, queryset: QuerySet):
        if request.user.is_superuser:
            self.set_value_for_dc_checking(queryset, False)

    def confirm_tech_inspection(self, request, queryset: QuerySet):
        if request.user.is_active:
            self.set_value_for_tech_inspection(queryset, True)

    def cancel_tech_inspection(self, request, queryset: QuerySet):
        if request.user.is_active:
            self.set_value_for_tech_inspection(queryset, False)

    @staticmethod
    def set_value_for_dc_checking(queryset: QuerySet, state):
        for dc in queryset:
            dc.checking_dc = state
            dc.save()

    @staticmethod
    def set_value_for_tech_inspection(queryset: QuerySet, state):
        for dc in queryset:
            dc.is_active = state
            dc.save()

    change_checked_dc_button.short_description = 'Проверка техосмотра'
    enable_dc_blocking.short_description = "Добавить проверку техосмотра"
    disable_dc_blocking.short_description = "Отменить проверку техосмотра"
    change_tech_inspection_button.short_description = "Блокировка ДК"
    confirm_tech_inspection.short_description = "Разблокировать диагностическую карту"
    cancel_tech_inspection.short_description = "Заблокировать диагностическую карту"
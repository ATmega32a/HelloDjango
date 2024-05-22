from django.shortcuts import redirect, render
from django.urls import reverse, path
from django.utils.html import format_html

from customer.models import Subscriber, BlockedSubscribers
from customer.models import Driver

from django.db.models import QuerySet
from django.contrib import admin

from order.models import Car, WaybillEntry

admin.site.register(Driver)


@admin.register(Subscriber)
class ViewSubscriber(admin.ModelAdmin):
    list_display = (
        'image_img',
        'name',
        'phone',
        'is_driver',
        'СНИЛС',
        'snils_check',

        'car_view',
        'lic_number_view',
        'car_enable',
        'get_documents',
    )

    exclude = ('color_for_snils',)

    search_fields = ['phone', 'name', 'SNILS']
    actions = ['add_driver_law', 'remove_driver_law']

    def add_driver_law(self, request, queryset: QuerySet):
        if request.user.is_superuser:
            self.set_driver_or_client(queryset, True)

    def remove_driver_law(self, request, queryset: QuerySet):
        if request.user.is_superuser:
            self.set_driver_or_client(queryset, False)

    @staticmethod
    def set_driver_or_client(queryset: QuerySet, state):
        for user in queryset:
            user.is_driver = state
            user.save()

    @staticmethod
    def get_car(obj):
        waybill_entry = WaybillEntry.objects.get(applicant=obj.pk)
        car_number = waybill_entry.tr_reg_num
        car = Car.objects.get(car_number=car_number)
        return car

    @staticmethod
    def car_enabling_or_disabling(request, pk):
        if request.user.is_superuser:
            car = Car.objects.get(car_number=WaybillEntry.objects.get(applicant=pk).tr_reg_num)
            if car.is_available:
                car.is_available = False
            else:
                car.is_available = True
            car.save()
        return redirect('/admin/customer/subscriber')

    @staticmethod
    def show_form_choice_documents(request, pk_d):
        if request.user.is_superuser:
            return render(request, 'html-templates/choice_docs_modal_form.html', {
                    'pk_d': pk_d
                })
        return redirect('/admin/customer/subscriber')

    @staticmethod
    def snils_is_checked(request, pk_s):
        if request.user.is_superuser:
            subscriber = Subscriber.objects.get(pk=pk_s)
            if subscriber.snils_verified:
                subscriber.snils_verified = False
            else:
                subscriber.snils_verified = True
            subscriber.save()
        return redirect('/admin/customer/subscriber')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('car_enabling_or_disabling/<str:pk>',
                 self.admin_site.admin_view(self.car_enabling_or_disabling),
                 name='pk'),
            path('show_form_choice_documents/<str:pk_d>',
                 self.admin_site.admin_view(self.show_form_choice_documents),
                 name='pk_d'),
            path('snils_is_checked/<str:pk_s>',
                 self.admin_site.admin_view(self.snils_is_checked),
                 name='pk_s')
        ]
        return custom_urls + urls

    def car_view(self, obj):
        car = self.get_car(obj)
        return format_html(f'<a href="/admin/order/car/{car.pk}/change/">{car}</a>')

    def lic_number_view(self, obj):
        car = self.get_car(obj)
        return format_html(car.car_licensing_number)

    def car_enable(self, obj):
        car = self.get_car(obj)
        if Subscriber.objects.get(pk=obj.pk).is_driver:
            if car.is_available:
                text = "Заблокировать авто"
            else:
                text = "Разблокировать авто"
            return format_html('<a class="button" href="{}">' + text + '</a>', reverse('admin:pk', args=[obj.pk]))

    def snils_check(self, obj):
        if Subscriber.objects.get(pk=obj.pk).SNILS == "":
            return ""
        if Subscriber.objects.get(pk=obj.pk).snils_verified:
            return "Подтверждено"
        else:
            return format_html('<a class="button" href="{}">Подтвердить</a>', reverse('admin:pk_s', args=[obj.pk]))

    def get_documents(self, obj):
        text = "Выбрать из списка..."
        return format_html(
            f'<a class="button" href="/admin/customer/subscriber/show_form_choice_documents/' + str(obj.pk)
            + '#openModal">' + text + '</a>', reverse('admin:pk_d', args=[obj.pk]))

    get_documents.short_description = "Документы"
    car_enable.short_description = 'Блокировка автомобиля'
    car_enable.allow_tags = True

    snils_check.short_description = 'Проверка СНИЛС'
    snils_check.allow_tags = True

    car_view.short_description = 'Автомобиль'
    car_view.allow_tags = True
    lic_number_view.short_description = 'Номер лицензии'
    lic_number_view.allow_tags = True

    add_driver_law.short_description = "Добавить права водителя"
    remove_driver_law.short_description = "Удалить права водителя"

    ordering = ['-last_modify_date', '-snils_verified']


@admin.register(BlockedSubscribers)
class ViewBlockedSubscribers(ViewSubscriber):

    exclude = ('car_enable', 'get_documents')

    @staticmethod
    def car_enabling_or_disabling(request, pk):
        if request.user.is_superuser:
            car = Car.objects.get(car_number=WaybillEntry.objects.get(applicant=pk).tr_reg_num)
            if car.is_available:
                car.is_available = False
            else:
                car.is_available = True
            car.save()
        return redirect('/admin/customer/blockedsubscribers')

    @staticmethod
    def show_form_choice_documents(request, pk_d):
        if request.user.is_superuser:
            return render(request, 'html-templates/choice_docs_modal_form.html', {
                    'pk_d': pk_d
                })
        return redirect('/admin/customer/blockedsubscribers')

    @staticmethod
    def snils_is_checked(request, pk_sa):
        if request.user.is_superuser:
            subscriber = Subscriber.objects.get(pk=pk_sa)
            subscriber.snils_verified = True
            subscriber.save()
        return redirect('/admin/customer/blockedsubscribers')

    @staticmethod
    def snils_is_rejected(request, pk_sd):
        if request.user.is_superuser:
            subscriber = Subscriber.objects.get(pk=pk_sd)
            subscriber.snils_verified = False
            subscriber.save()
        return redirect('/admin/customer/blockedsubscribers')

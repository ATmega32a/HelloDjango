from datetime import datetime
from django.db import models
from django.utils import timezone
from django.utils.html import format_html


class Subscriber(models.Model):
    user = models.CharField(max_length=30, db_index=True, unique=True)
    name = models.CharField("Имя в Viber", max_length=256, blank=True)
    date_sub = models.DateTimeField(verbose_name="Дата подписки", default=timezone.now)
    image = models.CharField("Аватар", max_length=450, blank=True)
    region = models.CharField(max_length=2, blank=True, verbose_name="Страна")
    phone = models.CharField(max_length=14, verbose_name="Телефон", blank=True)
    source = models.CharField("Источник", max_length=128, blank=True)
    is_admin = models.BooleanField("Администратор", default=False)
    in_use = models.BooleanField("Подписан", default=True)
    is_driver = models.BooleanField("Водитель", default=True)
    is_enable = models.BooleanField("Включен", default=True)

    SNILS = models.CharField(verbose_name="СНИЛС", max_length=14, blank=True, default='')
    color_for_snils = models.CharField(max_length=7, default="#FFFFFF")
    snils_verified = models.BooleanField("СНИЛС проверен", default=False)
    last_modify_date = models.DateTimeField(verbose_name="Дата последнего обновления", default=timezone.now)

    objects = models.Manager()

    __last_saved_snils = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__last_saved_snils = self.SNILS

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.SNILS != self.__last_saved_snils:
            self.color_for_snils = '#FFAF33'
            self.snils_verified = False
            self.last_modify_date = datetime.now()

        if self.snils_verified:
            self.color_for_snils = '#FFFFFF'
        else:
            self.color_for_snils = '#FFAF33'

        super(Subscriber, self).save(force_insert, force_update, *args, **kwargs)
        self.__last_saved_snils = self.SNILS

    def СНИЛС(self):
        if self.SNILS is not None:
            return format_html(f'<span style="background: {self.color_for_snils};">{self.SNILS}</span>')
        else:
            return self.SNILS

    def __str__(self):
        return str(self.name) + ", tel: " + str(self.phone)

    def image_img(self):
        if self.image:
            from django.utils.safestring import mark_safe
            return mark_safe('<img src = "%s" width="30"/>' % self.image)
        else:
            return "Нет Аватара"

    image_img.short_description = "Аватар"
    image_img.allow_tags = True

    @staticmethod
    def save_user(subs, source="источник"):
        if not Subscriber.objects.filter(user=subs.id):
            if not subs.avatar:
                p, _ = Subscriber.objects.update_or_create(user=subs.id, region=subs.country,
                                                           name=subs.name, source=source)
            else:
                p, _ = Subscriber.objects.update_or_create(user=subs.id, region=subs.country,
                                                           name=subs.name, image=subs.avatar, source=source)
        else:
            usr = Subscriber.objects.get(user=subs.id)
            usr.in_use = True
            usr.save()

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        ordering = ['-snils_verified']


class Driver(models.Model):
    Dri = "Driver"
    Category = [
        (Dri, "Водители"),
    ]
    managers = models.CharField("Водители", max_length=20, choices=Category, default=Dri, unique=True)
    inuse = models.ManyToManyField(Subscriber, verbose_name="Список Водителей Маруси", blank=True)

    class Meta:
        verbose_name = "Водитель"
        verbose_name_plural = "Водители"

    def __str__(self):
        return self.managers


class BlockedSubscribersManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_driver=False)


class BlockedSubscribers(Subscriber):
    objects = BlockedSubscribersManager()

    class Meta:
        proxy = True

        verbose_name = "Заблокированный водитель"
        verbose_name_plural = "Заблокированные водители"

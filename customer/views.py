from time import sleep

from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import render, redirect

import order
from botviber.handler import waybill_build, save_waybill_to_journal
from botviber.utils.parsing_utilities import parse_car_number
from order.models import WaybillEntry, Car, WaybillNote
from .models import Subscriber


def sort_by_name(s):
    return s.name


def subscriber_info(subscribers: []):
    counter = 0
    names_drivers = []
    surnames_drivers = []
    tr_marks = []
    tr_models = []
    tr_reg_nums = []
    lic_numbers = []
    cars = []
    for s in subscribers:
        lq = WaybillEntry.objects.filter(applicant=s)
        if lq.exists():
            counter += 1
            lq_obj = lq.get()
            names_drivers.append(lq_obj.name)
            surnames_drivers.append(lq_obj.surname)
            car_filter = Car.objects.filter(car_number=lq_obj.tr_reg_num)
            if car_filter.exists():
                cars.append(car_filter.get())
            else:
                cars.append("-")

            if len(lq_obj.tr_mark + " " + lq_obj.tr_model) > 15:
                tr_marks.append(lq_obj.tr_mark)
                tr_models.append(lq_obj.tr_model)
            else:
                tr_marks.append(lq_obj.tr_mark + " " + lq_obj.tr_model)
                tr_models.append("")
            tr_reg_nums.append(lq_obj.tr_reg_num)
            lic_numbers.append(lq_obj.num_lic)
        else:
            counter += 1
            names_drivers.append(s.name)
            surnames_drivers.append("-")
            tr_marks.append("-")
            tr_models.append("")
            tr_reg_nums.append("-")
            lic_numbers.append("-")
            cars.append("-")
    return names_drivers, surnames_drivers, tr_marks, tr_models, tr_reg_nums, lic_numbers, counter, cars


def search_result(request):
    req_get = request.GET
    query = req_get.get('q')
    search_by = req_get['search_by']
    subscribers = Subscriber.objects.all()
    set_subscribers = set()
    searched_phones = set()
    set_ws_duplicate = set()
    found_subscribers = []
    text = ''
    names = str(query).split('%2C')
    searched_phones_subscribers_str = ''
    list_of_filters = []

    if query != '':
        for name in names:
            if name == '':
                continue
            name = name.strip()
            try:
                if search_by == 'by_name':
                    list_of_filters = filter_by_name(WaybillEntry, name)
                elif search_by == 'by_surname':
                    list_of_filters = filter_by_surname(WaybillEntry, name)
                elif search_by == 'by_phone':
                    list_of_filters.append(WaybillEntry.objects.filter(phone__contains=name))
                elif search_by == 'by_lic_number':
                    list_of_filters.append(WaybillEntry.objects.filter(num_lic__contains=name))
                elif search_by == 'by_car':
                    list_of_filters = filter_by_car(WaybillEntry, name)

                for lq_filter in list_of_filters:
                    if lq_filter.exists():
                        found_subscribers = set_found_subscribers(searched_phones, set_subscribers, set_ws_duplicate,
                                                                  lq_filter.get().applicant)
                        response(request, search_by, subscribers, searched_phones_subscribers_str,
                                 subscriber_info(found_subscribers))

            except MultipleObjectsReturned:
                lq_find_list = []
                for lq_find in WaybillEntry.objects.all():
                    if search_by == 'by_name':
                        lq_find_list.append((lq_find.name, lq_find.applicant))
                    elif search_by == 'by_surname':
                        lq_find_list.append((lq_find.surname, lq_find.applicant))
                    elif search_by == 'by_phone':
                        lq_find_list.append((lq_find.phone, lq_find.applicant))
                    elif search_by == 'by_lic_number':
                        lq_find_list.append((lq_find.num_lic, lq_find.applicant))
                    elif search_by == 'by_car':
                        lq_find_list.append((lq_find.tr_mark, lq_find.applicant))
                        lq_find_list.append((lq_find.tr_model, lq_find.applicant))
                        lq_find_list.append((lq_find.tr_reg_num, lq_find.applicant))
                    for lq_find_field in lq_find_list:
                        if lq_find_field[0].strip().lower().__contains__(name.strip().lower()):
                            s = lq_find_field[1]
                            set_ws_duplicate.add(s)
                            searched_phones.add(s.phone)
                            found_subscribers = [*set_ws_duplicate]
                            searched_phones.add(s.phone)

        found_subscribers.sort(key=sort_by_name)
        for searched_name in searched_phones:
            searched_phones_subscribers_str += searched_name + " "
        if len(found_subscribers) == 0:
            searched_phones_subscribers_str = ''
            text = "По вашему запросу ничего не найдено"
    else:
        searched_phones_subscribers_str = ''
        text = "Вы не ввели поисковый запрос!"
    return response(request, search_by, found_subscribers, searched_phones_subscribers_str,
                    subscriber_info(found_subscribers), text)


def filter_by_name(model, name):
    list_of_filters = []
    if model.objects.filter(name__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(name__contains=name.lower()))
    elif model.objects.filter(name__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(name__contains=name.upper()))
    elif model.objects.filter(name__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(name__contains=name.capitalize()))
    return list_of_filters


def filter_by_surname(model, name):
    list_of_filters = []
    if model.objects.filter(surname__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(surname__contains=name.lower()))
    elif model.objects.filter(surname__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(surname__contains=name.upper()))
    elif model.objects.filter(surname__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(surname__contains=name.capitalize()))
    return list_of_filters


def filter_by_car(model, name):
    list_of_filters = []
    if model.objects.filter(tr_mark__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(tr_mark__contains=name.lower()))
    elif model.objects.filter(tr_mark__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(tr_mark__contains=name.upper()))
    elif model.objects.filter(tr_mark__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(tr_mark__contains=name.capitalize()))

    elif model.objects.filter(tr_model__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(tr_model__contains=name.lower()))
    elif model.objects.filter(tr_model__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(tr_model__contains=name.upper()))
    elif model.objects.filter(tr_model__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(tr_model__contains=name.capitalize()))

    elif model.objects.filter(tr_reg_num__contains=name.lower()).exists():
        list_of_filters.append(model.objects.filter(tr_reg_num__contains=name.lower()))
    elif model.objects.filter(tr_reg_num__contains=name.upper()).exists():
        list_of_filters.append(model.objects.filter(tr_reg_num__contains=name.upper()))
    elif model.objects.filter(tr_reg_num__contains=name.capitalize()).exists():
        list_of_filters.append(model.objects.filter(tr_reg_num__contains=name.capitalize()))

    elif model.objects.filter(tr_reg_num__contains=parse_car_number(name)[0]).exists():
        list_of_filters.append(model.objects.filter(tr_reg_num__contains=parse_car_number(name)[0]))

    elif model.objects.filter(tr_reg_num__contains=parse_car_number(name)[1]).exists():
        list_of_filters.append(model.objects.filter(tr_reg_num__contains=parse_car_number(name)[1]))

    return list_of_filters


def set_found_subscribers(searched_phones, set_subscribers, set_ws_duplicate, subscriber):
    set_subscribers.add(subscriber)
    set_ws_duplicate.add(subscriber)
    searched_phones.add(subscriber.phone)
    found_subscribers = [*set_ws_duplicate]
    return found_subscribers


def response(request, search_by, subscribers, searched_phones_subscribers_str, info_car_licensing, text=''):
    number_of_subscribers = info_car_licensing[6]
    counter = []
    for i in range(int(number_of_subscribers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')
    subscribers_info = zip(subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                           info_car_licensing[3], info_car_licensing[4], info_car_licensing[5], info_car_licensing[7])
    return render(request, "html-templates/get-user-list.html",
                  {"subscribers": subscribers_info,
                   "searched_phones": searched_phones_subscribers_str,
                   "counter": counter,
                   "number_of_subscribers": number_of_subscribers,
                   "checked": search_by,
                   "text": text
                   })


def show_all(request):
    searched_phones_subscribers_str = ''
    subscribers = Subscriber.objects.all()
    for s in subscribers:
        searched_phones_subscribers_str += s.phone + " "
    number_of_subscribers = subscribers.count()
    counter = []
    for i in range(int(number_of_subscribers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')
    info_car_licensing = subscriber_info(subscribers)
    return response(request, "by_name", subscribers, searched_phones_subscribers_str,
                    info_car_licensing)


def all_drivers(request):
    searched_phones_subscribers_str = ''
    subscribers = Subscriber.objects.filter(is_driver=True)
    list_of_subscribers = []
    for subscriber in subscribers:
        searched_phones_subscribers_str += subscriber.phone + " "
        if WaybillEntry.objects.filter(applicant=subscriber).exists():
            list_of_subscribers.append(subscriber)

    number_of_subscribers = len(list_of_subscribers)
    counter = []
    for i in range(int(number_of_subscribers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')
    info_car_licensing = subscriber_info(subscribers)
    list_of_subscribers.sort(key=sort_by_name)
    return response(request,
                    "by_name",
                    subscribers,
                    searched_phones_subscribers_str,
                    info_car_licensing)


def choice_documents(request):
    req_get = request.GET
    choice_type_doc = req_get['choice_type_doc']
    type_doc = choice_type_doc.split('_')[0]
    pk_d = choice_type_doc.split('_')[1]
    subscriber = Subscriber.objects.get(pk=pk_d)
    vid = subscriber.user
    if type_doc == 'agreement':
        pass
    elif type_doc == 'waybill':
        odometer_value = req_get['odometer_value']
        try:
            wbe = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid))
            car = Car.objects.get(car_number=wbe.tr_reg_num)

            url_doc = waybill_build(vid=vid, odometer_value=odometer_value, car=car)[0]
            save_waybill_to_journal()

            WaybillNote.objects.create(applicant=wbe.applicant,
                                       organization=wbe.organization,
                                       number=wbe.number,
                                       id_client=wbe.id_client,
                                       surname=wbe.surname,
                                       name=wbe.name,
                                       patronymic=wbe.patronymic,
                                       ser_doc=wbe.ser_doc,
                                       num_doc=wbe.num_doc,
                                       num_lic=wbe.num_lic,
                                       kod_org_doc=wbe.kod_org_doc,
                                       tr_reg_num=wbe.tr_reg_num,
                                       tr_mark=wbe.tr_mark,
                                       tr_model=wbe.tr_model,
                                       odometer_value=wbe.odometer_value,
                                       date=wbe.date,
                                       time=wbe.time,
                                       time_zone=wbe.time_zone)
            sleep(2)
            return redirect(url_doc)
        except order.models.WaybillEntry.DoesNotExist:
            return redirect(f'/admin/order/waybillentry/add/?'
                            f'name={subscriber.name}&'
                            f'phone={subscriber.phone}&'
                            f'odometer_value={odometer_value}')
    return redirect('/admin/customer/subscriber')

from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from viberbot.api.messages.data_types.contact import Contact
from viberbot.api.messages.data_types.location import Location
from viberbot.api.viber_requests import ViberMessageRequest, ViberSubscribedRequest, ViberUnsubscribedRequest, \
    ViberConversationStartedRequest
from viberbot.api.messages import LocationMessage, PictureMessage, FileMessage, KeyboardMessage
from viberbot.api.messages import ContactMessage

from botviber.bot_config import viber
from botviber.buttons.buttons import info, share_phone, \
    main_menu_kb, refresh_menu_rich, waybill_form
from botviber.handler import location_handler, message_handler, set_order, picture_handler, car_management, \
    file_handler, set_edit_waybill_buttons
from customer import forms
from customer.models import Subscriber
from customer.views import subscriber_info
from order.models import Car, WaybillEntry


message_timestamp_dict = {}


def main_menu(viber_request):
    viber.send_messages(
        viber_request.user.id, [refresh_menu_rich(),
                                KeyboardMessage(
                                    keyboard=main_menu_kb(viber_request.user.id),
                                    min_api_version=6)]
    )


def sort_by_name(s):
    return s.name


def get_users(request):
    subscribers = Subscriber.objects.all()
    number_of_subscribers = Subscriber.objects.count()
    counter = []
    for i in range(int(number_of_subscribers)):
        if i % 2 == 0:
            counter.append('a')
        else:
            counter.append('b')

    return render(request, "html-templates/get-driver-list.html",
                  {
                      "subscribers": subscribers,
                      "number_of_subscribers": number_of_subscribers,
                      "counter": counter,
                      "checked": "by_name",
                      "text": ""
                  })


def set_driver(request, subscriber_id, searched_phones='', search_by='by_name'):
    def _sort_by_name(sub):
        return sub.name

    try:
        subscriber = Subscriber.objects.get(phone=str(subscriber_id))
        role = subscriber.is_driver
        if role:
            subscriber.is_driver = False
        else:
            subscriber.is_driver = True
        subscriber.save()
        current_subscribers = []
        phones = str(searched_phones).strip().split("%20")
        if searched_phones != '':
            for phone in phones:
                if phone == '':
                    continue
                current_subscribers.append(Subscriber.objects.get(phone=phone))
        else:
            for subscriber in Subscriber.objects.all():
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=_sort_by_name)
        info_car_licensing = subscriber_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4], info_car_licensing[5],
                               info_car_licensing[7])
        number_of_subscribers = info_car_licensing[6]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def enable_client(request, subscriber_id, searched_phones='', search_by='by_name'):
    try:
        subscriber = Subscriber.objects.get(phone=str(subscriber_id))
        state = subscriber.is_enable
        if state:
            subscriber.is_enable = False
        else:
            subscriber.is_enable = True
        subscriber.save()

        current_subscribers = []
        phones = str(searched_phones).strip().split("%20")
        if searched_phones != '':
            for phone in phones:
                if phone == '':
                    continue
                current_subscribers.append(Subscriber.objects.get(phone=phone))
        else:
            for subscriber in Subscriber.objects.all():
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = subscriber_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4], info_car_licensing[5],
                               info_car_licensing[7])
        number_of_subscribers = info_car_licensing[6]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def enable_car(request, subscriber_id, car_number, searched_phones='', search_by='by_name'):
    try:
        subscriber = Subscriber.objects.get(phone=str(subscriber_id))
        car = Car.objects.get(car_number=car_number)

        if car.is_available:
            car_management(subscriber.user, car_number, False)
        else:
            car_management(subscriber.user, car_number, True)

        current_subscribers = []
        phones = str(searched_phones).strip().split("%20")
        if searched_phones != '':
            for phone in phones:
                if phone == '':
                    continue
                current_subscribers.append(Subscriber.objects.get(phone=phone))
        else:
            for subscriber in Subscriber.objects.all():
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = subscriber_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4], info_car_licensing[5],
                               info_car_licensing[7])
        number_of_subscribers = info_car_licensing[6]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')

        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def make_all_clients_or_drivers(request, search_by, searched_phones, state):
    try:
        current_subscribers = []
        phones = str(searched_phones).strip().split("%20")
        if searched_phones != '':
            for phone in phones:
                if phone == '':
                    continue
                subscriber = Subscriber.objects.get(phone=phone)
                subscriber.is_driver = state
                subscriber.save()
                current_subscribers.append(subscriber)
        else:
            for subscriber in Subscriber.objects.all():
                subscriber.is_driver = state
                subscriber.save()
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = subscriber_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4], info_car_licensing[5],
                               info_car_licensing[7])
        number_of_subscribers = info_car_licensing[6]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')

        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def blocking_car(request, search_by, searched_phones, state):
    try:
        current_subscribers = []
        phones = str(searched_phones).strip().split("%20")
        cars = []
        if searched_phones != '':
            for phone in phones:
                if phone == '':
                    continue
                subscriber = Subscriber.objects.get(phone=phone)
                entry_objects_filter = WaybillEntry.objects.filter(applicant=subscriber)
                if entry_objects_filter.exists():
                    car_number = entry_objects_filter.get().tr_reg_num
                    car_filter = Car.objects.filter(car_number=car_number)
                    if car_filter.exists():
                        car = car_filter.get()
                        car.is_available = state
                        car.save()
                        cars.append(car)
                current_subscribers.append(subscriber)
        else:
            for subscriber in Subscriber.objects.all():
                entry_objects_filter = WaybillEntry.objects.filter(applicant=subscriber)
                if entry_objects_filter.exists():
                    car_number = entry_objects_filter.get().tr_reg_num
                    car_filter = Car.objects.filter(car_number=car_number)
                    if car_filter.exists():
                        car = car_filter.get()
                        car.is_available = state
                        car.save()
                        cars.append(car)
                current_subscribers.append(subscriber)
        user_form = forms.UserForm()
        current_subscribers.sort(key=sort_by_name)
        info_car_licensing = subscriber_info(current_subscribers)
        subscribers_info = zip(current_subscribers, info_car_licensing[0], info_car_licensing[1], info_car_licensing[2],
                               info_car_licensing[3], info_car_licensing[4], info_car_licensing[5], cars)
        number_of_subscribers = info_car_licensing[6]
        counter = []
        for i in range(int(number_of_subscribers)):
            if i % 2 == 0:
                counter.append('a')
            else:
                counter.append('b')
        return render(request, "html-templates/get-user-list.html",
                      {"subscribers": subscribers_info,
                       "form": user_form,
                       "searched_phones": searched_phones,
                       "number_of_subscribers": number_of_subscribers,
                       "counter": counter,
                       "checked": search_by,
                       "text": ""
                       })
    except Subscriber.DoesNotExist:
        return HttpResponseNotFound("<h2>User not found</h2>")


def make_all_drivers(request, searched_phones='', search_by='by_name'):
    return make_all_clients_or_drivers(request, search_by, searched_phones, True)


def make_all_clients(request, searched_phones='', search_by='by_name'):
    return make_all_clients_or_drivers(request, search_by, searched_phones, False)


def unblocking_car_for_all_selected_drivers(request, searched_phones='', search_by='by_name'):
    return blocking_car(request, search_by, searched_phones, True)


def blocking_car_for_all_selected_drivers(request, searched_phones='', search_by='by_name'):
    return blocking_car(request, search_by, searched_phones, False)


def viber_events(request):
    if request.method == "POST":
        if not viber.verify_signature(request.body, request.headers.get('X-Viber-Content-Signature')):
            return HttpResponse(status=403)
        viber_request = viber.parse_request(request.body)
        
        try:
            sender_id = viber_request.sender.id
        except AttributeError:
            sender_id = viber_request.user.id

        message_timestamp = viber_request.timestamp
        current_timestamp_list = message_timestamp_dict.get(sender_id)
        
        if current_timestamp_list is not None:
            if message_timestamp in current_timestamp_list:
                return HttpResponse(status=200)
            else:
                current_timestamp_list.append(message_timestamp)
        else:
            current_timestamp_list = [message_timestamp]
            
        if len(current_timestamp_list) >= 30:
            del current_timestamp_list[0]
            
        message_timestamp_dict.update(
            {sender_id: current_timestamp_list}
        )
        
        if isinstance(viber_request, ViberMessageRequest):
            message = viber_request.message
            if isinstance(message, LocationMessage):
                location = message.location
                if isinstance(location, Location):
                    vid = viber_request.sender.id
                    name = viber_request.sender.name
                    lat = location.latitude
                    lon = location.longitude
                    tracking_data = viber_request.message.tracking_data
                    location_handler(vid, name, lat, lon, tracking_data)
            elif isinstance(message, ContactMessage):
                contact = message.contact
                if isinstance(contact, Contact):
                    vid = viber_request.sender.id
                    num = contact.phone_number
                    sub = Subscriber.objects.get(user=vid)
                    sub.phone = '+' + num
                    sub.save()
                    if viber_request.message.tracking_data == "share-phone-number":

                        set_edit_waybill_buttons(vid, True)
                        viber.send_messages(vid,
                                            [waybill_form(vid=vid, number_button=None,
                                                          text="Регистрация нового пользователя\n\nПоочерёдно нажимайте на кнопки формы"
                                                               " регистрации и указывайте"
                                                               " соответствующие данные",
                                                          text_field="hidden")])
                    elif viber_request.message.tracking_data == "phone-number-for-support-letter":
                        viber.send_messages(vid, [info()])
                    else:
                        set_order(vid)
            elif isinstance(message, PictureMessage):
                picture_handler(viber_request)
            elif isinstance(message, FileMessage):
                file_handler(viber_request)
            else:
                message_handler(viber_request)
#                vid = viber_request.sender.id
                
#                if vid == 'PXiguHPVx8vHp6O/asKvcg==':
#                    message_handler(viber_request)
#                else:
#                    viber.send_messages(vid, TextMessage(text="Сервис недоступен. Ведутся технические работы"))
                
        elif isinstance(viber_request, ViberConversationStartedRequest):
            uid = viber_request.user.id
            name = viber_request.user.name
            if not viber_request.subscribed:
                Subscriber.save_user(viber_request.user, 'internet')
                viber.send_messages(uid, messages=[share_phone(name)])
            else:
                main_menu(viber_request)

        elif isinstance(viber_request, ViberSubscribedRequest):
            usr = Subscriber.objects.get(user=viber_request.user.id)
            usr.in_use = True
            usr.save()
            main_menu(viber_request)

        elif isinstance(viber_request, ViberUnsubscribedRequest):
            usr = Subscriber.objects.get(user=viber_request.user_id)
            usr.in_use = False
            usr.save()
        return HttpResponse(status=200)

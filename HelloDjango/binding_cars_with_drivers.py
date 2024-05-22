import os
import django

def binding_cars_with_drivers():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HelloDjango.settings")
    django.setup()
    from order.models import WaybillEntry
    from customer.models import Subscriber
    for subscriber in Subscriber.objects.all():
        for car in subscriber.cars.all():
            waybill_entry_filter = WaybillEntry.objects.filter(
                    applicant=subscriber)
            if waybill_entry_filter.exists():
                waybill_entry_filter.update(tr_reg_num=car.car_number,
                                            tr_mark=car.car_brand,
                                            tr_model=car.car_model,
                                            num_lic=car.car_licensing_number)
            else:
                waybill_entry = WaybillEntry.objects.create(
                    applicant=subscriber,
                    tr_reg_num=car.car_number,
                    tr_mark=car.car_brand,
                    tr_model=car.car_model,
                    num_lic=car.car_licensing_number)
                waybill_entry.save()
                
                
if __name__ == '__main__':
    binding_cars_with_drivers()

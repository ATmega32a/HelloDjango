from datetime import datetime, timedelta, timezone
from pathlib import Path
from fpdf import FPDF
from pikepdf import Pdf, Page, Rectangle

from botviber.utils.split_string_by_length import split_string_by_length
from HelloDjango.settings import MEDIA_ROOT
from threading import Thread

from customer.models import Subscriber
from order.models import WaybillEntry

import fitz


def szs(n):
    n = str(n)
    if len(n) == 1:
        return "0" + n
    return n


def render_pdf_template(
        vid=None,
        number=None,
        id_client=None,
        time=None,
        date=None,
        surname=None,
        name=None,
        patronymic=None,
        ser_doc=None,
        num_doc=None,
        snils=None,
        kod_org_doc=None,
        tr_mark=None,
        tr_reg_num=None,
        odometer_value=None,
        car_organization_name=None,
        car_organization_contract_number=None,
        car_organization_eds_valid_from=None,
        car_organization_eds_org_name=None,
        car_organization_eds_valid_to=None,
        car_organization_inn=None,
        car_organization_ogrn=None,

        car_organization_mechanic=None,
        car_organization_mechanic_eds_valid_from=None,
        car_organization_mechanic_eds_valid_to=None,
        car_organization_mechanic_eds_number=None,
        car_organization_mechanic_eds_address=None,

        car_organization_dispatcher=None,
        car_organization_dispatcher_eds_valid_from=None,
        car_organization_dispatcher_eds_valid_to=None,
        car_organization_dispatcher_eds_number=None,
        car_organization_dispatcher_eds_address=None,

        car_organization_doctor=None,
        car_organization_doctor_eds_valid_from=None,
        car_organization_doctor_eds_valid_to=None,
        car_organization_doctor_eds_number=None,
        car_organization_doctor_eds_address=None,

):
    full_name = surname + " " + name + " " + patronymic
    fio_driver = surname + " " + name[:1] + "." + patronymic[:1] + "."

    day = szs(date.split(".")[0])
    month = szs(date.split(".")[1])
    year = szs(date.split(".")[2])

    hours = szs(time.split("-")[0])
    minutes = szs(time.split("-")[1])
    time = hours + " : " + minutes
    date = day + "." + month + "." + year + " г."
   
    car_organization_eds_org_name_list = split_string_by_length(car_organization_eds_org_name, 45)
    array_car_organization_eds_org_name = text_output_in_several_lines(car_organization_eds_org_name_list, 92.5, 65, 7, 3)

    car_organization_name_list = split_string_by_length(car_organization_name, 66)
    array_car_organization_name = text_output_in_several_lines(car_organization_name_list, 131.5, 194, 9, 4)

    car_organization_mechanic_eds_address_list = split_string_by_length(car_organization_mechanic_eds_address, 48)
    array_car_organization_mechanic_eds_address = text_output_in_several_lines(car_organization_mechanic_eds_address_list, 338, 378.5, 6.5, 2)

    car_organization_dispatcher_eds_address_list = split_string_by_length(car_organization_dispatcher_eds_address, 48)
    array_car_organization_dispatcher_eds_address = text_output_in_several_lines(car_organization_dispatcher_eds_address_list, 92, 551.5, 6.5, 2)

    car_organization_doctor_eds_address_list = split_string_by_length(car_organization_doctor_eds_address, 48)
    array_car_organization_doctor_eds_address = text_output_in_several_lines(car_organization_doctor_eds_address_list, 92, 735.5, 6.5, 2)

    array = (
        *array_car_organization_eds_org_name,
        (car_organization_eds_valid_from, 135, 95.2),
        (car_organization_eds_valid_to, 186, 95.2),
        (car_organization_inn, 103, 134.1),
        (car_organization_ogrn, 189, 134.1),
        (date, 140, 103.1),
        (str(number), 450, 164),
        ("от " + day + "/" + month + "/" + year + " г.", 185, 180),
        (day + "/" + month + "/" + year + " г.", 395.5, 282),
        (time, 480, 282),
        (tr_mark, 166, 238),
        (str(id_client), 460, 248),
        (tr_reg_num, 166.1, 248),
        (full_name, 124.2, 257),
        (ser_doc + " " + num_doc, 145.5, 267),
        (kod_org_doc, 410, 267),
        (snils, 112.7, 275),
        (str(odometer_value), 478, 322),
        (fio_driver, 395, 446),
        (date, 380, 453.3),
        (time, 455, 453.3),
        *array_car_organization_name,
        (car_organization_mechanic, 338, 363),
        (car_organization_mechanic_eds_valid_from, 381, 369.5),
        (car_organization_mechanic_eds_valid_to, 430, 369.5),
        (car_organization_mechanic_eds_number, 385, 377.5),
        *array_car_organization_mechanic_eds_address,
        (car_organization_dispatcher, 92, 535),
        (car_organization_dispatcher_eds_valid_from, 134, 542.8),
        (car_organization_dispatcher_eds_valid_to, 185.5, 542.8),
        (car_organization_dispatcher_eds_number, 140, 550.7),
        *array_car_organization_dispatcher_eds_address,
        (time, 227, 501),
        (car_organization_doctor, 92, 719),
        (car_organization_doctor_eds_valid_from, 134, 726.5),
        (car_organization_doctor_eds_valid_to, 185.5, 726.5),
        (car_organization_doctor_eds_number, 132, 734.5),
        *array_car_organization_doctor_eds_address,
    )

    media_files = paths_files(vid)
    thread = Thread(target=set_text_in_template_pdf, args=[array, media_files[4], media_files[2]])
    thread.setDaemon(True)
    thread.start()
    thread.join()
    return media_files


def text_output_in_several_lines(text, x, y, y_step, n):
    array_for_text = []
    for i in range(len(text[:n])):
        y += y_step
        array_for_text.append((text[i], x, y))
    return array_for_text


def new_pdf(path_to_pdf=''):
    pdf = Pdf.new()
    pdf.save(path_to_pdf)


def paths_files(vid):
    offset = timedelta(hours=int(WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid)).time_zone))
    tz = timezone(offset, name='TZ')
    now = datetime.now(tz=tz)
    date_time = now.strftime("%d.%m.%Y_%H-%M")
    path_to_media = Path(MEDIA_ROOT)
    if not Path.exists(path_to_media):
        Path.mkdir(path_to_media)
    v = str(vid)
    user_dir_name = str(v).replace("/", "").replace("+", "").replace("=", "")
    user_path = path_to_media.joinpath(user_dir_name)

    if not Path.exists(user_path):
        Path.mkdir(user_path)

    filename_pdf = Path("Waybill_" + str(date_time) + ".pdf")
    attached_data_filename = Path("data.pdf")
    attached_data = user_path.joinpath(attached_data_filename)
    pdf_media_file = user_path.joinpath(filename_pdf)

    if not Path(attached_data).exists():
        t = Thread(target=new_pdf, args=[attached_data])
        t.setDaemon(True)
        t.start()
        t.join()

    return user_path, user_dir_name, pdf_media_file, filename_pdf, attached_data


def set_text_in_template_pdf(text_data, path_to_pdf_attached_data, path_output_pdf):
    path_to_pdf_template = Path(MEDIA_ROOT).joinpath("template.pdf")
    path_to_ttf = Path(MEDIA_ROOT).joinpath("dejavu-sans-condensed_997.ttf")

    pdf = FPDF(orientation='P', unit='pt', format='A4')

    pdf.add_page()
    pdf.set_margin(0)

    pdf.add_font('DejaVu', '', path_to_ttf, uni=True)
    pdf.set_font('DejaVu', '', 7)

    for i in text_data:
        pdf.set_font_size(7)
        pdf.set_text_color(1, 1, 1)
        pdf.set_xy(i[1], i[2])
        pdf.cell(7, 7, i[0])

    pdf.output(path_to_pdf_attached_data)

    pdf1 = Pdf.open(path_to_pdf_template)
    pdf2 = Pdf.open(path_to_pdf_attached_data)

    page1 = Page(pdf1.pages[0])
    page2 = Page(pdf2.pages[0])
    page1.add_overlay(page2, Rectangle(0, 0, 595, 842))
    pdf1.save(path_output_pdf)


#def pdf_to_png_converter(path_file):
#     output = path_file[:-4] + ".png"
#     doc = fitz.open(path_file)
#     page = doc.load_page(0)
 
#     zoom = 3
#     mat = fitz.Matrix(zoom, zoom)
#     pix = page.getPixmap(matrix=mat)
#     pix.writePNG(output)
#     return output

def pdf_to_png_converter(path_file):
    output = path_file[:-4] + ".png"
    doc = fitz.open(path_file)
    zoom_x = 3.0
    zoom_y = 3.0
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = doc[0].get_pixmap(matrix=mat)
    pix.save(output)
import io
import re

import PyPDF2
import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def get_concat_h(im1, im2):
    dst = Image.new("RGB", (im1.width + im2.width, im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst

from PIL import Image, ImageOps
def merge_pages(order_image, barcode_image):
    track_border = (50, 30, 50, 0)
    order_border = (40, 40, 40, 0)
    # Sol, üst, sağ, alt,
    color = "green"
    order_image = ImageOps.expand(order_image, border=order_border, fill=color)
    barcode_image = ImageOps.expand(barcode_image, border=track_border, fill=color)
    ratio = order_image.height / barcode_image.height
    barcode_image = barcode_image.resize(
        (int(barcode_image.width * ratio), order_image.height)
    )
    merged_image = get_concat_h(barcode_image, order_image)
    whole_border = (0, 0, 0, 30)
    merged_image = ImageOps.expand(merged_image, border=whole_border, fill=color)
    a4_size = (841, 595)
    im_resized = ImageOps.fit(merged_image, a4_size, Image.ANTIALIAS)

    return merged_image


def get_track_numbers_and_page_numbers(track_images):
    order_list = []
    page_counter = 0
    pattern = r"\b\d{4} \d{4} \d{4} \d{4}\b \d{4}\b \d{2}\b"
    for img in track_images:
        track_num = (
            re.search(pattern, pytesseract.image_to_string(img))
            .group()
            .replace(" ", "")
        )
        img_dict = {track_num: page_counter}
        order_list.append(img_dict.copy())
        page_counter += 1

    return order_list


def img_to_pdf(img):
    with io.BytesIO() as f:
        img.save(f, format="pdf")
        pdf_bytes = f.getvalue()
        pdf_reader = PyPDF2.PdfFileReader(io.BytesIO(pdf_bytes))
        pdf_page = pdf_reader.getPage(0)
    return pdf_page


def merge_pdf_files(track, order, file_number):
    track_images = convert_from_path(track)
    order_images = convert_from_path(order)

    order_list = get_track_numbers_and_page_numbers(track_images)

    order_file = open(order, "rb")
    order_reader = PyPDF2.PdfFileReader(order_file)
    pdf_writer = PyPDF2.PdfFileWriter()
    merged_images = []
    pdf_pages = []
    pdf_writer = PyPDF2.PdfFileWriter()
    counter = 0
    for order_page_num in range(order_reader.getNumPages()):
        print(counter)
        counter += 1
        saved = False
        order_reader.getPage(order_page_num)
        pdf_page = order_reader.getPage(order_page_num)
        text = pdf_page.extractText()
        try:
            matches = re.findall(r"\d{19,22}", text)
            for item in order_list:
                for match in matches:
                    match = str(match)
                    ge = item.get(match)
                    if ge != None:
                        print("Order Ve Track Number eşleşti")
                        merged = merge_pages(
                            order_images[order_page_num], track_images[item.get(match)]
                        )
                        merged.resize((int(595 * 0.1), int(842 * 0.1)))
                        pdf_page = img_to_pdf(merged)
                        output_page = PyPDF2.pdf.PageObject.createBlankPage(
                            width=merged.width, height=merged.height
                        )
                        output_page.mergeScaledTranslatedPage(pdf_page, 1, 0, 0)
                        pdf_writer.addPage(output_page)
                        pdf_pages.append(pdf_page)
                        merged_images.append(merged)
                        saved = True
        except Exception as e:
            print("Excepte Düştü Yani Orderın devamı white imagela merge.",e)
            color = (255, 255, 255)  # white
            img = Image.new(
                "RGB", (track_images[0].width, track_images[0].height), color
            )
            merged = merge_pages(order_images[order_page_num], img)
            pdf_page = img_to_pdf(merged)
            output_page = PyPDF2.pdf.PageObject.createBlankPage(
                width=merged.width, height=merged.height
            )
            output_page.mergeScaledTranslatedPage(pdf_page, 1, 0, 0)
            pdf_writer.addPage(output_page)
            pdf_pages.append(pdf_page)
            saved = True

            """
            for item in order_list:
                if item.get(previous_order):
                    print(f"This page will merge with page {item.get(previous_order)}")
                    pageee = item.get(previous_order)
                    merged = merge_pages(order_images[order_page_num],track_images[item.get(previous_order)])
                    pdf_page = img_to_pdf(merged)
                    output_page = PyPDF2.pdf.PageObject.createBlankPage(width=merged.width, height=merged.height)
                    output_page.mergeScaledTranslatedPage(pdf_page, 1, 0, 0)
                    pdf_writer.addPage(output_page)
                    pdf_pages.append(pdf_page)
            """

        if not saved:
            print("Order Track numberla eşleşmedi.")
            color = (255, 255, 255)  # white
            img = Image.new(
                "RGB", (track_images[0].width, track_images[0].height), color
            )
            merged = merge_pages(order_images[order_page_num], img)
            pdf_page = img_to_pdf(merged)
            output_page = PyPDF2.pdf.PageObject.createBlankPage(
                width=merged.width, height=merged.height
            )
            output_page.mergeScaledTranslatedPage(pdf_page, 1, 0, 0)
            pdf_writer.addPage(output_page)
            pdf_pages.append(pdf_page)

    with open(f"merged_files/merged_{file_number}.pdf", "wb") as merged_file:
        pdf_writer.write(merged_file)



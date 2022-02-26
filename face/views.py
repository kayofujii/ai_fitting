import asyncio
import base64
import glob
import hashlib
import io
import os
import os.path
import shutil
import sys
import time
import uuid
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

import cv2
import numpy as np
import requests
from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import (Person,
                                                        TrainingStatusType)
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image, ImageDraw, ImageFilter

from .forms import ImageForm


def index(request):
    params = {}
    params["form"] = ImageForm()
    return render(request, "index.html", params)


# def fitting(request):
#     params = {}
#     params["form"] = ImageForm()
#     return render(request, "fitting.html", params)


def help(request):
    params = {}
    return render(request, "help.html", params)


def about(request):
    params = {}
    return render(request, "about.html", params)


def upload_image(request):
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            user_im = request.FILES.get("user_im")
            product_im = request.FILES.get("product_im")
            hash_now_date, output = recognize_face_with_api(
                user_im, product_im)

            if not output:
                messages.error(request, '画像の作成に失敗しました。')
                return redirect('index')

            result_file = open(output, 'rb').read()
            delete_file(hash_now_date)
            return HttpResponse(result_file, content_type="image/png")
        else:
            messages.error(request, '画像を選択してください')
            return redirect('index')


def get_tmp_image_path(dir, hash_now_date):
    os.makedirs(str(settings.BASE_DIR) +
                f"/media/tmp/{dir}{hash_now_date}", exist_ok=True)
    return f"/media/tmp/{dir}{hash_now_date}/%s%s" % (hash_now_date, ".png")


def recognize_face_with_api(user_im, product_im):
    # Face API を使用したバージョン
    face_client = FaceClient(
        settings.ENDPOINT, CognitiveServicesCredentials(settings.KEY))
    now_date = str(datetime.now())
    hash_now_date = hashlib.sha1((now_date).encode("utf-8")).hexdigest()

    u_path = str(settings.BASE_DIR) + get_tmp_image_path('user', hash_now_date)
    fs = FileSystemStorage()
    filename = fs.save(u_path, user_im)

    img = Image.open('media/' + filename)

    u_stream = open(
        'media/' + filename, "rb")

    u_detected_faces = face_client.face.detect_with_stream(
        image=u_stream, detection_model='detection_03')

    u_face = u_detected_faces[0]

    user_rect = u_face.face_rectangle

    x, y, w, h = user_rect.left, user_rect.top, user_rect.width, user_rect.height
    sab = int(w*0.5)

    im_crop = img.crop((x-sab, y-sab, x+w+sab, y+h+sab))
    im_rgba = im_crop.copy()

    # 丸を作成
    im_a = Image.new("L", im_rgba.size, 0)
    draw = ImageDraw.Draw(im_a)
    draw.ellipse((0, 0, im_rgba.size[0], im_rgba.size[0]), fill=255)
    im_a = im_a.filter(ImageFilter.GaussianBlur(10))

    # 丸に顔をいれる
    im_rgba.putalpha(im_a)
    im_rgba_crop = im_rgba.crop(
        (0, 0, im_rgba.size[0]+20, im_rgba.size[0]+20))
    crop_path = str(settings.BASE_DIR) +\
        get_tmp_image_path('crop', hash_now_date)
    im_rgba_crop.save(crop_path)

    p_path = str(settings.BASE_DIR) + get_tmp_image_path('pro', hash_now_date)
    ps = FileSystemStorage()
    pfilename = ps.save(p_path, product_im)

    # 商品画像の顔を識別
    pro_img = Image.open('media/' + pfilename)
    p_stream = open('media/' + pfilename, "rb")

    p_detected_faces = face_client.face.detect_with_stream(
        image=p_stream, detection_model='detection_03')
    p_face = p_detected_faces[0]

    pro_rect = p_face.face_rectangle
    px, py, pw, ph = pro_rect.left, pro_rect.top, pro_rect.width, pro_rect.height
    p_sab = int(pw*0.5)

    copy_pro_im = pro_img.copy()
    im_rgba_crop = im_rgba_crop.resize((int(pw+p_sab*2), int(ph+p_sab*2)))
    copy_pro_im.paste(im_rgba_crop, (int(px-p_sab), int(py-p_sab)),
                      im_rgba_crop.split()[3])

    copy_pro_im.save(str(settings.BASE_DIR) +
                     get_tmp_image_path('paste', hash_now_date))

    output = str(settings.BASE_DIR) + \
        get_tmp_image_path('images', hash_now_date)

    output_im = copy_pro_im.copy()
    output_im = np.array(output_im, dtype=np.uint8)
    output_im = cv2.cvtColor(output_im, cv2.COLOR_RGB2BGR)

    cv2.imwrite(output, output_im)
    return hash_now_date, output


def delete_file(hash_now_date):
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/user{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/pro{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/crop{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/paste{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) +
                  f'/media/tmp/images{hash_now_date}/')

from django.http import HttpResponseServerError
from django.views.decorators.csrf import requires_csrf_token
import hashlib
import os.path
import shutil
from datetime import datetime

import cv2
import numpy as np
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
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
            day, output = recognize_face(user_im, product_im)

            if not output:
                messages.error(request, '画像の作成に失敗しました。')
                return redirect('index')

            result_file = open(output, 'rb').read()
            delete_file(day)
            return HttpResponse(result_file, content_type="image/png")
        else:
            messages.error(request, '画像を選択してください')
            return redirect('index')


def get_tmp_image_path(dir, day):
    os.makedirs(str(settings.BASE_DIR) +
                f"/media/tmp/{dir}{day}", exist_ok=True)
    return f"/media/tmp/{dir}{day}/%s%s" % (
        hashlib.sha1(
            (day).encode("utf-8")).hexdigest(),
        ".png",
    )


def recognize_face(user_im, product_im):
    day = str(datetime.utcnow().date()).replace('-', '')
    face_cascade = cv2.CascadeClassifier('opencv/face_cascade.xml')
    src = cv2.imdecode(np.fromstring(
        user_im.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    try:
        faces = face_cascade.detectMultiScale(src)
    except:
        return None, None
    try:
        face = sorted(faces, reverse=True, key=lambda x: x[2])[0]
    except:
        return None, None

    x, y, w, h = face[0], face[1], face[2], face[3]
    sab = int(w*0.25)
    face = src[y-sab:y+h+sab, x-sab:x+w+sab]
    im_rgba = face.copy()

    # opencv→pillow変換 https://qiita.com/derodero24/items/f22c22b22451609908ee
    im_rgba = cv2.cvtColor(im_rgba, cv2.COLOR_BGR2RGB)
    im_rgba = Image.fromarray(im_rgba)
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
        get_tmp_image_path('crop', day)
    im_rgba_crop.save(crop_path)

    # 商品画像の顔を識別
    pro_src = cv2.imdecode(np.fromstring(
        product_im.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    try:
        pro_faces = face_cascade.detectMultiScale(pro_src)
    except:
        return None, None
    try:
        pro_face = sorted(pro_faces, reverse=True, key=lambda x: x[2])[0]
    except:
        return None, None

    px, py, pw, ph = pro_face[0], pro_face[1], pro_face[2], pro_face[3]

    pro_im = cv2.cvtColor(pro_src, cv2.COLOR_BGR2RGB)
    pro_im = Image.fromarray(pro_im)

    copy_pro_im = pro_im.copy()
    im_rgba_crop = im_rgba_crop.resize((int(pw+sab*1.5), int(ph+sab*1.5)))
    copy_pro_im.paste(im_rgba_crop, (px-sab, py-sab),
                      im_rgba_crop.split()[3])
    copy_pro_im.save(str(settings.BASE_DIR) +
                     get_tmp_image_path('paste', day))

    output = str(settings.BASE_DIR) + get_tmp_image_path('images', day)

    output_im = copy_pro_im.copy()
    output_im = np.array(output_im, dtype=np.uint8)
    output_im = cv2.cvtColor(output_im, cv2.COLOR_RGB2BGR)

    cv2.imwrite(output, output_im)
    return day, output


def delete_file(day):
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/crop{day}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/paste{day}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/images{day}/')


@requires_csrf_token
def my_customized_server_error(request, template_name='500.html'):
    import sys

    from django.views import debug
    error_html = debug.technical_500_response(request, *sys.exc_info()).content
    return HttpResponseServerError(error_html)

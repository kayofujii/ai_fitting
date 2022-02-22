import hashlib
import os.path
import shutil
from datetime import datetime

import cv2
import numpy as np
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from PIL import Image, ImageDraw, ImageFilter

from .forms import ImageForm
from .models import UploadedImage

# def home(request):
#     params = {}

#     return render(request, "home.html", params)


def index(request):
    params = {}
    params["form"] = ImageForm()
    # params["uploaded_images"] = UploadedImage.objects.filter(author=request.user).order_by(
    #     '-created_at')

    return render(request, "index.html", params)


def upload_image(request):
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            # uploaded_image = UploadedImage()
            # uploaded_image.user_im = request.FILES.get("user_im")
            # uploaded_image.product_im = request.FILES.get("product_im")
            # uploaded_image.author = request.user
            # uploaded_image.save()
            user_im = request.FILES.get("user_im")
            product_im = request.FILES.get("product_im")

            day, output = recognize_face(user_im, product_im)
            # uploaded_image.image = get_image_path(uploaded_image)
            # uploaded_image.save()
            # path = str(settings.BASE_DIR) + "/media" + \
            #     get_image_path()
            result_file = open(output, 'rb').read()
            delete_file(day)
    return HttpResponse(result_file, content_type="image/png")


# def get_image_path(day):
#     return "/face_images/%s%s" % (
#         hashlib.sha1(
#             (day).encode("utf-8")).hexdigest(),
#         ".png",
#     )


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

    # url = uploaded_image.user_im.url
    # path = str(settings.BASE_DIR) + url
    # src = cv2.imread(path)
    src = cv2.imdecode(np.fromstring(
        user_im.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    faces = face_cascade.detectMultiScale(src)
    face = sorted(faces, reverse=True, key=lambda x: x[2])[0]

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
    # pro_path = str(settings.BASE_DIR) + uploaded_image.product_im.url
    # pro_src = cv2.imread(pro_path)
    pro_src = cv2.imdecode(np.fromstring(
        product_im.read(), np.uint8), cv2.IMREAD_UNCHANGED)
    pro_faces = face_cascade.detectMultiScale(pro_src)
    pro_face = sorted(pro_faces, reverse=True, key=lambda x: x[2])[0]

    px, py, pw, ph = pro_face[0], pro_face[1], pro_face[2], pro_face[3]

    pro_im = cv2.cvtColor(pro_src, cv2.COLOR_BGR2RGB)
    pro_im = Image.fromarray(pro_im)

    # pro_im = Image.open(pro_path)
    copy_pro_im = pro_im.copy()
    im_rgba_crop = im_rgba_crop.resize((pw+sab*2, ph+sab*2))
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

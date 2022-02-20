import hashlib
import os.path

import cv2
import numpy as np
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from PIL import Image, ImageDraw, ImageFilter

from .forms import ImageForm
from .models import UploadedImage


def home(request):
    params = {}

    return render(request, "home.html", params)


@login_required
def index(request):
    params = {}
    params["form"] = ImageForm()
    params["uploaded_images"] = UploadedImage.objects.filter(author=request.user).order_by(
        '-created_at')

    return render(request, "index.html", params)


@login_required
def upload_image(request):
    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_image = UploadedImage()
            uploaded_image.user_im = request.FILES.get("user_im")
            uploaded_image.product_im = request.FILES.get("product_im")
            uploaded_image.author = request.user
            uploaded_image.save()

            recognize_face(uploaded_image)
            uploaded_image.image = get_image_path(uploaded_image)
            uploaded_image.save()
    return redirect("index")


def get_image_path(before_im):
    return "/face_images/%s%s" % (
        hashlib.sha1(
            (before_im.user_im.url).encode("utf-8")).hexdigest(),
        ".png",
    )


def get_tmp_image_path(before_im, dir):
    os.makedirs(str(settings.BASE_DIR) +
                f"/media/tmp/{dir}", exist_ok=True)
    return f"/media/tmp/{dir}/%s%s" % (
        hashlib.sha1(
            (before_im.user_im.url).encode("utf-8")).hexdigest(),
        ".png",
    )


def recognize_face(uploaded_image):
    face_cascade = cv2.CascadeClassifier('opencv/face_cascade.xml')

    url = uploaded_image.user_im.url
    path = str(settings.BASE_DIR) + url
    src = cv2.imread(path)

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
        get_tmp_image_path(uploaded_image, 'crop')
    im_rgba_crop.save(crop_path)

    # 商品画像の顔を識別
    pro_path = str(settings.BASE_DIR) + uploaded_image.product_im.url
    pro_src = cv2.imread(pro_path)
    pro_faces = face_cascade.detectMultiScale(pro_src)
    pro_face = sorted(pro_faces, reverse=True, key=lambda x: x[2])[0]

    px, py, pw, ph = pro_face[0], pro_face[1], pro_face[2], pro_face[3]

    pro_im = Image.open(pro_path)
    copy_pro_im = pro_im.copy()
    im_rgba_crop = im_rgba_crop.resize((pw+sab*2, ph+sab*2))
    copy_pro_im.paste(im_rgba_crop, (px-sab, py-sab),
                      im_rgba_crop.split()[3])
    copy_pro_im.save(str(settings.BASE_DIR) +
                     get_tmp_image_path(uploaded_image, 'paste'))

    output = str(settings.BASE_DIR) + '/media' + \
        get_image_path(uploaded_image)

    output_im = copy_pro_im.copy()
    output_im = np.array(output_im, dtype=np.uint8)
    output_im = cv2.cvtColor(output_im, cv2.COLOR_RGB2BGR)

    cv2.imwrite(output, output_im)
    return output

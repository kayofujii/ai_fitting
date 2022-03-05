import hashlib
import os
import os.path
import shutil
from datetime import datetime
from urllib.parse import urlencode

import pyheif
from azure.cognitiveservices.vision.face import FaceClient
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import redirect, render
from django.urls import reverse
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image, ImageDraw, ImageFilter

from .forms import ImageForm
from .models import UploadedImage


def index(request):
    params = {}
    params["form"] = ImageForm()

    try:
        token = request.GET.get('token')
        image = UploadedImage.objects.get(
            token=token)
        params['image'] = image
    except:
        pass
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
            try:
                hash_now_date, output = recognize_face_with_api(
                    user_im, product_im)
            except:
                messages.error(request, '画像の作成に失敗しました。')
                return redirect('index')

            uploaded_image = UploadedImage()
            uploaded_image.user_im = user_im
            uploaded_image.product_im = product_im
            uploaded_image.image = SimpleUploadedFile(name='temp.png', content=open(
                output, 'rb').read(), content_type='image/png')
            uploaded_image.token = hash_now_date

            if request.user.is_authenticated:
                uploaded_image.author = request.user
            uploaded_image.save()

            delete_file(hash_now_date)
            redirect_url = reverse('index')
            parameters = urlencode({'token': hash_now_date})
            url = f'{redirect_url}?{parameters}'
            return redirect(url)
        else:
            messages.error(request, '画像を選択してください')
            return redirect('index')


def get_tmp_image_path(dir, hash_now_date, im=None):
    extention = '.png'
    if im:
        extention = os.path.splitext(im.name)[1]
    os.makedirs(str(settings.BASE_DIR) +
                f"/media/tmp/{dir}{hash_now_date}", exist_ok=True)
    return f"/media/tmp/{dir}{hash_now_date}/%s%s" % (hash_now_date, extention)


def rotateImage(img, orientation):
    """
    画像ファイルをOrientationの値に応じて回転させる
    """
    # orientationの値に応じて画像を回転させる
    if orientation == 1:
        pass
    elif orientation == 2:
        # 左右反転
        img_rotate = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif orientation == 3:
        # 180度回転
        img_rotate = img.transpose(Image.ROTATE_180)
    elif orientation == 4:
        # 上下反転
        img_rotate = img.transpose(Image.FLIP_TOP_BOTTOM)
    elif orientation == 5:
        # 左右反転して90度回転
        img_rotate = img.transpose(
            Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
    elif orientation == 6:
        # 270度回転
        img_rotate = img.transpose(Image.ROTATE_270)
    elif orientation == 7:
        # 左右反転して270度回転
        img_rotate = img.transpose(
            Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
    elif orientation == 8:
        # 90度回転
        img_rotate = img.transpose(Image.ROTATE_90)
    else:
        pass

    return img_rotate


def save_image_match_exif(img, filename):
    # exif情報取得
    exifinfo = img._getexif()
    # exif情報からOrientationの取得
    orientation = exifinfo.get(0x112, 1)
    # 画像を回転
    img_rotate = rotateImage(img, orientation)
    # 回転した画像を保存（元の画像に上書き）
    img_rotate.save('media/' + filename)
    img = Image.open('media/' + filename)
    return img


def recognize_face_with_api(user_im, product_im):
    # Face API を使用したバージョン
    face_client = FaceClient(
        settings.ENDPOINT, CognitiveServicesCredentials(settings.KEY))
    now_date = str(datetime.now())
    hash_now_date = hashlib.sha1((now_date).encode("utf-8")).hexdigest()

    u_path = str(settings.BASE_DIR) + \
        get_tmp_image_path('user', hash_now_date, user_im)
    fs = FileSystemStorage()
    filename = fs.save(u_path, user_im)

    img = Image.open('media/' + filename)
    try:
        img = save_image_match_exif(img, filename)
    except:
        pass

    u_stream = open(
        'media/' + filename, "rb")

    u_detected_faces = face_client.face.detect_with_stream(
        image=u_stream, detection_model='detection_03')

    u_face = u_detected_faces[0]

    user_rect = u_face.face_rectangle

    x, y, w, h = user_rect.left, user_rect.top, user_rect.width, user_rect.height
    sab = int(w*0.35)

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
        (0, 0, im_rgba.size[0]+int(im_rgba.size[0]*0.25),
         im_rgba.size[0]+int(im_rgba.size[0]*0.25)))
    crop_path = str(settings.BASE_DIR) +\
        get_tmp_image_path('crop', hash_now_date)
    im_rgba_crop.save(crop_path)

    p_path = str(settings.BASE_DIR) + \
        get_tmp_image_path('pro', hash_now_date, product_im)
    ps = FileSystemStorage()
    pfilename = ps.save(p_path, product_im)

    # 商品画像の顔を識別
    pro_img = Image.open('media/' + pfilename)

    try:
        pro_img = save_image_match_exif(pro_img, filename)
    except:
        pass

    p_stream = open('media/' + pfilename, "rb")

    p_detected_faces = face_client.face.detect_with_stream(
        image=p_stream, detection_model='detection_03')
    p_face = p_detected_faces[0]

    pro_rect = p_face.face_rectangle
    px, py, pw, ph = pro_rect.left, pro_rect.top, pro_rect.width, pro_rect.height
    p_sab = int(pw*0.35)

    copy_pro_im = pro_img.copy()
    im_rgba_crop = im_rgba_crop.resize((int(pw+p_sab*2.8), int(ph+p_sab*2.8)))
    copy_pro_im.paste(im_rgba_crop, (px-p_sab, py-int(p_sab*1.5)),
                      im_rgba_crop.split()[3])
    output = str(settings.BASE_DIR) + \
        get_tmp_image_path('images', hash_now_date)
    copy_pro_im.save(output)
    return hash_now_date, output


def delete_file(hash_now_date):
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/user{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/pro{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) + f'/media/tmp/crop{hash_now_date}/')
    shutil.rmtree(str(settings.BASE_DIR) +
                  f'/media/tmp/images{hash_now_date}/')

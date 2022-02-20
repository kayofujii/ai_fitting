import hashlib
import os.path

import cv2
import numpy as np
from django.conf import settings
from django.shortcuts import redirect, render
from PIL import Image, ImageDraw, ImageFilter

from .forms import ImageForm
from .models import UploadedImage


def index(request):
    params = {}
    params["form"] = ImageForm()
    params["uploaded_images"] = UploadedImage.objects.filter(author=request.user).order_by(
        '-created_at')

    return render(request, "index.html", params)


def upload_image(request):

    return render(request, "index.html")

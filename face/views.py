from django.shortcuts import render


def index(request):

    return render(request, "index.html")


def upload_image(request):

    return render(request, "index.html")

from django import forms


class ImageForm(forms.Form):
    user_im = forms.FileField(label="ユーザー画像")
    product_im = forms.FileField(label="商品画像")

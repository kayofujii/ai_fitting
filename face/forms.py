from django import forms


class ImageForm(forms.Form):
    user_im = forms.ImageField(label="ユーザー画像")
    product_im = forms.ImageField(label="商品画像")

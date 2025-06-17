# board/forms.py
from django import forms
from captcha.fields import CaptchaField
from .models import Message

class MessageForm(forms.ModelForm):
    captcha = CaptchaField(label="驗證碼") # 增加驗證碼字段

    class Meta:
        model = Message
        fields = ['subject', 'content', 'captcha'] # 在表單中包含 captcha 字段
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': '請輸入主题'}),
            'content': forms.Textarea(attrs={'placeholder': '請輸入留言内容', 'rows': 5}),
        }
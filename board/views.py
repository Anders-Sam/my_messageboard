# board/views.py
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Message
from .forms import MessageForm # 稍後創建
from captcha.fields import CaptchaField # 導入驗證碼字段
from captcha.models import CaptchaStore
from captcha.helpers import captcha_image_url

# ... (導入其他)

# class MyMessageForm(forms.ModelForm):
#     # 為方便展示，這裡不直接集成 CaptchaField，而是在視圖中動態處理或獨立表單
#     # 如果要直接集成，可以這樣做：captcha = CaptchaField()
#     class Meta:
#         model = Message
#         fields = ['subject', 'content'] # author 會在試圖中自動填入

# 留言列表視圖 (已審核的留言)
def message_list(request):
    approved_messages = Message.objects.filter(is_approved=True)
    paginator = Paginator(approved_messages, 10) # 每頁10條
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'board/message_list.html', {'page_obj': page_obj})

# 發布留言視圖
@login_required # 限定只有登錄用户才能訪問
def post_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST) # 稍後創建包含驗證碼的表單
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user # 自動設置留言者為當前登錄用户
            message.save()
            messages.success(request, '您的留言已提交，等待管理员审核。')
            return redirect('message_list')
    else:
        form = MessageForm() # 稍後創建包含驗證碼的表單
    return render(request, 'board/post_message.html', {'form': form})
# Create your views here.

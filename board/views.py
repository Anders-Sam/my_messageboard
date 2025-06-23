# board/views.py
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.mail import send_mail, mail_admins
from django.conf import settings
from django.urls import reverse
from .models import Message, User
from .forms import MessageForm, CustomUserCreationForm # 導入 CustomUserCreationForm
from captcha.fields import CaptchaField # 導入驗證碼字段
# from captcha.models import CaptchaStore # 通常不需要直接操作 Store
# from captcha.helpers import captcha_image_url # 通常由 widget 處理

# 註冊視圖
def signup(request):
    if request.user.is_authenticated:
        return redirect('message_list') # 如果已登入，重定向到首頁
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # 註冊後自動登入
            messages.success(request, '註冊成功！歡迎加入，您現在已登入。')
            # 可以考慮發送歡迎郵件
            # send_mail(
            #     '歡迎加入我們的留言板',
            #     f'您好 {user.username},\n\n感謝您的註冊！',
            #     settings.DEFAULT_FROM_EMAIL,
            #     [user.email],
            #     fail_silently=True, # 開發時可設為 False 以便調試
            # )
            return redirect('message_list') # 重定向到留言列表
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


# 留言列表視圖 (已審核的留言)
def message_list(request):
    # 只顯示已審核的留言，並按時間倒序排列
    message_list_qs = Message.objects.filter(is_approved=True).order_by('-created_at')
    paginator = Paginator(message_list_qs, 10) # 每頁顯示 10 條留言
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 檢查是否有留言，用於模板中顯示提示信息
    has_messages = message_list_qs.exists()

    admin_email = None
    if settings.ADMINS and settings.ADMINS[0] and isinstance(settings.ADMINS[0], tuple) and len(settings.ADMINS[0]) > 1:
        admin_email = settings.ADMINS[0][1] # (Name, Email)

    return render(request, 'board/message_list.html', {
        'page_obj': page_obj,
        'has_messages': has_messages,
        'admin_contact_email': admin_email,
    })

# 發布留言視圖
@login_required # 限定只有登錄用户才能訪問
def post_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST) # 包含驗證碼的表單
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user # 自動設置留言者為當前登錄用户
            message.save()
            messages.success(request, '您的留言已成功提交，管理員將盡快審核。')

            # 通知管理員有新留言待審核
            try:
                admin_url = request.build_absolute_uri(reverse('admin:board_message_change', args=[message.pk]))
                mail_admins(
                    subject=f"【新留言待審核】{message.subject}",
                    message=f"使用者 {request.user.username} 發布了一條新留言需要審核。\n\n"
                            f"主題: {message.subject}\n"
                            f"內容: {message.content[:200]}...\n\n"
                            f"請點擊以下鏈接進行審核:\n{admin_url}",
                    fail_silently=True # 生產環境中建議 True，開發時 False
                )
            except Exception as e:
                # 記錄錯誤，但不影響用戶體驗
                print(f"Error sending admin notification email: {e}")

            return redirect('message_list') # 重定向到留言列表
        else:
            # 表單無效時，將錯誤信息傳遞給模板
            messages.error(request, '表單提交失敗，請檢查您輸入的內容。')
    else:
        form = MessageForm() # GET 請求時，創建空表單
    return render(request, 'board/post_message.html', {'form': form})

@login_required
def edit_message(request, message_id):
    try:
        message = Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        messages.error(request, "找不到指定的留言。")
        return redirect('message_list')

    if message.author != request.user:
        messages.error(request, "您沒有權限編輯此留言。")
        return redirect('message_list')

    if request.method == 'POST':
        # 傳遞 is_editing=True 以移除驗證碼
        form = MessageForm(request.POST, instance=message, is_editing=True)
        if form.is_valid():
            edited_message = form.save(commit=False)
            edited_message.is_approved = False # 修改後需要重新審核
            edited_message.notified = False    # 重置通知狀態
            edited_message.save()
            messages.success(request, '留言已成功修改，將等待管理員重新審核。')

            # 通知管理員有留言被修改並待審核
            try:
                admin_url = request.build_absolute_uri(reverse('admin:board_message_change', args=[edited_message.pk]))
                mail_admins(
                    subject=f"【留言已修改待重審】{edited_message.subject}",
                    message=f"使用者 {request.user.username} 修改了他們的留言，需要重新審核。\n\n"
                            f"主題: {edited_message.subject}\n"
                            f"內容: {edited_message.content[:200]}...\n\n"
                            f"請點擊以下鏈接進行審核:\n{admin_url}",
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error sending admin notification email for edited message: {e}")

            return redirect('message_list')
        else:
            messages.error(request, '表單提交失敗，請檢查您輸入的內容。')
    else:
        # 傳遞 is_editing=True 以移除驗證碼
        form = MessageForm(instance=message, is_editing=True)

    return render(request, 'board/edit_message.html', {'form': form, 'message': message})

@login_required
def delete_message(request, message_id):
    try:
        message = Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        messages.error(request, "找不到指定的留言。")
        return redirect('message_list')

    # 允許作者或管理員刪除
    if not (message.author == request.user or request.user.is_staff):
        messages.error(request, "您沒有權限刪除此留言。")
        return redirect('message_list')

    if request.method == 'POST':
        subject = message.subject # Store subject for message before deleting
        message.delete()
        messages.success(request, f'留言 "{subject}" 已成功刪除。')
        return redirect('message_list')

    return render(request, 'board/delete_message_confirm.html', {'message': message})
# Create your views here.

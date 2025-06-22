"""
URL configuration for my_messageboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# my_messageboard/urls.py
from django.contrib import admin
from django.urls import path, include
from board import views as board_views # 導入應用視圖，並使用別名以區分
from django.contrib.auth import views as auth_views # 導入 Django 內建的認證視圖

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'), # 登入
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'), # 登出
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'), # 密碼重設請求
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'), # 密碼重設郵件已發送
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'), # 密碼重設確認
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'), # 密碼重設完成
    path('accounts/signup/', board_views.signup, name='signup'), # 註冊
    path('', board_views.message_list, name='message_list'), # 留言列表頁
    path('post/', board_views.post_message, name='post_message'), # 發布留言頁
    path('message/<int:message_id>/edit/', board_views.edit_message, name='edit_message'), # 編輯留言頁
    path('message/<int:message_id>/delete/', board_views.delete_message, name='delete_message'), # 刪除留言頁
    path('captcha/', include('captcha.urls')), # 驗證碼 URL
]

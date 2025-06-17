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
from board import views # 導入應用視

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Django 認證系統的 URL
    path('', views.message_list, name='message_list'), # 留言列表頁
    path('post/', views.post_message, name='post_message'), # 發布留言頁
    path('captcha/', include('captcha.urls')), # 驗證碼 URL
]

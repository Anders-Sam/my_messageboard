# board/models.py
from django.db import models
from django.contrib.auth.models import User # 導入Django内置的用户模型

class Message(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="留言者")
    subject = models.CharField(max_length=200, verbose_name="主題")
    content = models.TextField(verbose_name="留言内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="留言時間")
    is_approved = models.BooleanField(default=False, verbose_name="是否通過審核")
    notified = models.BooleanField(default=False, verbose_name="已通知留言者") # 用於郵件通知

    class Meta:
        ordering = ['-created_at'] # 按時間倒序排列
        verbose_name = "留言"
        verbose_name_plural = "留言"

    def __str__(self):
        return f"主題: {self.subject} - 留言者: {self.author.username}"
# Create your models here.

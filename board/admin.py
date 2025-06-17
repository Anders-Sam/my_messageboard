# board/admin.py
from django.contrib import admin
from .models import Message
from django.template.response import TemplateResponse
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'author', 'created_at', 'is_approved', 'notified', 'admin_actions')
    list_filter = ('is_approved', 'notified')
    search_fields = ('subject', 'content', 'author__username')
    actions = ['mark_approved', 'mark_unapproved'] # 批量操作

    # 自定義字段，用於顯示管理操作按鈕
    def admin_actions(self, obj):
        if not obj.is_approved:
            return admin.display(description="操作", ordering='-created_at')(
                lambda o: f'<a class="button" href="{obj.id}/approve/">審核通過</a>'
            )(obj)
        return ""
    admin_actions.allow_tags = True
    admin_actions.short_description = "操作"

    # 審核通過動作
    def approve_message(self, request, message_id):
        message = Message.objects.get(id=message_id)
        if not message.is_approved:
            message.is_approved = True
            message.save()
            messages.success(request, f'留言 "{message.subject}" 已通過審核。')
            # 審核通過後發送郵件通知
            try:
                if not message.notified:
                    send_mail(
                        '您的留言已通過審核',
                        f'您好，您的留言《{message.subject}》已通過管理員審核，現在已在網站上顯示。',
                        settings.DEFAULT_FROM_EMAIL,
                        [message.author.email],
                        fail_silently=False,
                    )
                    message.notified = True
                    message.save()
                    messages.info(request, f'已發送郵件通知留言者 {message.author.username}。')
            except Exception as e:
                messages.error(request, f'發送郵件通知失敗: {e}')
        return redirect('admin:board_message_changelist')

    # 批量通過
    @admin.action(description='批量通過選中的留言')
    def mark_approved(self, request, queryset):
        for message in queryset:
            if not message.is_approved:
                message.is_approved = True
                message.save()
                # 審核通過後發送郵件通知
                try:
                    if not message.notified:
                        send_mail(
                            '您的留言已通過審核',
                            f'您好，您的留言《{message.subject}》已通過管理員審核，現在已在網站上顯示。',
                            settings.DEFAULT_FROM_EMAIL,
                            [message.author.email],
                            fail_silently=False,
                        )
                        message.notified = True
                        message.save()
                except Exception as e:
                    self.message_user(request, f'發送郵件通知留言者 {message.author.username} 失敗: {e}', level='error')
        self.message_user(request, f'成功通過 {queryset.count()} 條留言。')

    # 批量取消通過
    @admin.action(description='批量取消通過選中的留言')
    def mark_unapproved(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'成功取消通過 {queryset.count()} 條留言。')


    # 添加自定義的 URL 路由
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:message_id>/approve/', self.admin_site.admin_view(self.approve_message), name='message_approve'),
            path('approve_all_pending/', self.admin_site.admin_view(self.approve_all_pending), name='approve_all_pending'),
        ]
        return custom_urls + urls

    # "快速通過全部留言" 按鈕視圖
    def approve_all_pending(self, request):
        if request.method == 'POST':
            pending_messages = Message.objects.filter(is_approved=False)
            count = 0
            for message in pending_messages:
                message.is_approved = True
                message.save()
                # 審核通過後發送郵件通知
                try:
                    if not message.notified:
                        send_mail(
                            '您的留言已通過審核',
                            f'您好，您的留言《{message.subject}》已通過管理員審核，現在已在網站上顯示。',
                            settings.DEFAULT_FROM_EMAIL,
                            [message.author.email],
                            fail_silently=False,
                        )
                        message.notified = True
                        message.save()
                except Exception as e:
                    self.message_user(request, f'發送郵件通知留言者 {message.author.username} 失敗: {e}', level='error')
                count += 1
            messages.success(request, f'成功通過了 {count} 條未審核留言。')
            return redirect('admin:board_message_changelist')

        # 顯示確認頁面
        pending_count = Message.objects.filter(is_approved=False).count()
        context = dict(
            self.admin_site.each_context(request),
            pending_count=pending_count,
            title="確認快速通過所有未審核留言",
        )
        return TemplateResponse(request, "admin/approve_all_pending_confirmation.html", context)


    # 在 admin 列表頁頂部添加自定義按鈕
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['pending_messages_count'] = Message.objects.filter(is_approved=False).count()
        return super().changelist_view(request, extra_context=extra_context)
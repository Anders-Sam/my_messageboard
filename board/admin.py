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
    list_display = ('subject', 'author_email', 'created_at', 'is_approved', 'notified') # 修改 'author' 為 'author_email'
    list_filter = ('is_approved', 'notified', 'author__username') # 增加 author__username 過濾
    search_fields = ('subject', 'content', 'author__username', 'author__email') # 增加 author__email 搜尋
    actions = ['mark_approved_and_notify', 'mark_unapproved'] # 修改批量操作名稱
    readonly_fields = ('author', 'subject', 'content', 'created_at') # 設置部分欄位為唯讀

    # 顯示留言者 Email
    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = '留言者 Email'

    # 審核通過並通知的動作 (合併原有的 approve_message 和 mark_approved)
    def _approve_and_notify_message(self, request, message):
        if not message.is_approved:
            message.is_approved = True
            # 只有在留言者有 Email 的情況下才嘗試發送郵件
            if message.author.email:
                try:
                    if not message.notified: # 避免重複通知
                        send_mail(
                            f'您的留言「{message.subject}」已通過審核',
                            f'您好 {message.author.username}，\n\n您的留言「{message.subject}」已通過管理員審核，現在已在網站上顯示。\n\n感謝您的參與！',
                            settings.DEFAULT_FROM_EMAIL,
                            [message.author.email],
                            fail_silently=False,
                        )
                        message.notified = True
                        messages.success(request, f'已發送郵件通知留言者 {message.author.username} ({message.author.email})。')
                except Exception as e:
                    messages.error(request, f'發送郵件通知給 {message.author.username} ({message.author.email}) 失敗: {e}')
            else:
                messages.warning(request, f'留言者 {message.author.username} 未提供電子郵件，無法發送通知。')
            message.save()
            return True
        return False

    # 單個審核操作（保持原有邏輯，但調用新的通知方法）
    def approve_message_view(self, request, message_id):
        message = Message.objects.get(id=message_id)
        if self._approve_and_notify_message(request, message):
            messages.success(request, f'留言 "{message.subject}" 已通過審核。')
        else:
            messages.info(request, f'留言 "{message.subject}" 先前已被審核。')
        return redirect('admin:board_message_changelist')

    # 批量通過並通知
    @admin.action(description='批量通過選中留言並郵件通知')
    def mark_approved_and_notify(self, request, queryset):
        approved_count = 0
        for message in queryset:
            if self._approve_and_notify_message(request, message):
                approved_count +=1
        if approved_count > 0:
            self.message_user(request, f'成功通過 {approved_count} 條留言。')
        else:
            self.message_user(request, '沒有留言被更新（可能已審核或無郵箱）。', level=messages.WARNING)


    # 批量取消通過
    @admin.action(description='批量取消通過選中的留言 (不發送通知)')
    def mark_unapproved(self, request, queryset):
        updated_count = queryset.update(is_approved=False, notified=False) # 取消審核時也重置通知狀態
        self.message_user(request, f'成功取消通過 {updated_count} 條留言。')


    # 添加自定義的 URL 路由
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:message_id>/approve/', self.admin_site.admin_view(self.approve_message_view), name='message_approve'), # 更新視圖名稱
            path('approve_all_pending/', self.admin_site.admin_view(self.approve_all_pending_view), name='approve_all_pending'), # 更新視圖名稱
        ]
        return custom_urls + urls

    # "快速通過全部未審核留言" 按鈕視圖
    def approve_all_pending_view(self, request): # 更新視圖名稱
        if request.method == 'POST':
            pending_messages = Message.objects.filter(is_approved=False)
            approved_count = 0
            for message in pending_messages:
                if self._approve_and_notify_message(request, message):
                    approved_count += 1
            if approved_count > 0:
                messages.success(request, f'成功通過了 {approved_count} 條未審核留言。')
            else:
                messages.info(request, '沒有需要通過的未審核留言，或留言者無 Email。')
            return redirect('admin:board_message_changelist')

        # 顯示確認頁面
        pending_count = Message.objects.filter(is_approved=False).count()
        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta, # <<<< 主要修改：將 model._meta 傳遞給模板上下文的 'opts'
            pending_count=pending_count,
            title="確認快速通過所有未審核留言並通知",
        )
        # 使用項目級別的模板路徑
        return TemplateResponse(request, "admin/board/message/approve_all_pending_confirmation.html", context)


    # 在 admin 列表頁頂部添加自定義按鈕和統計信息
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        # 統計未審核留言數量
        extra_context['pending_messages_count'] = Message.objects.filter(is_approved=False).count()
        # 統計今日新增留言數量
        from django.utils import timezone
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        extra_context['today_messages_count'] = Message.objects.filter(created_at__gte=today_start).count()
        return super().changelist_view(request, extra_context=extra_context)

    # 移除舊的 admin_actions，因為審核操作現在通過 actions 和直接點擊（如果需要）
    # admin_actions.allow_tags = True
    # admin_actions.short_description = "操作"

    # 覆寫 change_form.html 以添加 "審核並通知" 按鈕
    change_form_template = "admin/board/message/change_form.html"

    # 在保存模型時，如果 is_approved 被勾選且之前未通知，則發送通知
    def save_model(self, request, obj, form, change):
        should_notify = False
        if change and 'is_approved' in form.changed_data and obj.is_approved and not obj.notified:
            # 檢查是否是從未審核變為已審核
            old_obj = Message.objects.get(pk=obj.pk)
            if not old_obj.is_approved:
                should_notify = True

        super().save_model(request, obj, form, change) # 先保存

        if should_notify and obj.author.email: # 確保有 email
            try:
                send_mail(
                    f'您的留言「{obj.subject}」已通過審核',
                    f'您好 {obj.author.username}，\n\n您的留言「{obj.subject}」已通過管理員審核，現在已在網站上顯示。\n\n感謝您的參與！',
                    settings.DEFAULT_FROM_EMAIL,
                    [obj.author.email],
                    fail_silently=False,
                )
                obj.notified = True
                obj.save(update_fields=['notified']) # 只更新 notified 欄位
                messages.success(request, f'已發送郵件通知留言者 {obj.author.username} ({obj.author.email})。')
            except Exception as e:
                messages.error(request, f'在保存後發送郵件通知給 {obj.author.username} ({obj.author.email}) 失敗: {e}')
        elif should_notify and not obj.author.email:
            messages.warning(request, f'留言者 {obj.author.username} 未提供電子郵件，無法在保存後發送通知。')
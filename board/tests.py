from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Message
from .forms import MessageForm, CustomUserCreationForm
from django.core import mail # 用於測試郵件發送
from django.conf import settings
from unittest import mock # Import mock

from django.test import override_settings # Ensure override_settings is imported

# 移除全局 settings.CAPTCHA_TEST_MODE = True

class MessageBoardTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # 創建一個超級使用者和一個普通使用者
        # 使用 @classmethod + setUpTestData 可以為整個測試類創建一次數據，更高效
        cls.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'password123')
        cls.user_with_email = User.objects.create_user('testuserwithemail', 'user@example.com', 'password123')
        cls.user_without_email = User.objects.create_user('testuserwoemail', '', 'password123')


    def setUp(self):
        # 每個測試方法執行前都會執行的設置
        self.client = Client()
        mail.outbox = [] # 清空郵件箱

        # 為每個測試創建獨立的留言，避免測試間相互影響
        self.approved_message = Message.objects.create(
            author=self.user_with_email,
            subject='Approved Subject Test',
            content='Approved content here for test.',
            is_approved=True,
            notified=False # 確保初始未通知
        )
        self.pending_message = Message.objects.create(
            author=self.user_with_email,
            subject='Pending Subject Test',
            content='Pending content here for test.',
            is_approved=False,
            notified=False
        )
        self.pending_message_no_email_user = Message.objects.create(
            author=self.user_without_email,
            subject='Pending No Email User',
            content='Content from user without email.',
            is_approved=False,
            notified=False
        )

    # 1. 模型測試
    def test_message_model_str(self):
        self.assertEqual(str(self.approved_message), f"主題: {self.approved_message.subject} - 留言者: {self.user_with_email.username}")

    def test_message_default_ordering(self):
        # Message 模型中 Meta.ordering = ['-created_at']
        m1 = Message.objects.create(author=self.user_with_email, subject='First', content='1st', is_approved=True)
        m2 = Message.objects.create(author=self.user_with_email, subject='Second', content='2nd', is_approved=True)
        messages = Message.objects.filter(is_approved=True)
        self.assertEqual(messages.first(), m2) # 最新的應該在最前面
        self.assertEqual(messages.last(), self.approved_message) # setUp 中創建的 approved_message 應該更早

    # 2. 視圖測試
    def test_message_list_view_status_code(self):
        response = self.client.get(reverse('message_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'board/message_list.html')

    def test_message_list_view_shows_approved_messages_only(self):
        response = self.client.get(reverse('message_list'))
        self.assertContains(response, self.approved_message.subject)
        self.assertNotContains(response, self.pending_message.subject)

    def test_post_message_view_requires_login(self):
        response = self.client.get(reverse('post_message'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('post_message')}")

    @override_settings(CAPTCHA_TEST_MODE=True)
    def test_post_message_view_logged_in_get(self):
        self.client.login(username=self.user_with_email.username, password='password123')
        response = self.client.get(reverse('post_message'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], MessageForm)
        self.assertTemplateUsed(response, 'board/post_message.html')

    @override_settings(CAPTCHA_TEST_MODE=True)
    @mock.patch('captcha.fields.CaptchaField.clean')
    def test_post_message_view_post_success_and_admin_notification(self, mock_captcha_clean):
        mock_captcha_clean.side_effect = lambda value: value # Bypass captcha validation
        self.client.login(username=self.user_with_email.username, password='password123')
        form_data = {
            'subject': 'Test Post Subject From View',
            'content': 'Test post content from view.',
            'captcha_0': 'dummy_captcha_key', # Captcha hashkey
            'captcha_1': 'PASSED',          # Captcha input value (CAPTCHA_TEST_MODE=True)
        }
        initial_message_count = Message.objects.count()

        # 確保 ADMINS 已配置以測試 mail_admins
        with self.settings(ADMINS=(('Admin', 'admin_test@example.com'),), EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            response = self.client.post(reverse('post_message'), data=form_data, follow=True) # Use follow=True

        self.assertEqual(response.status_code, 200) # Final page after follow should be 200
        self.assertRedirects(response, reverse('message_list'), status_code=302, target_status_code=200)

        # redirect_response = self.client.get(response.url) # No longer needed
        # self.assertEqual(redirect_response.status_code, 200)

        self.assertEqual(Message.objects.count(), initial_message_count + 1)
        new_message = Message.objects.latest('created_at')
        self.assertEqual(new_message.subject, 'Test Post Subject From View')
        self.assertEqual(new_message.author, self.user_with_email)
        self.assertFalse(new_message.is_approved)

        # Check messages on the final page's context
        messages_on_final_page = list(response.context.get('messages', []))
        self.assertEqual(len(messages_on_final_page), 1)
        self.assertEqual(str(messages_on_final_page[0]), '您的留言已成功提交，管理員將盡快審核。')

        # 測試是否有管理員通知郵件被發送
        if settings.ADMINS:
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(f"【新留言待審核】{new_message.subject}", mail.outbox[0].subject)
            self.assertTrue(all(admin_email in mail.outbox[0].to for _, admin_email in settings.ADMINS))

    def test_post_message_view_post_invalid_captcha(self):
        self.client.login(username=self.user_with_email.username, password='password123')
        # 臨時禁用 CAPTCHA_TEST_MODE 以測試無效驗證碼
        # 並確保 EMAIL_BACKEND 是 locmem 以隔離郵件測試
        with self.settings(CAPTCHA_TEST_MODE=False, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            form_data = {
                'subject': 'Test Invalid Captcha From View',
                'content': 'Content here.',
                'captcha_0': 'dummy_captcha_key_invalid', # 這些值在實際驗證時很重要
                'captcha_1': 'WRONG_CAPTCHA', # 錯誤的驗證碼
            }
            # response = self.client.post(reverse('post_message'), data=form_data) # Original line
            # It seems the error is that response.context['form'] is not available if the view doesn't re-render with context
            # Let's check the view's behavior on invalid form
            # board/views.py:
            #    else:
            #        messages.error(request, '表單提交失敗，請檢查您輸入的內容。')
            # else:
            #    form = MessageForm() # GET 請求時，創建空表單
            # return render(request, 'board/post_message.html', {'form': form})
            # The view *does* re-render the form. The issue might be with assertFormError.
            # Let's try to get the form from the context if available.
            post_response = self.client.post(reverse('post_message'), data=form_data)

        self.assertEqual(post_response.status_code, 200) # 應該停留在原頁面，因為表單無效
        # self.assertFormError(response, 'form', 'captcha', '無效的驗證碼') # This was causing AttributeError
        # Let's check the form error more directly from the context if possible
        if 'form' in post_response.context:
            form_in_context = post_response.context['form']
            self.assertIn('captcha', form_in_context.errors)
            self.assertEqual(form_in_context.errors['captcha'][0], 'Invalid CAPTCHA') # Updated to English message
        else:
            # Fallback or fail if form not in context, which would be unexpected
            self.fail("Form not found in response context after invalid POST")

        self.assertTrue(Message.objects.filter(subject='Test Invalid Captcha From View').count() == 0) # 留言未創建
        # 確保在這種情況下沒有發送管理員郵件
        self.assertEqual(len(mail.outbox), 0)


    def test_signup_view_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_view_post_success(self):
        user_count_before = User.objects.count()
        form_data = {
            'username': 'newsignupuser_test',
            'email': 'newsignup_test@example.com',
            'password1': 'complexpassword123_test',
            'password2': 'complexpassword123_test',
        }
        # No Django version check needed for password field names, UserCreationForm internally uses password1 & password2

        response = self.client.post(reverse('signup'), data=form_data, follow=True) # Use follow=True

        # if response_post.status_code != 302 and 'form' in response_post.context: # Old debug
        #     print(f"DEBUG: test_signup_view_post_success form errors: {response_post.context['form'].errors.as_json()}")

        self.assertEqual(response.status_code, 200)  # Final page after follow should be 200
        self.assertRedirects(response, reverse('message_list'), status_code=302, target_status_code=200)

        # response_redirect = self.client.get(response_post.url) # No longer needed
        # self.assertEqual(response_redirect.status_code, 200)

        self.assertEqual(User.objects.count(), user_count_before + 1) # Verify a new user was created

        new_user = User.objects.get(username='newsignupuser_test')
        # Check if the new user is logged in by inspecting the session
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.pk)

        # Verify success message on the final page's context
        messages_on_final_page = list(response.context.get('messages', []))
        self.assertEqual(len(messages_on_final_page), 1)
        self.assertEqual(str(messages_on_final_page[0]), '註冊成功！歡迎加入，您現在已登入。')

    def test_signup_view_when_logged_in(self):
        self.client.login(username=self.user_with_email.username, password='password123')
        response = self.client.get(reverse('signup'))
        self.assertRedirects(response, reverse('message_list')) # 已登入用戶應重定向

    # 3. 表單測試
    @override_settings(CAPTCHA_TEST_MODE=True)
    @mock.patch('captcha.fields.CaptchaField.clean')
    def test_message_form_valid(self, mock_captcha_clean):
        # Configure the mock to return the cleaned value,
        # effectively bypassing the original clean's validation logic
        mock_captcha_clean.side_effect = lambda value: value # For MultiValueField, clean returns a list of cleaned values

        form_data = {
            'subject': 'Form Test Subject',
            'content': 'Form test content.',
            'captcha_0': 'dummy_key',
            'captcha_1': 'PASSED', # This value is now passed to the mock
        }
        form = MessageForm(data=form_data)
        # if not form.is_valid(): # Debugging print, can be removed
        #     print("DEBUG: test_message_form_valid errors:", form.errors.as_json())
        #     print("DEBUG: mock_captcha_clean called:", mock_captcha_clean.called)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())

    @override_settings(CAPTCHA_TEST_MODE=True)
    @mock.patch('captcha.fields.CaptchaField.clean')
    def test_message_form_missing_subject(self, mock_captcha_clean):
        mock_captcha_clean.side_effect = lambda value: value
        form_data = {
            'content': 'Form test content without subject.',
            'captcha_0': 'dummy_key', 'captcha_1': 'PASSED',
        }
        form = MessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        # Django's default error messages might vary slightly by version or locale settings.
        # It's safer to check for the existence of an error rather than exact string if not critical.
        # self.assertTrue(any('required' in e.code for e in form.errors['subject'])) # e.code does not exist for string error
        self.assertTrue(form.errors['subject'])


    def test_custom_user_creation_form_valid(self):
        form_data = {
            'username': 'formuser_test',
            'email': 'formuser_test@example.com',
            'password1': 'anotherpassword123_test', # Main password field used by UserCreationForm
            'password2': 'anotherpassword123_test', # Confirmation password
        }
        # No Django version check needed here as password1/password2 are consistently used internally by UserCreationForm

        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())


    def test_custom_user_creation_form_missing_email(self):
        form_data = {
            'username': 'formuser_no_email_test',
            'password2': 'password123_test',
        }
        from django import VERSION as django_version
        if django_version < (5,0):
            form_data['password1'] = 'password123_test'
        else:
            form_data['password'] = 'password123_test'

        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        # self.assertTrue(any('required' in e.code for e in form.errors['email']))
        self.assertTrue(form.errors['email'])


    # 4. 管理後台測試 (MessageAdmin)
    def test_admin_message_action_mark_approved_and_notify(self):
        self.client.login(username=self.superuser.username, password='password123')
        self.assertFalse(self.pending_message.is_approved)

        message_admin_changelist_url = reverse('admin:board_message_changelist')
        action_data = {
            'action': 'mark_approved_and_notify',
            '_selected_action': [str(self.pending_message.id)],
        }
        response = self.client.post(message_admin_changelist_url, action_data, follow=True)
        self.assertEqual(response.status_code, 200) # Action 後重定向到 changelist

        self.pending_message.refresh_from_db()
        self.assertTrue(self.pending_message.is_approved)

        # 測試郵件通知
        if self.user_with_email.email:
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(f"您的留言「{self.pending_message.subject}」已通過審核", mail.outbox[0].subject)
            self.assertIn(self.user_with_email.email, mail.outbox[0].to)
            self.assertTrue(self.pending_message.notified) # 確保 notified 標記已更新
        else:
            self.assertEqual(len(mail.outbox), 0)

    def test_admin_message_action_mark_approved_user_without_email(self):
        self.client.login(username=self.superuser.username, password='password123')
        self.assertFalse(self.pending_message_no_email_user.is_approved)

        message_admin_changelist_url = reverse('admin:board_message_changelist')
        action_data = {
            'action': 'mark_approved_and_notify',
            '_selected_action': [str(self.pending_message_no_email_user.id)],
        }
        response = self.client.post(message_admin_changelist_url, action_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.pending_message_no_email_user.refresh_from_db()
        self.assertTrue(self.pending_message_no_email_user.is_approved)
        self.assertEqual(len(mail.outbox), 0) # 用戶無郵箱，不應發送郵件
        self.assertFalse(self.pending_message_no_email_user.notified) # notified 應為 False

        # 檢查是否有警告訊息
        messages = list(response.context['messages'])
        self.assertTrue(any(f'留言者 {self.user_without_email.username} 未提供電子郵件，無法發送通知。' in str(m) for m in messages))


    def test_admin_message_action_mark_unapproved(self):
        self.client.login(username=self.superuser.username, password='password123')
        self.assertTrue(self.approved_message.is_approved)
        self.approved_message.notified = True # 假設之前已通知
        self.approved_message.save()

        message_admin_changelist_url = reverse('admin:board_message_changelist')
        action_data = {
            'action': 'mark_unapproved',
            '_selected_action': [str(self.approved_message.id)],
        }
        self.client.post(message_admin_changelist_url, action_data)

        self.approved_message.refresh_from_db()
        self.assertFalse(self.approved_message.is_approved)
        self.assertFalse(self.approved_message.notified) # 取消審核時應重置 notified

    def test_admin_approve_all_pending_view(self):
        self.client.login(username=self.superuser.username, password='password123')
        # 確保至少有一條未審核留言
        self.assertTrue(Message.objects.filter(is_approved=False).exists())

        approve_all_url = reverse('admin:approve_all_pending')
        response_get = self.client.get(approve_all_url) # GET 請求顯示確認頁面
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "確認快速通過所有未審核留言並通知")

        response_post = self.client.post(approve_all_url, {'post': 'yes'}, follow=True) # POST 請求執行操作
        self.assertEqual(response_post.status_code, 200) # 重定向回 changelist
        self.assertFalse(Message.objects.filter(is_approved=False).exists()) # 所有留言應已審核

        # 檢查郵件是否已發送給有 email 的用戶
        # self.pending_message 的作者有 email, self.pending_message_no_email_user 的作者沒有
        num_emails_expected = 1 if self.user_with_email.email else 0
        self.assertEqual(len(mail.outbox), num_emails_expected)
        if num_emails_expected > 0:
             self.assertTrue(any(self.pending_message.subject in email.subject for email in mail.outbox))


    def test_admin_save_model_sends_email_on_approval(self):
        self.client.login(username=self.superuser.username, password='password123')
        message_change_url = reverse('admin:board_message_change', args=[self.pending_message.id])

        self.assertFalse(self.pending_message.is_approved)
        self.assertFalse(self.pending_message.notified)

        # 模擬在 admin 編輯頁面勾選 is_approved 並保存
        # Django admin 的 changeform 提交的數據會包含所有表單字段
        # readonly 字段通常不會被提交，除非它們是 initial data 的一部分
        # 這裡我們只需要提交會改變的字段和必要的控制字段
        post_data = {
            # readonly fields: author, subject, content, created_at
            # editable fields: is_approved, notified
            'is_approved': 'on', # 模擬勾選 CheckboxInput
            # 'notified': '', # 保持為 False (或不傳)
            '_save': 'Save', # 模擬點擊保存按鈕
        }

        # 為了讓 save_model 中的 form.changed_data 正確，
        # 我們需要確保 POST 的數據與 MessageAdmin.form 的字段匹配。
        # MessageAdmin 默認使用 forms.ModelForm。
        # readonly_fields 不會出現在 ModelForm 中，除非自定義了 form。
        # 這裡的 MessageAdmin 沒有自定義 form，所以 is_approved, notified 是表單的一部分。

        response = self.client.post(message_change_url, data=post_data, follow=True)
        self.assertEqual(response.status_code, 200) # 保存後重定向到 changelist

        self.pending_message.refresh_from_db()
        self.assertTrue(self.pending_message.is_approved)

        if self.user_with_email.email:
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(f"您的留言「{self.pending_message.subject}」已通過審核", mail.outbox[0].subject)
            self.assertTrue(self.pending_message.notified)
        else:
            self.assertEqual(len(mail.outbox), 0)

    def tearDown(self):
        # 清理測試中創建的 CaptchaStore 記錄 (如果有的話)
        # from captcha.models import CaptchaStore
        # CaptchaStore.objects.all().delete() # CAPTCHA_TEST_MODE = True 時通常不需要
        pass

# 建議在 settings.py (或測試專用 settings) 中配置：
# EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend' # 測試時使用內存郵件後端
# ADMINS = [('Admin Name', 'admin_test@example.com')] # 用於測試 mail_admins
# MANAGERS = ADMINS
# CAPTCHA_TEST_MODE = True (已在文件頂部設置)

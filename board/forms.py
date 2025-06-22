# board/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from captcha.fields import CaptchaField
from .models import Message
# from django.conf import settings as django_settings # For debugging - Removed

# Debugging CaptchaField - Removed
# class DebugCaptchaField(CaptchaField):
#     def clean(self, value):
#         print(f"DEBUG CaptchaField.clean: CAPTCHA_TEST_MODE = {getattr(django_settings, 'CAPTCHA_TEST_MODE', 'Not Set')}")
#         print(f"DEBUG CaptchaField.clean: value = {value}")
#         try:
#             return super().clean(value)
#         except forms.ValidationError as e:
#             print(f"DEBUG CaptchaField.clean: ValidationError = {e}")
#             raise

class MessageForm(forms.ModelForm):
    captcha = CaptchaField(label="驗證碼") # Reverted to original CaptchaField

    class Meta:
        model = Message
        fields = ['subject', 'content', 'captcha'] # 在表單中包含 captcha 字段
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入主题'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '請輸入留言内容', 'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        is_editing = kwargs.pop('is_editing', False) # 檢查是否為編輯模式
        super().__init__(*args, **kwargs)
        self.fields['subject'].label = "主題"
        self.fields['content'].label = "留言內容"

        if is_editing or self.instance and self.instance.pk: # 如果是編輯現有實例，則移除驗證碼
            if 'captcha' in self.fields:
                del self.fields['captcha']
        # 更新 Meta 中的 fields 列表，如果驗證碼被移除
        if 'captcha' not in self.fields and 'captcha' in self.Meta.fields:
            meta_fields = list(self.Meta.fields)
            meta_fields.remove('captcha')
            self.Meta.fields = meta_fields


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text='請輸入有效的電子郵件地址，用於接收通知。',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'})
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '使用者名稱'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 更新内建字段的 widget 属性以添加 class
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': '使用者名稱'})

        # UserCreationForm 在 Django < 5.0 時使用 password1 和 password2
        # 在 Django >= 5.0 時，UserCreationForm 內部可能仍使用 password1, password2，或者 password 字段本身代表組合字段
        # 為了兼容性和明確性，我們直接引用 UserCreationForm.Meta.fields 來確定密碼字段
        # 然而，直接修改 self.fields['password'] (如果存在) 或 self.fields['password1'] / self.fields['password2'] 更為直接

        from django import VERSION as django_version
        if django_version < (5,0):
            if 'password1' in self.fields:
                self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': '密碼'})
                self.fields['password1'].label = "密碼"
            if 'password2' in self.fields:
                self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': '確認密碼'})
                self.fields['password2'].label = "確認密碼"
        else: # Django 5.0+
            # Django 5.0 UserCreationForm 包含 'password' 字段，它是一個 MultiWidget (PasswordInput + PasswordInput for confirmation)
            # 但其 Meta.fields 仍然是 ('username', 'password')
            # 我們需要分別處理 password1 和 password2 （如果它們是分開的字段）
            # 或者如果 'password' 是一個整體字段，則修改它。
            # 實際上，UserCreationForm 內部仍然會創建 password1 和 password2 字段供 clean 方法使用
            # 但表單上顯示的是一個 'password' 字段（如果沒有自定義）。
            # 我們的 CustomUserCreationForm 繼承了 UserCreationForm.Meta，所以 fields 包含 'username'
            # 並且我們添加了 'email'。 UserCreationForm.Meta.fields 預設是 ('username',)
            # UserCreationForm 本身會添加 password1 和 password2 字段。
            # 因此，我們應該檢查 self.fields 是否包含 password1 和 password2。
            if 'password' in self.fields and isinstance(self.fields['password'].widget, forms.PasswordInput):
                 # 這是 Django 5.0+ UserCreationForm 的情況，它有一個 'password' 字段，但 UserCreationForm 內部會生成 password1 和 password2
                 # 但是我們 CustomUserCreationForm 繼承 UserCreationForm.Meta，然後添加 'email'
                 # UserCreationForm 自身會處理 password1 和 password2。我們只需要確保它們有 class。
                 # 最好的方式是 UserCreationForm 已經處理了 password1 和 password2 的 widget
                 # 我們只需要修改它們的 label。
                 # UserCreationForm 的 fields 屬性會包含 password1 和 password2
                 pass # 通常 UserCreationForm 已經處理了 password 字段的 widget 和 label
                 # 但是為了確保 class，我們還是可以這樣做：
            if self.fields.get('password1'):
                 self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': '密碼'})
                 self.fields['password1'].label = "密碼"
            if self.fields.get('password2'):
                 self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': '確認密碼'})
                 self.fields['password2'].label = "確認密碼"

        # 更改字段標籤
        self.fields['username'].label = "使用者帳號"
        self.fields['email'].label = "電子郵件"
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm


class InviteUserCreationForm(UserCreationForm):
    invite_code = forms.CharField(
        label="招待コード",
        required=True,
        widget=forms.PasswordInput(),
        help_text="許可された人のみ登録できます。",
    )

    def clean_invite_code(self):
        code = self.cleaned_data.get("invite_code", "")
        expected = getattr(settings, "INVITE_CODE", "")
        if settings.DEBUG and not expected:
            return code
        if not expected or code != expected:
            raise forms.ValidationError("招待コードが正しくありません。")
        return code

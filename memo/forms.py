from django import forms

from .models import QuickMemo


class QuickMemoForm(forms.ModelForm):
    class Meta:
        model = QuickMemo
        fields = ["title", "body"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "空欄なら本文先頭20文字を自動設定"}
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": "思いついたことをそのまま入力",
                    "required": True,
                }
            ),
        }


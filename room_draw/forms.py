from django import forms

from .services import PARTICIPANT_COUNT, name_key


class RosterForm(forms.Form):
    roster = forms.CharField(
        max_length=4000,
        error_messages={
            "required": "参加者の名前を1行に1人ずつ入力してください。",
            "max_length": "名簿の入力が長すぎます。名前だけを入力してください。",
        },
    )

    def clean_roster(self):
        participants = [
            line.strip()
            for line in self.cleaned_data["roster"].splitlines()
            if line.strip()
        ]
        if len(participants) != PARTICIPANT_COUNT:
            raise forms.ValidationError(
                f"参加者を{PARTICIPANT_COUNT}人入力してください（現在{len(participants)}人）。"
            )
        if any(len(name) > 80 for name in participants):
            raise forms.ValidationError("名前は1人あたり80文字以内で入力してください。")
        if len({name_key(name) for name in participants}) != len(participants):
            raise forms.ValidationError(
                "名前が重複しています。同姓同名の場合は区別できる表記にしてください。"
            )
        return participants

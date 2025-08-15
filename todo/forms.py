from django import forms
from .models import Schedule, Task, ActionItem 

class ActionItemForm(forms.ModelForm):
    class Meta:
        model = ActionItem
        # ↓↓↓ fields に4つ追加します ↓↓↓
        fields = ['title', 'action_type', 'due_date', 'text1', 'text2', 'text3']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'action_type': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # ↓↓↓ widget を3つ追加します ↓↓↓
            'text1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'text2': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'text3': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'title': 'タイトル',
            'action_type': '種類',
            'due_date': '期日',
            # ↓↓↓ label を3つ追加します ↓↓↓
            'text1': '目標 (Specific)',
            'text2': '測定可能 (Measurable)',
            'text3': '達成可能 (Achievable)',
        }


class ScheduleForm(forms.ModelForm):
    
    action_item = forms.ModelChoiceField(
        # 変更前: is_scheduled=False
        # 変更後: completed=False と owner=request.user を追加（ビュー側で設定）
        queryset=ActionItem.objects.none(), # ← まずは空にしておく
        label="アクション",
        empty_label="選択してください"
    )

    def __init__(self, *args, **kwargs):
        # requestオブジェクトを受け取るためにpopで取り出す
        user = kwargs.pop('user', None) 
        super(ScheduleForm, self).__init__(*args, **kwargs)
        if user:
            # ログインユーザーが所有する、未完了のActionItemのみを選択肢にする
            self.fields['action_item'].queryset = ActionItem.objects.filter(
                owner=user, 
                completed=False
            )

    class Meta:
        model = Schedule
        # ↓↓↓ fields の内容を大幅に変更します ↓↓↓
        fields = [
            'action_item', # 'title' などの代わりに追加
            'start_time',
            'end_time',
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

# TaskForm は変更なし
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title']
        labels = {
            'title': '',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '新しいタスクを入力してください'
            }),
        }
from django import forms
from .models import Schedule, Task, ActionItem, ActionCategory

class ActionCategoryForm(forms.ModelForm):
    class Meta:
        model = ActionCategory
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'カテゴリ名（例: 研究）'}),
            # type='color' にするとブラウザのカラーピッカーが使えます
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': '色を選択'}),
        }

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
    class Meta:
        model = Schedule
        # action_item を削除し、action_category を追加
        fields = ['action_category', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'action_category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            # ログインユーザーのカテゴリだけを表示する
            self.fields['action_category'].queryset = ActionCategory.objects.filter(owner=self.user)
            self.fields['action_category'].empty_label = "カテゴリを選択してください"

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
from django import forms
from .models import Schedule, Task, ActionItem, ActionCategory

class ActionCategoryForm(forms.ModelForm):
    class Meta:
        model = ActionCategory
        # track_pages を追加
        fields = ['name', 'color', 'track_pages'] 
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'カテゴリ名（例: 読書）'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            # チェックボックスのデザイン調整
            'track_pages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ActionItemForm(forms.ModelForm):
    class Meta:
        model = ActionItem
        fields = ['category', 'title', 'due_date', 'text1', 'text2', 'text3']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'text1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'text2': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'text3': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'category': 'カテゴリ',
            'title': 'タイトル',
            'due_date': '期限',
            'text1': '目的 (Specific)',
            'text2': '測定可能 (Measurable)',
            'text3': '達成可能 (Achievable)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = ActionCategory.objects.filter(owner=user)


class PrivateActionItemForm(ActionItemForm):
    class Meta(ActionItemForm.Meta):
        fields = ['title', 'due_date', 'text1', 'text2', 'text3']


class ReadingActionItemForm(forms.ModelForm):
    class Meta:
        model = ActionItem
        fields = ['title', 'theme', 'reading_purpose', 'book_image', 'book_author']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'theme': forms.TextInput(attrs={'class': 'form-control'}),
            'reading_purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'book_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'book_author': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': '書籍タイトル',
            'theme': 'テーマ',
            'reading_purpose': '読む目的',
            'book_image': '書籍画像',
            'book_author': '作者',
        }

class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        # action_item をフィールドに追加
        fields = ['action_category', 'action_item', 'start_page', 'end_page', 'page_count', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'action_category': forms.Select(attrs={'class': 'form-select', 'id': 'id_action_category'}),
            'start_page': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_start_page', 'placeholder': '開始'}),
            'end_page': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_end_page', 'placeholder': '終了'}),
            'page_count': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_page_count', 'placeholder': '読んだページ数'}),
            # ★追加: 具体的な内容（本など）を選ぶプルダウン
            'action_item': forms.Select(attrs={'class': 'form-select', 'id': 'id_action_item'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['action_category'].queryset = ActionCategory.objects.filter(owner=self.user)
            # ActionItemもユーザーのもので絞り込む（必須ではないのでrequired=False）
            self.fields['action_item'].queryset = ActionItem.objects.filter(owner=self.user)
            self.fields['action_item'].required = False
            self.fields['action_item'].empty_label = "（指定なし）"

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

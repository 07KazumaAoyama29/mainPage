from django import forms
from .models import Knowledge, Tag, Comment

class KnowledgeForm(forms.ModelForm):
    class Meta:
        model = Knowledge
        fields = ['title', 'content', 'parent', 'tags', 'is_public']  # 'is_public'フィールドを追加
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
            'is_public': forms.CheckboxInput(), # チェックボックスとして表示
        }

# CommentFormクラスの追加
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'コメント'}
        widgets = {'text': forms.Textarea(attrs={'cols': 80})}

# TagFormクラスの追加
class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
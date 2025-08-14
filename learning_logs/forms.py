from django import forms
from .models import Knowledge, Tag, Comment

class KnowledgeForm(forms.ModelForm):
    class Meta:
        model = Knowledge
        fields = ['title', 'content', 'parent', 'tags', 'is_public', 'knowledge_type', 'page', 'size', 'author', 'isbn', 'genre']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
            'is_public': forms.CheckboxInput(),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'コメント'}
        widgets = {'text': forms.Textarea(attrs={'cols': 80})}

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
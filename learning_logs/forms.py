from django import forms

from .models import Comment, Knowledge, KnowledgeImage, Tag


class KnowledgeForm(forms.ModelForm):
    class Meta:
        model = Knowledge
        fields = [
            'title',
            'content',
            'parent',
            'tags',
            'is_public',
            'knowledge_type',
            'page',
            'size',
            'author',
            'isbn',
            'genre',
        ]
        labels = {
            'title': 'タイトル',
            'content': '本文',
            'parent': '親ノート',
            'tags': 'タグ',
            'is_public': '公開する',
            'knowledge_type': 'ノートの種類',
            'page': 'ページ数',
            'size': '1ページの大きさ',
            'author': '著者名',
            'isbn': 'ISBN',
            'genre': 'ジャンル',
        }
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 18}),
            'tags': forms.CheckboxSelectMultiple(),
            'is_public': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['knowledge_type'].choices = [
            ('normal', '一般'),
            ('book', '書籍'),
            ('paper', '論文'),
        ]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'コメント'}
        widgets = {'text': forms.Textarea(attrs={'cols': 80, 'class': 'form-control', 'rows': 3})}


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        labels = {'name': 'タグ名'}

class KnowledgeImageForm(forms.ModelForm):
    class Meta:
        model = KnowledgeImage
        fields = ['image']
        labels = {'image': '\u753b\u50cf'}
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

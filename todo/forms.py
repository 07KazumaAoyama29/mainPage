# forms.py

from django import forms
from .models import Todo

# TodoFormをModelFormに書き換え
class TodoForm(forms.ModelForm):
    class Meta:
        model = Todo
        fields = ['title', 'task_type', 'description', 'text1', 'text2', 'text3', 'text4', 'deadline', 'int1']
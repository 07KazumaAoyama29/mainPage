from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import UpdateView, DeleteView
from django.utils import timezone
from django.forms import ModelForm
from django.urls import reverse_lazy
from .models import Todo
from .forms import TodoForm
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class TodoUpdate(LoginRequiredMixin, UpdateView):
    model = Todo
    form_class = TodoForm
    template_name = 'todo/todo_form.html'
    success_url = reverse_lazy("todo:tasklist")

class TodoDelete(LoginRequiredMixin, DeleteView):
    model = Todo
    context_object_name = "task"
    success_url = reverse_lazy("todo:tasklist")
    template_name = 'todo/todo_confirm_delete.html'

def state(request, pk):
    if request.method == 'POST':
        data = Todo.objects.get(id = pk)
        data.int2 = 2 # Done
        data.save()
    return redirect(to='todo:tasklist')

def taskList(request):
    tlist = Todo.objects.filter(Q(int2=0)|Q(int2=1)).order_by('deadline')
    my_dict = {
        "tasks": tlist,
    }
    return render(request, "todo/todo_list.html", my_dict)

def create(request):
    message = ''
    if (request.method == 'POST'):
        form = TodoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(to='todo:tasklist')
        else: message = '再入力して下さい'
    my_dict = {
        "form": TodoForm(),
        'message': message,
    }
    return render(request, "todo/todo_form.html", my_dict)
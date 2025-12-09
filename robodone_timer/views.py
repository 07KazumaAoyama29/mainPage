from django.shortcuts import render

def index(request):
    return render(request, 'robodone_timer/index.html')
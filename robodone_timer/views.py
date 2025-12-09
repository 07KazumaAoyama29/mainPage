from django.shortcuts import render

def menu(request):
    return render(request, 'robodone_timer/menu.html') # 作成したメニュー画面

def build_timer(request):
    return render(request, 'robodone_timer/build_timer.html') # ロボット制作タイマー

def pair_timer(request):
    return render(request, 'robodone_timer/index.html') # 交代タイマー（index.htmlの場合）
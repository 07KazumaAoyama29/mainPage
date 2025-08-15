from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta

from .models import Schedule, Task, ActionItem
from .forms import ScheduleForm, TaskForm, ActionItemForm

import json

@login_required
def calendar_view(request):
    """カレンダーページ本体を表示するビュー"""
    return render(request, "todo/calendar.html")

@login_required
def calendar_events(request):
    """カレンダーに表示するイベント（スケジュール）をJSON形式で返すビュー"""
    # ↓ この行に .select_related('action_item') を追加するとパフォーマンスが向上します
    COLOR_MAP = {
        '読書': '#28a745',   # 青
        '研究': '#dc3545',   # 赤
        'バイト': '#ffc107',   # 黄
        '娯楽': '#007bff',   # 緑
        'ジム': '#fd7e14',   # オレンジ
        'その他': '#6c757d',  # グレー
    }
    schedules = Schedule.objects.filter(owner=request.user).select_related('action_item')
    events = []
    for schedule in schedules:
        tasks = schedule.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(completed=True).count()
        if total_tasks > 0:
            progress_percentage = int((completed_tasks / total_tasks) * 100)
        else:
            progress_percentage = 100

        events.append({
            'id': schedule.pk,
            'title': f"{schedule.action_item.title} ({progress_percentage}%)", # schedule.title -> schedule.action_item.title
            'start': schedule.start_time.isoformat(),
            'end': schedule.end_time.isoformat(),
            'url': reverse_lazy('todo:schedule_detail', kwargs={'pk': schedule.pk}),
            'backgroundColor': COLOR_MAP.get(schedule.action_item.action_type, '#6c757d')
        })
    return JsonResponse(events, safe=False)

@login_required
def schedule_create_form(request): # 引数から *args, **kwargs を削除
    """モーダルに表示するための空のスケジュール作成フォームを返すビュー"""
    
    # --- ▼▼▼ この時間処理のブロックを復活させます ▼▼▼ ---
    start_time_str = request.GET.get('start_time')
    initial_data = {}
    if start_time_str:
        try:
            # タイムゾーン情報などを切り捨てて、"YYYY-MM-DDTHH:MM:SS"の部分だけを使う
            clean_start_time_str = start_time_str[:19]
            start_time_obj = datetime.fromisoformat(clean_start_time_str)
            end_time_obj = start_time_obj + timedelta(hours=1)
            initial_data['start_time'] = start_time_obj.strftime('%Y-%m-%dT%H:%M')
            initial_data['end_time'] = end_time_obj.strftime('%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            # エラーが発生しても処理を続ける
            pass
    # --- ▲▲▲ ここまで復活 ▲▲▲ ---

    # フォームを初期化
    form = ScheduleForm(initial=initial_data, user=request.user)
    
    # 本番環境のデータベースエラーを回避するための重要な一行
    form.fields['action_item'].choices = list(form.fields['action_item'].choices)
    
    context = {'form': form}
    return render(request, 'todo/partials/schedule_create_form.html', context)

@login_required
@require_POST
def schedule_create(request):
    """スケジュールを作成し、ActionItemを「スケジュール済み」に更新するビュー"""
    form = ScheduleForm(request.POST, user=request.user)
    if form.is_valid():
        new_schedule = form.save(commit=False)
        new_schedule.owner = request.user
        new_schedule.save()

        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response
    else:
        context = {'form': form}
        return render(request, 'todo/partials/schedule_create_form.html', context)

@login_required
@require_POST
def reorder_tasks(request):
    """タスクの並び順を更新する"""
    task_pks = request.POST.getlist('task_pks') # HTMXから送信されたタスクの主キーリスト
    for index, pk in enumerate(task_pks):
        try:
            task = Task.objects.get(pk=pk, owner=request.user)
            task.position = index
            task.save()
        except Task.DoesNotExist:
            # 他人のタスクを操作しようとした場合などは無視
            continue
    return HttpResponse(status=204) # 更新成功、コンテンツは返さない

@login_required
def schedule_edit_form(request, pk):
    """モーダルに表示するための、データが入ったスケジュール編集フォームを返す"""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    form = ScheduleForm(instance=schedule, user=request.user)
    
    # --- ▼▼▼ この一行を追加 ▼▼▼ ---
    # データベースエラーを回避するため、選択肢をここで一度に読み込む
    form.fields['action_item'].choices = list(form.fields['action_item'].choices)

    context = {'form': form, 'schedule': schedule}
    return render(request, 'todo/partials/schedule_edit_form.html', context)

@login_required
@require_POST
def schedule_update(request, pk):
    """スケジュールを更新する"""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    # フォームにuserを渡すのを忘れない
    form = ScheduleForm(request.POST, instance=schedule, user=request.user)
    if form.is_valid():
        form.save()
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response
    else:
        context = {'form': form, 'schedule': schedule}
        return render(request, 'todo/partials/schedule_edit_form.html', context)

@login_required
@require_POST
def schedule_update_time(request):
    """ドラッグ&ドロップでスケジュールの時間を更新する"""
    try:
        # request.bodyをデコードしてJSONとして読み込む
        data = json.loads(request.body.decode('utf-8'))
        schedule_id = data.get('id')
        new_start = data.get('start')
        new_end = data.get('end')

        schedule = get_object_or_404(Schedule, pk=schedule_id, owner=request.user)

        schedule.start_time = new_start
        # new_endがNoneの場合もあるので、その場合は既存の終了時刻を使うか、開始時刻から計算する
        schedule.end_time = new_end if new_end else schedule.start_time + timedelta(hours=1)
        schedule.save()

        return JsonResponse({'status': 'success'})
    except Exception as e:
        # エラーの詳細をログに出力するとデバッグに役立つ
        print(f"Error in schedule_update_time: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def schedule_delete(request, pk):
    """スケジュールを削除する"""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    schedule.delete()
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('todo:calendar')
    return response

@login_required
def schedule_detail(request, pk):
    """スケジュールの詳細ページを表示するビュー"""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)

    # --- ↓↓↓ ここからPOSTリクエストの処理を追加 ↓↓↓ ---
    if request.method == 'POST':
        # 新しいタスクを作成するリクエストの場合
        form = TaskForm(data=request.POST)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.owner = request.user
            new_task.schedule = schedule # このスケジュールの子として設定
            new_task.save()
            return redirect('todo:schedule_detail', pk=pk)
    # --- ↑↑↑ ここまで追加 ↑↑↑ ---

    tasks = schedule.tasks.order_by('completed', 'position')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()

    if total_tasks > 0:
        progress_percentage = (completed_tasks / total_tasks) * 100
    else:
        progress_percentage = 100

    form = TaskForm() # 空のタスク作成フォームを準備
    context = {
        'schedule': schedule,
        'tasks': tasks,
        'progress_percentage': progress_percentage,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'form': form, # フォームをテンプレートに渡す
    }
    return render(request, 'todo/schedule_detail.html', context)


@login_required
@require_POST # POSTリクエストのみを受け付ける
def toggle_task(request, pk):
    """タスクの完了状態を切り替えるビュー"""
    task = get_object_or_404(Task, pk=pk, owner=request.user)

    # completedフィールドの値を反転させる (True -> False, False -> True)
    task.completed = not task.completed
    task.save()

    # 詳細ページ全体を再描画して返す
    schedule = task.schedule
    tasks = schedule.tasks.order_by('completed', 'position')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    if total_tasks > 0:
        progress_percentage = (completed_tasks / total_tasks) * 100
    else:
        progress_percentage = 100

    form = TaskForm()
    context = {
        'schedule': schedule,
        'tasks': tasks,
        'progress_percentage': progress_percentage,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'form': form,
    }
    return render(request, 'todo/partials/task_list_and_progress.html', context)

@login_required
@require_POST
def toggle_action_item_completion(request, pk):
    """ActionItemの完了状態を切り替えるビュー"""
    action_item = get_object_or_404(ActionItem, pk=pk, owner=request.user)
    action_item.completed = not action_item.completed
    action_item.save()
    
    # 部分テンプレートを更新して返す
    return render(request, 'todo/partials/action_item_list_item.html', {'item': action_item})

@login_required
def action_item_detail(request, pk):
    """
    ActionItemの詳細ページ。
    もしスケジュール済みなら、関連するスケジュールの詳細ページにリダイレクトする。
    未スケジュールなら、ActionItem自体の情報を表示する。
    """
    action_item = get_object_or_404(ActionItem, pk=pk, owner=request.user)

    schedules = action_item.schedules.all().order_by('start_time').prefetch_related('tasks')

    context = {
        'action_item': action_item,
        'schedules': schedules
    }
    return render(request, 'todo/action_item_detail.html', context)

@login_required
def action_item_list(request):
    """やることリスト（ActionItem）の一覧ページ（絞り込み機能付き）"""
    
    action_items = ActionItem.objects.filter(owner=request.user)

    filter_param = request.GET.get('filter')
    if filter_param == 'completed':
        action_items = action_items.filter(completed=True)
    elif filter_param == 'incomplete':
        action_items = action_items.filter(completed=False)

    context = {
        'action_items': action_items.order_by('completed', 'due_date', 'pk')
    }

    if request.headers.get('HX-Request'):
        return render(request, 'todo/partials/action_item_list_content.html', context)
    
    return render(request, 'todo/action_item_list.html', context)

@login_required
def action_item_create_form(request):
    """モーダルに表示するための、空のActionItem作成フォームを返す"""
    form = ActionItemForm()
    return render(request, 'todo/partials/action_item_form.html', {'form': form})

@login_required
@require_POST
def action_item_create(request):
    """ActionItemを作成する"""
    form = ActionItemForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.owner = request.user
        item.save()
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true' # ページ全体をリフレッシュ
        return response
    return render(request, 'todo/partials/action_item_form.html', {'form': form})

@login_required
def action_item_edit_form(request, pk):
    """モーダルに表示するための、データが入ったActionItem編集フォームを返す"""
    item = get_object_or_404(ActionItem, pk=pk, owner=request.user)
    form = ActionItemForm(instance=item)
    return render(request, 'todo/partials/action_item_form.html', {'form': form, 'item': item})

@login_required
@require_POST
def action_item_update(request, pk):
    """ActionItemを更新する"""
    item = get_object_or_404(ActionItem, pk=pk, owner=request.user)
    form = ActionItemForm(request.POST, instance=item)
    if form.is_valid():
        form.save()
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true' # ページ全体をリフレッシュ
        return response
    return render(request, 'todo/partials/action_item_form.html', {'form': form, 'item': item})

@login_required
@require_POST # Django 4.1以降では @require_http_methods(["DELETE"]) が推奨
def action_item_delete(request, pk):
    """ActionItemを削除する"""
    item = get_object_or_404(ActionItem, pk=pk, owner=request.user)
    item.delete()
    response = HttpResponse(status=204)
    response['HX-Refresh'] = 'true' # ページ全体をリフレッシュ
    return response


@login_required
def task_edit_form(request, pk):
    """タスクのタイトルをインラインで編集するためのフォームを返す"""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = TaskForm(instance=task)
    # 既存のタスク表示部分と、編集フォームを切り替えるためのコンテキスト
    return render(request, 'todo/partials/task_item.html', {'task': task, 'edit_form': form})

@login_required
@require_POST
def task_update(request, pk):
    """タスクのタイトルを更新する"""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = TaskForm(request.POST, instance=task)
    if form.is_valid():
        form.save()
        # 更新が成功したら、通常のタスク表示に戻す
        return render(request, 'todo/partials/task_item.html', {'task': task})
    # バリデーションエラーがあったら、エラーメッセージ付きのフォームを再表示
    return render(request, 'todo/partials/task_item.html', {'task': task, 'edit_form': form})

@login_required
@require_POST # Django 4.1以降では @require_http_methods(["DELETE"])
def task_delete(request, pk):
    """タスクを削除する"""
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.delete()
    # 削除が成功したら、空のHTTPレスポンスを返す（HTMXがこの要素をDOMから削除する）
    return HttpResponse()
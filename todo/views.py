from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta

from .models import Schedule, Task
from .forms import ScheduleForm, TaskForm

@login_required
def calendar_view(request):
    """カレンダーページ本体を表示するビュー"""
    return render(request, "todo/calendar.html")

@login_required
def calendar_events(request):
    """カレンダーに表示するイベント（スケジュール）をJSON形式で返すビュー"""
    schedules = Schedule.objects.filter(owner=request.user)
    events = []
    for schedule in schedules:

        # --- ↓↓↓ このブロックを丸ごと追加します ↓↓↓ ---
        # 各スケジュールの進捗率を計算
        tasks = schedule.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(completed=True).count()
        if total_tasks > 0:
            progress_percentage = int((completed_tasks / total_tasks) * 100)
        else:
            progress_percentage = 100
        # --- ↑↑↑ ここまで追加 ↑↑↑ ---

        events.append({
            'id': schedule.pk,
            # ↓ タイトルに進捗率を追加
            'title': f"{schedule.title} ({progress_percentage}%)",
            'start': schedule.start_time.isoformat(),
            'end': schedule.end_time.isoformat(),
            'url': reverse_lazy('todo:schedule_detail', kwargs={'pk': schedule.pk})
        })
    return JsonResponse(events, safe=False)

@login_required
def schedule_create_form(request):
    """モーダルに表示するための空のスケジュール作成フォームを返すビュー"""
    start_time_str = request.GET.get('start_time')
    initial_data = {}
    if start_time_str:
        try:
            start_time_obj = datetime.fromisoformat(start_time_str)
            end_time_obj = start_time_obj + timedelta(hours=1)
            initial_data['start_time'] = start_time_obj.strftime('%Y-%m-%dT%H:%M')
            initial_data['end_time'] = end_time_obj.strftime('%Y-%m-%dT%H:%M')
        except ValueError:
            pass
    form = ScheduleForm(initial=initial_data)
    context = {'form': form}
    return render(request, 'todo/partials/schedule_create_form.html', context)

@login_required
def schedule_create(request):
    """スケジュールを作成するビュー"""
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
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
    return redirect('todo:calendar')

@login_required
def schedule_edit_form(request, pk):
    """モーダルに表示するための、データが入ったスケジュール編集フォームを返すビュー"""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    form = ScheduleForm(instance=schedule)
    context = {'form': form, 'schedule': schedule}
    return render(request, 'todo/partials/schedule_edit_form.html', context)

@login_required
def schedule_update(request, pk):
    """スケジュールを更新するビュー"""
    schedule = get_object_or_404(Schedule, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Refresh'] = 'true'
            return response
        else:
            context = {'form': form, 'schedule': schedule}
            return render(request, 'todo/partials/schedule_edit_form.html', context)
    return redirect('todo:calendar')

@login_required
@require_POST
def schedule_update_time(request):
    """ドラッグ&ドロップでスケジュールの時間を更新する"""
    try:
        data = json.loads(request.body)
        schedule_id = data.get('id')
        new_start = data.get('start')
        new_end = data.get('end')

        schedule = get_object_or_404(Schedule, pk=schedule_id, owner=request.user)

        schedule.start_time = new_start
        schedule.end_time = new_end
        schedule.save()

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

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

    tasks = schedule.tasks.all()
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
    tasks = schedule.tasks.all()
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
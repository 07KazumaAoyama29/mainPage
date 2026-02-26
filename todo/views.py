from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.utils import timezone

from datetime import datetime, timedelta, date

from .models import Schedule, Task, ActionItem, ActionCategory, PeriodicTask
from .forms import ScheduleForm, TaskForm, ActionItemForm, ActionCategoryForm

import json
import calendar


def _build_periodic_task_items(user):
    today = date.today()
    periodic_tasks = PeriodicTask.objects.filter(owner=user).order_by('id')
    items = []
    for task in periodic_tasks:
        if task.last_done:
            days_since = (today - task.last_done).days
            days_display = f"{days_since}日"
        else:
            days_since = None
            days_display = "未実施"
        is_overdue = (days_since is None) or (days_since > task.interval_days)
        items.append({
            'id': task.id,
            'title': task.title,
            'interval_days': task.interval_days,
            'last_done': task.last_done,
            'days_display': days_display,
            'is_overdue': is_overdue,
            'days_since': days_since,
        })

    items.sort(key=lambda item: (
        not item['is_overdue'],
        -(item['days_since'] or 0),
        item['title'].lower()
    ))
    return items


def _get_or_create_today_schedule(user):
    today = timezone.localdate()
    today_title = "\u4eca\u65e5\u306e\u30bf\u30b9\u30af"
    schedule = Schedule.objects.filter(
        owner=user,
        title_override=today_title,
        start_time__date=today
    ).first()
    if schedule:
        return schedule

    start_time = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_time = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    return Schedule.objects.create(
        owner=user,
        title_override=today_title,
        start_time=start_time,
        end_time=end_time,
    )

@login_required
def calendar_view(request):
    """カレンダーページ"""
    return render(request, "todo/calendar.html")


@login_required
def today_tasks_setup(request):
    schedule = _get_or_create_today_schedule(request.user)

    if request.method == 'POST':
        form = TaskForm(data=request.POST)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.owner = request.user
            new_task.schedule = schedule
            new_task.save()
            return redirect('todo:today_tasks_setup')

    tasks = schedule.tasks.order_by('completed', 'position')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    if total_tasks > 0:
        progress_percentage = (completed_tasks / total_tasks) * 100
    else:
        progress_percentage = 100

    context = {
        'schedule': schedule,
        'tasks': tasks,
        'progress_percentage': progress_percentage,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'form': TaskForm(),
        'task_form_action': reverse('todo:today_tasks_setup'),
        'periodic_tasks': _build_periodic_task_items(request.user),
    }
    return render(request, 'todo/today_setup.html', context)

@login_required
def calendar_events(request):
    """カレンダーに表示するイベント（スケジュール）をJSON形式で返すビュー"""
    # select_related を action_category に変更
    schedules = Schedule.objects.filter(owner=request.user).select_related('action_category')
    events = []
    
    for schedule in schedules:
        tasks = schedule.tasks.all()
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(completed=True).count()
        if total_tasks > 0:
            progress_percentage = int((completed_tasks / total_tasks) * 100)
        else:
            progress_percentage = 100

        # タイトルと色を新しいカテゴリから取得
        # データ移行済みなので action_category は必ずあるはずですが、念のため安全策をとります
        title_text = "未分類"
        bg_color = "#6c757d"
        
        if schedule.action_category:
            title_text = schedule.action_category.name
            bg_color = schedule.action_category.color
        
        # ★追加: 具体的なアイテムが設定されていれば、タイトルに追加する
        if schedule.action_item:
            title_text += f": {schedule.action_item.title}"

        # ページ数があればそれも表示しちゃう？（お好みで）
        if schedule.page_count:
            title_text += f" ({schedule.page_count}p)"

            if getattr(schedule, 'title_override', None):
                title_text = schedule.title_override

    events.append({
            'id': schedule.pk,
            'title': title_text, # 進捗率(%)を表示したい場合はここに f"{title_text} ({progress_percentage}%)"
            'start': schedule.start_time.isoformat(),
            'end': schedule.end_time.isoformat(),
            'url': reverse_lazy('todo:schedule_detail', kwargs={'pk': schedule.pk}),
            'backgroundColor': bg_color,
            'borderColor': bg_color,
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

    categories = ActionCategory.objects.filter(owner=request.user)
    track_pages_map = {cat.id: cat.track_pages for cat in categories}
    
    items_by_category = {}
    action_items = ActionItem.objects.filter(owner=request.user).select_related('category')
    
    for item in action_items:
        # カテゴリが設定されている場合のみ
        if item.category:
            cat_id = item.category.id
            if cat_id not in items_by_category:
                items_by_category[cat_id] = []
            items_by_category[cat_id].append({'id': item.id, 'title': item.title})

    context = {
        'form': form,
        'track_pages_map': json.dumps(track_pages_map),
        'items_by_category': json.dumps(items_by_category), # ★JSONで渡す
    }
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

    categories = ActionCategory.objects.filter(owner=request.user)
    track_pages_map = {cat.id: cat.track_pages for cat in categories}

    items_by_category = {}
    action_items = ActionItem.objects.filter(owner=request.user).select_related('category')
    for item in action_items:
        if item.category:
            cat_id = item.category.id
            if cat_id not in items_by_category:
                items_by_category[cat_id] = []
            items_by_category[cat_id].append({'id': item.id, 'title': item.title})

    context = {
        'form': form, 
        'schedule': schedule,
        'track_pages_map': json.dumps(track_pages_map),
        'items_by_category': json.dumps(items_by_category), # ★追加
    }
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
        'task_form_action': reverse('todo:schedule_detail', kwargs={'pk': schedule.pk}),
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
    if getattr(schedule, 'title_override', '') == "\u4eca\u65e5\u306e\u30bf\u30b9\u30af":
        task_form_action = reverse('todo:today_tasks_setup')
    else:
        task_form_action = reverse('todo:schedule_detail', kwargs={'pk': schedule.pk})
    context = {
        'schedule': schedule,
        'tasks': tasks,
        'progress_percentage': progress_percentage,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'form': form,
        'task_form_action': task_form_action,
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

@login_required
def category_list(request):
    """カテゴリの一覧ページ"""
    categories = ActionCategory.objects.filter(owner=request.user).order_by('id')
    context = {'categories': categories}
    return render(request, 'todo/category_list.html', context)

@login_required
def category_create_form(request):
    """作成フォーム（モーダル用）"""
    form = ActionCategoryForm()
    return render(request, 'todo/partials/category_form.html', {'form': form})

@login_required
@require_POST
def category_create(request):
    """カテゴリ作成処理"""
    form = ActionCategoryForm(request.POST)
    if form.is_valid():
        category = form.save(commit=False)
        category.owner = request.user
        category.save()
        # 成功したらリフレッシュ
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response
    return render(request, 'todo/partials/category_form.html', {'form': form})

@login_required
def category_edit_form(request, pk):
    """編集フォーム（モーダル用）"""
    category = get_object_or_404(ActionCategory, pk=pk, owner=request.user)
    form = ActionCategoryForm(instance=category)
    return render(request, 'todo/partials/category_form.html', {'form': form, 'category': category})

@login_required
@require_POST
def category_update(request, pk):
    """カテゴリ更新処理"""
    category = get_object_or_404(ActionCategory, pk=pk, owner=request.user)
    form = ActionCategoryForm(request.POST, instance=category)
    if form.is_valid():
        form.save()
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response
    return render(request, 'todo/partials/category_form.html', {'form': form, 'category': category})

@login_required
@require_POST
def category_delete(request, pk):
    """カテゴリ削除処理"""
    category = get_object_or_404(ActionCategory, pk=pk, owner=request.user)
    category.delete()
    response = HttpResponse(status=204)
    response['HX-Refresh'] = 'true'
    return response

@login_required
def weekly_summary(request):
    # 1. 表示する基準日を決める
    date_str = request.GET.get('date')
    if date_str:
        try:
            # URLから渡された日付をパース
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
    else:
        # 指定がなければ今日
        target_date = date.today()

    # 2. その週の月曜日と日曜日を計算
    # target_date.weekday() : 月=0, ..., 日=6
    start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # 3. 前週と翌週の月曜日を計算（ボタン用）
    prev_week_start = start_of_week - timedelta(days=7)
    next_week_start = start_of_week + timedelta(days=7)

    # --- 以下、集計ロジック（既存のままですが、変数は start_of_week を使います） ---
    
    # タイムゾーン考慮してdatetimeにする
    start_datetime = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_of_week, datetime.max.time()))

    records = Schedule.objects.filter(
        owner=request.user,
        action_category__track_pages=True,
        page_count__isnull=False,
        start_time__range=(start_datetime, end_datetime)
    ).select_related('action_category').order_by('start_time')

    total_pages = records.aggregate(Sum('page_count'))['page_count__sum'] or 0

    # グラフ用データ作成（日別）
    daily_stats = {}
    for i in range(7):
        date_obj = start_of_week + timedelta(days=i)
        daily_stats[date_obj] = 0

    for record in records:
        local_date = timezone.localtime(record.start_time).date()
        if local_date in daily_stats:
            daily_stats[local_date] += record.page_count

    daily_labels = [d.strftime('%m/%d') for d in daily_stats.keys()]
    daily_data = list(daily_stats.values())

    # カテゴリ別集計
    category_summary = {}
    for record in records:
        cat_name = record.action_category.name
        category_summary[cat_name] = category_summary.get(cat_name, 0) + record.page_count
    
    pie_labels = list(category_summary.keys())
    pie_data = list(category_summary.values())

    context = {
        'start_date': start_of_week,
        'end_date': end_of_week,
        'records': records,
        'total_pages': total_pages,
        'category_summary': category_summary,
        'daily_labels': json.dumps(daily_labels),
        'daily_data': json.dumps(daily_data),
        'pie_labels': json.dumps(pie_labels),
        'pie_data': json.dumps(pie_data),
        # ★追加：ボタン用の日付文字列
        'prev_week_date': prev_week_start.strftime('%Y-%m-%d'),
        'next_week_date': next_week_start.strftime('%Y-%m-%d'),
        'is_this_week': start_of_week == (date.today() - timedelta(days=date.today().weekday())),
    }
    return render(request, 'todo/weekly_summary.html', context)

@login_required
def monthly_summary(request):
    """月間ヒートマップを表示するビュー"""
    
    # 1. 表示する年月を取得（指定がなければ今月）
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    today = date.today()
    if year and month:
        try:
            current_year = int(year)
            current_month = int(month)
        except ValueError:
            current_year = today.year
            current_month = today.month
    else:
        current_year = today.year
        current_month = today.month

    # 2. その月のデータを取得
    # 月の初日と最終日を計算
    _, last_day = calendar.monthrange(current_year, current_month)
    start_date = datetime(current_year, current_month, 1)
    end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
    
    # タイムゾーン対応
    start_datetime = timezone.make_aware(start_date)
    end_datetime = timezone.make_aware(end_date)

    # ページ数記録ONのデータを取得
    records = Schedule.objects.filter(
        owner=request.user,
        action_category__track_pages=True,
        page_count__isnull=False,
        start_time__range=(start_datetime, end_datetime)
    )

    # 日ごとの合計を計算 {day(int): pages(int)}
    daily_pages = {}
    max_pages = 0 # ヒートマップの基準（その月で一番読んだ日のページ数）
    
    for record in records:
        day = record.start_time.day
        daily_pages[day] = daily_pages.get(day, 0) + record.page_count
        if daily_pages[day] > max_pages:
            max_pages = daily_pages[day]

    # 3. カレンダー作成
    cal = calendar.Calendar(firstweekday=0) # 0=月曜始まり
    month_calendar = []
    
    for week in cal.monthdayscalendar(current_year, current_month):
        week_data = []
        for day in week:
            if day == 0:
                # 0は前の月/次の月の日付（空白にする）
                week_data.append(None)
            else:
                pages = daily_pages.get(day, 0)
                # 色の濃さを計算 (0.0 〜 1.0)
                # pagesが0なら0、それ以外は max_pages に対する割合（最低0.1は確保）
                opacity = 0
                if max_pages > 0 and pages > 0:
                    opacity = max(0.2, pages / max_pages) # 最低0.2の濃さは保証
                
                week_data.append({
                    'day': day,
                    'pages': pages,
                    'opacity': opacity
                })
        month_calendar.append(week_data)

    # 4. 前月・次月のリンク用計算
    if current_month == 1:
        prev_year, prev_month = current_year - 1, 12
    else:
        prev_year, prev_month = current_year, current_month - 1
        
    if current_month == 12:
        next_year, next_month = current_year + 1, 1
    else:
        next_year, next_month = current_year, current_month + 1

    context = {
        'year': current_year,
        'month': current_month,
        'calendar': month_calendar,
        'prev_year': prev_year, 'prev_month': prev_month,
        'next_year': next_year, 'next_month': next_month,
        'total_pages': sum(daily_pages.values())
    }
    return render(request, 'todo/monthly_summary.html', context)

@login_required
@require_POST
def pomodoro_start(request):
    """Create a Schedule entry from pomodoro timer."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    title = (data.get('title') or '').strip() or 'Pomodoro'
    work_minutes = int(data.get('work_minutes') or 25)

    start_time = timezone.now()
    end_time = start_time + timedelta(minutes=work_minutes)

    schedule = Schedule.objects.create(
        owner=request.user,
        start_time=start_time,
        end_time=end_time,
        title_override=title,
    )

    return JsonResponse({'status': 'success', 'id': schedule.pk})


@login_required
@require_POST
def periodic_task_create(request):
    title = (request.POST.get('title') or '').strip()
    if not title:
        return redirect('todo:calendar')

    interval_days = request.POST.get('interval_days') or '1'
    try:
        interval_days = int(interval_days)
    except ValueError:
        interval_days = 1
    if interval_days < 1:
        interval_days = 1

    last_done_str = (request.POST.get('last_done') or '').strip()
    last_done = None
    if last_done_str:
        try:
            last_done = datetime.strptime(last_done_str, '%Y-%m-%d').date()
        except ValueError:
            last_done = None

    PeriodicTask.objects.create(
        owner=request.user,
        title=title,
        interval_days=interval_days,
        last_done=last_done,
    )
    return redirect(request.META.get('HTTP_REFERER', reverse('todo:today_tasks_setup')))


@login_required
@require_POST
def periodic_task_done(request, pk):
    task = get_object_or_404(PeriodicTask, pk=pk, owner=request.user)
    task.last_done = date.today()
    task.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('todo:today_tasks_setup')))

def public_calendar_events(request):
    """
    公開用カレンダーのイベントデータを返す
    - 内容は伏せて「予定あり」で統一
    """
    target_user_id = 1
    schedules = Schedule.objects.filter(owner_id=target_user_id).select_related('action_category', 'action_item')

    events = []
    for schedule in schedules:
        title_text = "予定あり"
        bg_color = "#6c757d"

        events.append({
            'title': title_text,
            'start': schedule.start_time.isoformat(),
            'end': schedule.end_time.isoformat(),
            'backgroundColor': bg_color,
            'borderColor': bg_color,
        })

    return JsonResponse(events, safe=False)

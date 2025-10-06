import random
from collections import defaultdict
from django.shortcuts import render, redirect
from django.http import HttpRequest
from .models import LabMember

def select_members_view(request: HttpRequest):
    """参加者と発表者を選択するページを表示するビュー"""
    # 在籍中のメンバーのみを取得
    members = LabMember.objects.filter(is_active=True).order_by('name')
    context = {'members': members}
    return render(request, 'roulette_app/index.html', context)


def result_view(request: HttpRequest):
    """チーム分けを実行し、結果を表示するビュー (グループ数修正版)"""
    if request.method != 'POST':
        return redirect('roulette_app:index')

    participant_ids = request.POST.getlist('participants')
    presenter_ids = request.POST.getlist('presenters')

    # 発表者が選択されていない場合はエラーメッセージを表示して戻る
    if not presenter_ids:
        messages.error(request, '発表者を1人以上選択してください。')
        return redirect('roulette_app:index')

    participants = LabMember.objects.filter(id__in=participant_ids)
    presenters = LabMember.objects.filter(id__in=presenter_ids)
    others = participants.exclude(id__in=presenter_ids)

    # --- チーム分けアルゴリズム ---
    num_participants = len(participants)
    num_presenters = len(presenters)

    # ▼▼▼▼▼ ここからが修正箇所です ▼▼▼▼▼

    # 1. グループ数を発表者の数に設定
    num_groups = num_presenters
    
    # 以前のグループ数計算ロジックは削除

    # ▲▲▲▲▲ ここまでが修正箇所です ▲▲▲▲▲
    
    # 2. メンバーをシャッフル
    presenters_list = list(presenters)
    random.shuffle(presenters_list)
    others_list = list(others)
    random.shuffle(others_list)

    # 3. グループを初期化
    groups = [[] for _ in range(num_groups)]
    
    if not groups:
        messages.error(request, 'エラーが発生しました。もう一度お試しください。')
        return redirect('roulette_app:index')

    # 4. 各グループに発表者を1人ずつ配置
    for i, presenter in enumerate(presenters_list):
        groups[i].append(presenter)

    # 5. 残りのメンバー（発表者以外）を配置
    all_remaining = others_list
    random.shuffle(all_remaining)
    
    group_counts = [{'COMM': 0, 'GRAPH': 0} for _ in range(num_groups)]
    for i, group in enumerate(groups):
        for member in group:
            group_counts[i][member.research_group] += 1
            
    for member in all_remaining:
        group_indices = list(range(num_groups))
        group_indices.sort(key=lambda i: (
            len(groups[i]), 
            -abs(group_counts[i]['COMM'] - group_counts[i]['GRAPH'])
        ))
        
        target_group_index = group_indices[0]
        groups[target_group_index].append(member)
        group_counts[target_group_index][member.research_group] += 1

    final_groups = groups

    context = {'groups': final_groups}
    return render(request, 'roulette_app/result.html', context)
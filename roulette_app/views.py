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
    """チーム分けを実行し、結果を表示するビュー (修正版)"""
    if request.method != 'POST':
        return redirect('roulette_app:index')

    participant_ids = request.POST.getlist('participants')
    presenter_ids = request.POST.getlist('presenters')

    if not participant_ids:
        return redirect('roulette_app:index')

    participants = LabMember.objects.filter(id__in=participant_ids)
    presenters = LabMember.objects.filter(id__in=presenter_ids)
    others = participants.exclude(id__in=presenter_ids)

    # --- チーム分けアルゴリズム ---
    num_participants = len(participants)
    
    # 参加者が少ない場合は、全員を1つのグループに入れる
    if num_participants < 3:
        context = {'groups': [list(participants)]}
        return render(request, 'roulette_app/result.html', context)

    # 1. グループ数と各グループの人数を計算
    base_size = 3
    num_groups = num_participants // base_size
    remainder = num_participants % base_size

    # 4人グループが多くなりすぎないように調整
    if num_groups > 0 and remainder > num_groups / 2:
        num_groups = num_participants // 4
        remainder = num_participants % 4
        if num_groups == 0: # 4人未満の場合
             num_groups = 1
             base_size = num_participants
             remainder = 0
        else:
             base_size = 4
    
    group_sizes = [base_size + 1] * remainder + [base_size] * (num_groups - remainder)

    # 2. メンバーをシャッフル
    presenters_list = list(presenters)
    others_list = list(others)
    random.shuffle(presenters_list)
    random.shuffle(others_list)

    # 3. グループを初期化
    groups = [[] for _ in range(num_groups)]
    
    # 参加者がグループ数より少ない場合のエッジケース対応
    if not groups:
        context = {'groups': [list(participants)]}
        return render(request, 'roulette_app/result.html', context)

    # 4. 【優先ルール】各グループに発表者を1人ずつ配置
    for i, presenter in enumerate(presenters_list):
        group_index = i % num_groups
        groups[group_index].append(presenter)

    # 5. 残りのメンバーを配置
    all_remaining = others_list + presenters_list[num_groups:]
    random.shuffle(all_remaining)
    
    # ▼▼▼▼▼ ここからが修正箇所です ▼▼▼▼▼
    
    # 分野ごとのカウンタを各グループに持たせる
    group_counts = [{'COMM': 0, 'GRAPH': 0} for _ in range(num_groups)]
    for i, group in enumerate(groups):
        for member in group:
            group_counts[i][member.research_group] += 1
            
    # 残りのメンバーを配置していく
    for member in all_remaining:
        # 追加先のグループを決めるため、グループのインデックスをソートする
        # 条件：1. 現在の人数が少ない順, 2. 分野の偏りが大きい順
        group_indices = list(range(num_groups))
        group_indices.sort(key=lambda i: (
            len(groups[i]), 
            -abs(group_counts[i]['COMM'] - group_counts[i]['GRAPH'])
        ))
        
        # 最も優先度の高いグループに追加
        target_group_index = group_indices[0]
        groups[target_group_index].append(member)
        group_counts[target_group_index][member.research_group] += 1

    # ▲▲▲▲▲ ここまでが修正箇所です ▲▲▲▲▲

    final_groups = groups

    context = {'groups': final_groups}
    return render(request, 'roulette_app/result.html', context)
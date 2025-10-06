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
    """チーム分けを実行し、結果を表示するビュー"""
    if request.method != 'POST':
        return redirect('roulette_app:index')

    # フォームから送信されたIDリストを取得
    participant_ids = request.POST.getlist('participants')
    presenter_ids = request.POST.getlist('presenters')

    if not participant_ids:
        # 参加者が選択されていない場合はリダイレクト
        return redirect('roulette_app:index')

    # 参加者と発表者のモデルオブジェクトを取得
    participants = LabMember.objects.filter(id__in=participant_ids)
    presenters = LabMember.objects.filter(id__in=presenter_ids)
    others = participants.exclude(id__in=presenter_ids)

    # --- チーム分けアルゴリズム ---

    # 1. グループ数と各グループの人数を計算
    num_participants = len(participants)
    base_size = 3  # 基本のグループ人数
    
    num_groups = num_participants // base_size
    remainder = num_participants % base_size
    
    if remainder > num_groups: # 3人グループが多くなりすぎる場合
        base_size = 4
        num_groups = num_participants // base_size
        remainder = num_participants % base_size

    group_sizes = [base_size + 1] * remainder + [base_size] * (num_groups - remainder)
    if not group_sizes: # 参加者が少ない場合
        group_sizes = [num_participants] if num_participants > 0 else []

    # 2. メンバーをシャッフル
    presenters_list = list(presenters)
    others_list = list(others)
    random.shuffle(presenters_list)
    random.shuffle(others_list)
    
    # 3. グループを初期化
    groups = [[] for _ in range(len(group_sizes))]

    # 4. 【優先ルール】各グループに発表者を1人ずつ配置
    for i, presenter in enumerate(presenters_list):
        group_index = i % len(groups)
        groups[group_index].append(presenter)

    # 5. 残りのメンバーを分野のバランスを考慮しながら配置
    all_remaining = others_list + presenters_list[len(groups):]
    random.shuffle(all_remaining)

    # 分野ごとのカウンタを各グループに持たせる
    group_counts = [{'COMM': 0, 'GRAPH': 0} for _ in groups]
    for i, group in enumerate(groups):
        for member in group:
            group_counts[i][member.research_group] += 1
            
    # 残りのメンバーを配置
    for member in all_remaining:
        # グループを「現在の人数」「分野の偏り」でソート
        groups.sort(key=lambda g: (
            len(g), 
            abs(group_counts[groups.index(g)]['COMM'] - group_counts[groups.index(g)]['GRAPH'])
        ))
        
        # 最も優先度の高いグループに追加
        target_group_index = 0
        groups[target_group_index].append(member)
        group_counts[target_group_index][member.research_group] += 1

    # 最終的なグループリスト
    final_groups = groups

    context = {'groups': final_groups}
    return render(request, 'roulette_app/result.html', context)
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Knowledge, Tag, Comment
from .forms import KnowledgeForm , CommentForm, TagForm
from django.http import Http404
from django import forms

import markdown

#汎用関数
def check_knowledge_owner(request, knowledge):
    if knowledge.owner != request.user:
        raise Http404

def knowledge_list(request, show_others_flag=None):
    """
    トップページで、公開設定に基づいてKnowledgeオブジェクトを取得する。
    """
    if request.user.is_authenticated:
        # ログインユーザーの場合
        knowledges = Knowledge.objects.filter(
            Q(owner=request.user) | Q(is_public=True),
            parent__isnull=True
        ).order_by('id')
        
        if show_others_flag == 'false':
            knowledges = knowledges.filter(owner=request.user)
    else:
        # ログアウト中のユーザーの場合
        knowledges = Knowledge.objects.filter(
            is_public=True,
            parent__isnull=True
        ).order_by('id')

    context = {'knowledges': knowledges, 'show_others': show_others_flag}
    return render(request, 'learning_logs/knowledge_list.html', context)

# 詳細表示ビュー
def knowledge_detail(request, knowledge_id):
    """特定のKnowledgeオブジェクトを1件だけ取得し、その子要素とコメント、Todo、階層パスも取得する"""
    knowledge = get_object_or_404(Knowledge, pk=knowledge_id)
    
    # アクセス制御のロジック
    if not knowledge.is_public and knowledge.owner != request.user:
        raise Http404

    # コメントの処理
    if request.method == 'POST':
        if 'comment-submit' in request.POST:
            form = CommentForm(data=request.POST)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.knowledge = knowledge
                new_comment.user = request.user
                new_comment.save()
            return redirect('learning_logs:knowledge_detail', knowledge_id=knowledge.pk)
    else:
        comment_form = CommentForm()

    # 階層パスを取得
    breadcrumb_trail = []
    current_knowledge = knowledge
    while current_knowledge:
        breadcrumb_trail.insert(0, current_knowledge)
        current_knowledge = current_knowledge.parent
    
    # 子要素を取得
    children = Knowledge.objects.filter(parent=knowledge).filter(
        Q(is_public=True) | Q(owner=request.user)
    ).order_by('id')
    
    # コメント一覧を取得
    comments = knowledge.comments.all().order_by('-date_added')

    # MarkdownをHTMLに変換
    html_content = markdown.markdown(knowledge.content, extensions=['fenced_code', 'tables'])
    
    context = {
        'knowledge': knowledge,
        'html_content': html_content,
        'children': children,
        'comments': comments,
        'comment_form': comment_form,
        'breadcrumb_trail': breadcrumb_trail
    }
    return render(request, 'learning_logs/knowledge_detail.html', context)

# 新規作成ビュー
@login_required
def new_knowledge(request, parent_id=None, knowledge_type=None):
    """新しい知識を追加する"""
    parent_knowledge = None
    if parent_id:
        parent_knowledge = get_object_or_404(Knowledge, pk=parent_id)
        # ユーザーが所有者であることを確認する関数
        check_knowledge_owner(request, parent_knowledge)

    if request.method != 'POST':
        initial_data = {}
        if knowledge_type:
            initial_data['knowledge_type'] = knowledge_type
        
        # knowledge_typeの値に応じてcontentの初期値を設定
        if knowledge_type == 'book' or knowledge_type == 'paper':
            initial_data['content'] = "## おすすめ度:\n\n ★★★★★ \n\n## 詳細:\n\n\n## 章構成:\n\n\n## キーワード:\n\n"
        
        form = KnowledgeForm(initial=initial_data)
    else:
        form = KnowledgeForm(data=request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.owner = request.user
            new_item.parent = parent_knowledge
            new_item.save()
            return redirect('learning_logs:knowledge_detail', knowledge_id=new_item.pk)

    context = {'form': form, 'parent': parent_knowledge}
    return render(request, 'learning_logs/new_knowledge.html', context)

def edit_knowledge(request, pk):
    """既存の知識を編集する"""
    knowledge = get_object_or_404(Knowledge, pk=pk)
    
    # 所有者チェック
    check_knowledge_owner(request, knowledge)
    
    if request.method == 'POST':
        form = KnowledgeForm(request.POST, instance=knowledge)
        if form.is_valid():
            form.save()
            return redirect('learning_logs:knowledge_detail', knowledge_id=knowledge.pk)
    else:
        form = KnowledgeForm(instance=knowledge)
        
    context = {'knowledge': knowledge, 'form': form}
    return render(request, 'learning_logs/edit_knowledge.html', context)

def delete_knowledge(request, pk):
    """知識を削除する"""
    knowledge = get_object_or_404(Knowledge, pk=pk)

    # 所有者チェックを追加
    check_knowledge_owner(request, knowledge)
    
    if request.method == 'POST':
        knowledge.delete()
        return redirect('learning_logs:knowledge_list')
        
    context = {'knowledge': knowledge}
    return render(request, 'learning_logs/knowledge_confirm_delete.html', context)

def search_results(request):
    """知識の検索結果を表示する"""
    query = request.GET.get('q') # URLからキーワードを取得
    
    if request.user.is_authenticated:
        # ログインユーザーの場合
        knowledges = Knowledge.objects.filter(
            Q(owner=request.user) | Q(is_public=True)
        )
    else:
        # ログアウト中のユーザーの場合
        knowledges = Knowledge.objects.filter(
            is_public=True
        )

    if query:
        # キーワードでタイトルまたは内容をフィルタリング
        knowledges = knowledges.filter(Q(title__icontains=query) | Q(content__icontains=query))

    context = {'knowledges': knowledges, 'query': query}
    return render(request, 'learning_logs/knowledge_list.html', context)

def tag_list(request, tag_name):
    """特定のタグを持つ知識の一覧を表示する"""
    tag = get_object_or_404(Tag, name=tag_name)

    if request.user.is_authenticated:
        # ログインユーザーの場合
        knowledges = Knowledge.objects.filter(
            Q(tags=tag) & (Q(owner=request.user) | Q(is_public=True))
        ).order_by('id')
    else:
        # ログアウト中のユーザーの場合
        knowledges = Knowledge.objects.filter(
            tags=tag, is_public=True
        ).order_by('id')
    
    context = {'knowledges': knowledges, 'tag': tag}
    return render(request, 'learning_logs/knowledge_list.html', context)

def tags_list(request):
    """すべてのタグと、タグに紐づく知識の数を取得する"""
    if request.user.is_authenticated:
        # ログインユーザーの場合
        tags = Tag.objects.annotate(
            num_knowledges=Count('knowledge', filter=Q(knowledge__owner=request.user) | Q(knowledge__is_public=True))
        )
    else:
        # ログアウト中のユーザーの場合
        tags = Tag.objects.annotate(
            num_knowledges=Count('knowledge', filter=Q(knowledge__is_public=True))
        )
    
    # 知識が0件のタグは表示しない
    tags = tags.filter(num_knowledges__gt=0).order_by('name')

    context = {'tags': tags}
    return render(request, 'learning_logs/tags_list.html', context)

@login_required
def tag_create(request):
    """新しいタグを作成する"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('learning_logs:tags_list')
    else:
        form = TagForm()
    
    context = {'form': form}
    return render(request, 'learning_logs/tag_create.html', context)


def knowledge_detail(request, knowledge_id):
    """特定のKnowledgeオブジェクトを1件だけ取得し、その子要素とコメント、階層パスも取得する"""
    knowledge = get_object_or_404(Knowledge, pk=knowledge_id)
    
    # アクセス制御のロジック
    if not knowledge.is_public and knowledge.owner != request.user:
        raise Http404

    # コメントフォームの処理
    if request.method == 'POST':
        form = CommentForm(data=request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.knowledge = knowledge
            new_comment.user = request.user
            new_comment.save()
            return redirect('learning_logs:knowledge_detail', knowledge_id=knowledge.pk)
    else:
        form = CommentForm()

    # 階層パスを取得
    breadcrumb_trail = []
    current_knowledge = knowledge
    while current_knowledge:
        breadcrumb_trail.insert(0, current_knowledge)
        current_knowledge = current_knowledge.parent
    
    # 子要素を取得
    children = Knowledge.objects.filter(parent=knowledge).filter(
        Q(is_public=True) | Q(owner=request.user)
    ).order_by('id')

    # コメント一覧を取得
    comments = knowledge.comments.all().order_by('-date_added')

    # MarkdownをHTMLに変換
    html_content = markdown.markdown(knowledge.content, extensions=['fenced_code', 'tables'])
    
    context = {
        'knowledge': knowledge,
        'html_content': html_content,
        'children': children,
        'comments': comments, # コメント一覧をテンプレートに渡す
        'form': form, # コメントフォームをテンプレートに渡す
        'breadcrumb_trail': breadcrumb_trail
    }
    return render(request, 'learning_logs/knowledge_detail.html', context)

def profile(request, username):
    """ユーザープロフィールページを表示する"""
    user = get_object_or_404(User, username=username)

    if request.user.is_authenticated and user == request.user:
        # ログインユーザー自身のプロフィールの場合、公開・非公開両方の知識を取得
        knowledges = Knowledge.objects.filter(owner=user, parent__isnull=True).order_by('id')
    else:
        # 他人のプロフィール、またはログアウト中のユーザーの場合、公開知識のみを取得
        knowledges = Knowledge.objects.filter(owner=user, is_public=True, parent__isnull=True).order_by('id')
    
    context = {'profile_user': user, 'knowledges': knowledges}
    return render(request, 'learning_logs/profile.html', context)

@login_required
def delete_comment(request, comment_id):
    """コメントを削除する"""
    comment = get_object_or_404(Comment, pk=comment_id)
    knowledge = comment.knowledge

    # アクセス制御: コメントの所有者のみが削除可能
    if comment.user != request.user:
        raise Http404
    
    if request.method == 'POST':
        comment.delete()
        return redirect('learning_logs:knowledge_detail', knowledge_id=knowledge.pk)
    
    # GETリクエストの場合、削除確認ページなどを表示することも可能ですが、
    # ここではシンプルにPOSTリクエストがない限り何もしない
    return redirect('learning_logs:knowledge_detail', knowledge_id=knowledge.pk)
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import QuickMemoForm
from .models import QuickMemo


def _safe_title_filename(title, max_len=30):
    cleaned = (title or "").strip()
    for ch in '<>:"/\\|?*':
        cleaned = cleaned.replace(ch, "_")
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        cleaned = "memo"
    return cleaned[:max_len]


def _memo_to_text(memo):
    created_at_local = timezone.localtime(memo.created_at)
    lines = [
        f"ID: {memo.sequence_id}",
        f"作成日時: {created_at_local.strftime('%Y-%m-%d %H:%M:%S')}",
        f"タイトル: {memo.title}",
        "本文:",
        memo.body,
    ]
    return "\n".join(lines)


@login_required
def memo_list(request):
    memos = QuickMemo.objects.filter(owner=request.user)
    return render(request, "memo/list.html", {"memos": memos})


@login_required
def memo_create(request):
    if request.method == "POST":
        form = QuickMemoForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.owner = request.user
            memo.save()
            return redirect("memo:list")
    else:
        form = QuickMemoForm()
    return render(request, "memo/form.html", {"form": form, "mode": "create"})


@login_required
def memo_detail(request, pk):
    memo = get_object_or_404(QuickMemo, pk=pk, owner=request.user)
    return render(request, "memo/detail.html", {"memo": memo})


@login_required
def memo_edit(request, pk):
    memo = get_object_or_404(QuickMemo, pk=pk, owner=request.user)
    if request.method == "POST":
        form = QuickMemoForm(request.POST, instance=memo)
        if form.is_valid():
            form.save()
            return redirect("memo:list")
    else:
        form = QuickMemoForm(instance=memo)
    return render(
        request,
        "memo/form.html",
        {"form": form, "mode": "edit", "memo": memo},
    )


@login_required
def memo_delete(request, pk):
    memo = get_object_or_404(QuickMemo, pk=pk, owner=request.user)
    if request.method == "POST":
        memo.delete()
        return redirect("memo:list")
    return render(request, "memo/confirm_delete.html", {"memo": memo})


@login_required
def memo_export_single(request, pk):
    memo = get_object_or_404(QuickMemo, pk=pk, owner=request.user)
    content = _memo_to_text(memo) + "\n"
    filename = f"{_safe_title_filename(memo.title)}.txt"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def memo_export_all(request):
    memos = QuickMemo.objects.filter(owner=request.user).order_by("sequence_id")
    blocks = [_memo_to_text(memo) for memo in memos]
    if blocks:
        content = ("\n\n" + ("-" * 40) + "\n\n").join(blocks) + "\n"
    else:
        content = "メモはまだありません。\n"

    timestamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    filename = f"all_memos_{timestamp}.txt"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import ReadingNoteForm, AffiliateLinkForm, ReadingThemeTagForm
from .models import ReadingNote, AffiliateLink, ReadingThemeTag

AffiliateLinkFormSet = inlineformset_factory(
    ReadingNote,
    AffiliateLink,
    form=AffiliateLinkForm,
    extra=2,
    can_delete=False,
)


def _format_note_for_export(note):
    return "\n".join([
        f"[{note.title}]",
        f"著者: {note.author}",
        "読書中の感想:",
        note.impression_during,
        "読む目的・テーマ:",
        note.reading_purpose,
        "読了後の感想:",
        note.impression_after,
        "-----",
    ])


@login_required
def note_list(request):
    notes = ReadingNote.objects.filter(owner=request.user).prefetch_related("theme_tags")

    status = (request.GET.get("status") or "reading").strip()
    if status and status != "all":
        notes = notes.filter(status=status)

    q = (request.GET.get("q") or "").strip()
    if q:
        notes = notes.filter(
            Q(title__icontains=q)
            | Q(author__icontains=q)
            | Q(one_line_summary__icontains=q)
            | Q(reading_purpose__icontains=q)
            | Q(theme_tags__name__icontains=q)
        ).distinct()

    sort = request.GET.get("sort", "updated")
    order = request.GET.get("order", "desc")
    sort_map = {
        "updated": "updated_at",
        "finished": "finished_at",
        "rating": "rating",
    }
    sort_field = sort_map.get(sort, "updated_at")

    if order == "asc":
        notes = notes.order_by(sort_field, "-updated_at")
    else:
        notes = notes.order_by(f"-{sort_field}", "-updated_at")

    context = {
        "notes": notes,
        "q": q,
        "sort": sort,
        "order": order,
        "status": status,
    }
    return render(request, "reading_notes/list.html", context)


@login_required
def note_export_selected(request):
    if request.method != "POST":
        return redirect("reading_notes:list")

    note_ids = request.POST.getlist("note_ids")
    notes = ReadingNote.objects.filter(owner=request.user, pk__in=note_ids)

    id_order = {int(note_id): index for index, note_id in enumerate(note_ids) if note_id.isdigit()}
    notes = sorted(notes, key=lambda note: id_order.get(note.pk, len(id_order)))

    content = "\n".join(_format_note_for_export(note) for note in notes)
    if content:
        content += "\n"

    filename = f"{timezone.localdate().strftime('%Y-%m-%d')}-memo.txt"
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def note_detail(request, pk):
    note = get_object_or_404(ReadingNote.objects.prefetch_related("theme_tags", "affiliate_links"), pk=pk, owner=request.user)
    return render(request, "reading_notes/detail.html", {"note": note})


@login_required
def note_create(request):
    if request.method == "POST":
        form = ReadingNoteForm(request.POST, request.FILES, user=request.user)
        formset = AffiliateLinkFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            form.save_m2m()
            formset.instance = note
            formset.save()
            return redirect("reading_notes:detail", pk=note.pk)
    else:
        form = ReadingNoteForm(user=request.user)
        formset = AffiliateLinkFormSet(
            initial=[
                {"kind": AffiliateLink.Kind.AMAZON},
                {"kind": AffiliateLink.Kind.RAKUTEN},
            ]
        )

    return render(
        request,
        "reading_notes/form.html",
        {"form": form, "formset": formset, "mode": "create"},
    )


@login_required
def note_edit(request, pk):
    note = get_object_or_404(ReadingNote, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ReadingNoteForm(request.POST, request.FILES, instance=note, user=request.user)
        formset = AffiliateLinkFormSet(request.POST, instance=note)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("reading_notes:detail", pk=note.pk)
    else:
        form = ReadingNoteForm(instance=note, user=request.user)
        formset = AffiliateLinkFormSet(instance=note)

    return render(
        request,
        "reading_notes/form.html",
        {"form": form, "formset": formset, "mode": "edit", "note": note},
    )


@login_required
def note_delete(request, pk):
    note = get_object_or_404(ReadingNote, pk=pk, owner=request.user)
    if request.method == "POST":
        note.delete()
        return redirect("reading_notes:list")
    return render(request, "reading_notes/confirm_delete.html", {"note": note})


@login_required
def theme_tag_list(request):
    tags = ReadingThemeTag.objects.filter(owner=request.user).order_by("name")
    return render(request, "reading_notes/theme_tag_list.html", {"tags": tags})


@login_required
def theme_tag_create(request):
    if request.method == "POST":
        form = ReadingThemeTagForm(request.POST, user=request.user)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.owner = request.user
            tag.save()
            return redirect("reading_notes:theme_tag_list")
    else:
        form = ReadingThemeTagForm(user=request.user)
    return render(request, "reading_notes/theme_tag_form.html", {"form": form, "mode": "create"})


@login_required
def theme_tag_edit(request, pk):
    tag = get_object_or_404(ReadingThemeTag, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ReadingThemeTagForm(request.POST, instance=tag, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("reading_notes:theme_tag_list")
    else:
        form = ReadingThemeTagForm(instance=tag, user=request.user)
    return render(request, "reading_notes/theme_tag_form.html", {"form": form, "mode": "edit", "tag": tag})


@login_required
def theme_tag_delete(request, pk):
    tag = get_object_or_404(ReadingThemeTag, pk=pk, owner=request.user)
    if request.method == "POST":
        tag.delete()
        return redirect("reading_notes:theme_tag_list")
    return render(request, "reading_notes/theme_tag_confirm_delete.html", {"tag": tag})

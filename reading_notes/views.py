from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.forms import inlineformset_factory
from django.shortcuts import render, get_object_or_404, redirect

from .forms import ReadingNoteForm, AffiliateLinkForm
from .models import ReadingNote, AffiliateLink

AffiliateLinkFormSet = inlineformset_factory(
    ReadingNote,
    AffiliateLink,
    form=AffiliateLinkForm,
    extra=2,
    can_delete=True,
)


@login_required
def note_list(request):
    notes = ReadingNote.objects.filter(owner=request.user)

    q = (request.GET.get("q") or "").strip()
    if q:
        notes = notes.filter(
            Q(title__icontains=q)
            | Q(author__icontains=q)
            | Q(one_line_summary__icontains=q)
        )

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
    }
    return render(request, "reading_notes/list.html", context)


@login_required
def note_detail(request, pk):
    note = get_object_or_404(ReadingNote, pk=pk, owner=request.user)
    return render(request, "reading_notes/detail.html", {"note": note})


@login_required
def note_create(request):
    if request.method == "POST":
        form = ReadingNoteForm(request.POST, request.FILES)
        formset = AffiliateLinkFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.save()
            formset.instance = note
            formset.save()
            return redirect("reading_notes:detail", pk=note.pk)
    else:
        form = ReadingNoteForm()
        formset = AffiliateLinkFormSet()

    return render(
        request,
        "reading_notes/form.html",
        {"form": form, "formset": formset, "mode": "create"},
    )


@login_required
def note_edit(request, pk):
    note = get_object_or_404(ReadingNote, pk=pk, owner=request.user)
    if request.method == "POST":
        form = ReadingNoteForm(request.POST, request.FILES, instance=note)
        formset = AffiliateLinkFormSet(request.POST, instance=note)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("reading_notes:detail", pk=note.pk)
    else:
        form = ReadingNoteForm(instance=note)
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

from django.shortcuts import render, get_object_or_404

from .models import ReadingNote


def recommend_list(request):
    notes = ReadingNote.objects.filter(is_public=True)

    rating = request.GET.get("rating")
    if rating and rating.isdigit():
        notes = notes.filter(rating=int(rating))

    category = request.GET.get("category")
    if category:
        notes = notes.filter(category=category)

    notes = notes.order_by("-rating", "-finished_at", "-updated_at")

    context = {
        "notes": notes,
        "rating": rating or "",
        "category": category or "",
        "rating_choices": [5, 4, 3, 2, 1],
        "category_choices": [
            ("novel", "小説"),
            ("technical", "専門書"),
            ("reading", "読み物"),
            ("magazine", "雑誌"),
        ],
    }
    return render(request, "reading_notes/recommend_list.html", context)


def recommend_detail(request, pk):
    note = get_object_or_404(ReadingNote, pk=pk, is_public=True)
    return render(request, "reading_notes/recommend_detail.html", {"note": note})

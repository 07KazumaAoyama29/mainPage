from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from .forms import RosterForm
from .services import DrawUnavailable, draw_rooms, room_layout


@never_cache
@login_required
@require_GET
def index(request):
    return render(request, "room_draw/index.html", {"rooms": room_layout()})


def _roster_error(form):
    return JsonResponse({"error": str(form.errors["roster"][0])}, status=400)


@never_cache
@login_required
@require_POST
def prepare(request):
    form = RosterForm(request.POST)
    if not form.is_valid():
        return _roster_error(form)
    return JsonResponse({"participants": form.cleaned_data["roster"]})


@never_cache
@login_required
@require_POST
def draw(request):
    form = RosterForm(request.POST)
    if not form.is_valid():
        return _roster_error(form)
    try:
        rooms = draw_rooms(form.cleaned_data["roster"])
    except DrawUnavailable:
        return JsonResponse(
            {"error": "抽選できませんでした。もう一度お試しください。"}, status=503
        )
    return JsonResponse({"rooms": rooms})

import os

import requests as req
from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from concert.forms import LoginForm, SignUpForm
from concert.models import Concert, ConcertAttending


def _get_service_list(env_names, path, default_base):
    base = next((os.getenv(name) for name in env_names if os.getenv(name)), default_base)
    url = base if base.rstrip("/").endswith(path) else f"{base.rstrip('/')}{path}"
    response = req.get(url, timeout=(3, 10))
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        payload = payload["data"]
    if not isinstance(payload, list):
        raise ValueError("The service response must be a JSON list")
    return payload


def index(request):
    return render(request, "index.html")


def songs(request):
    error = None
    try:
        songs_list = _get_service_list(
            ("SONGS_API_URL", "SONGS_URL"), "/songs", "http://localhost:8081"
        )
    except (req.RequestException, ValueError) as exc:
        songs_list = []
        error = f"Songs service is unavailable: {exc}"
    return render(request, "songs.html", {"songs": songs_list, "service_error": error})


def photos(request):
    error = None
    try:
        photos_list = _get_service_list(
            ("PICTURES_API_URL", "PICTURES_URL"), "/picture", "http://localhost:8080"
        )
    except (req.RequestException, ValueError) as exc:
        photos_list = []
        error = f"Pictures service is unavailable: {exc}"
    return render(request, "photos.html", {"photos": photos_list, "service_error": error})


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("index")
    return render(request, "signup.html", {"form": form})


def login_view(request):
    form = LoginForm(request, data=request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "index")
    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("index")


def concerts(request):
    concert_list = Concert.objects.all()
    return render(request, "concerts.html", {"concerts": concert_list})


def concert_detail(request, id):
    concert = get_object_or_404(Concert, pk=id)
    status = ConcertAttending.AttendingChoices.NOTHING
    if request.user.is_authenticated:
        record = ConcertAttending.objects.filter(concert=concert, user=request.user).first()
        if record:
            status = record.attending
    return render(request, "concert_detail.html", {
        "concert_details": concert,
        "attending_choices": ConcertAttending.AttendingChoices.choices,
        "status": status,
    })


def concert_attendee(request):
    if request.method != "POST":
        return HttpResponse("POST required", status=405)
    if not request.user.is_authenticated:
        return redirect("login")

    concert = get_object_or_404(Concert, pk=request.POST.get("concert_id"))
    choice = request.POST.get("attendee_choice")
    valid_choices = {value for value, _label in ConcertAttending.AttendingChoices.choices}
    if choice not in valid_choices:
        return HttpResponse("Invalid RSVP choice", status=400)

    ConcertAttending.objects.update_or_create(
        concert=concert,
        user=request.user,
        defaults={"attending": choice},
    )
    return redirect("concert_detail", id=concert.pk)

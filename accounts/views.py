from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from companies.models import Company, Membership
from .forms import RegisterForm, LoginForm


# ── Public marketing pages ──────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return render(request, "pages/home.html")


def about(request):
    return render(request, "pages/about.html")


def how_it_works(request):
    return render(request, "pages/how_it_works.html")


def contact(request):
    if request.method == "POST":
        name = request.POST.get("first_name", request.POST.get("name", "")).strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        if name and email and message:
            messages.success(
                request,
                f"Thanks {name}! Your message has been received. We'll get back to you at {email} shortly.",
            )
        else:
            messages.error(request, "Please fill in all required fields.")
        return redirect("contact")

    return render(request, "pages/contact.html")


# ── Auth views ──────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                company = Company.objects.create(name=form.cleaned_data["company_name"])
                Membership.objects.create(
                    user=user,
                    company=company,
                    role=Membership.Role.OWNER,
                )
            login(request, user)
            messages.success(
                request,
                f"Welcome to WorkHub, {user.first_name}! Your company '{company.name}' is ready.",
            )
            return redirect("dashboard:home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get("next", "dashboard:home")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")

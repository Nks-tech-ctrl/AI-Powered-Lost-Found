from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegisterForm, LoginForm, UserUpdateForm, ProfileUpdateForm
from .models import UserProfile


def register_view(request):
    """
    User registration view.
    Validates form, creates user with securely hashed password,
    and redirects to login page with success message.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    User login view.
    Authenticates against Django's auth system, manages session persistence
    based on 'Remember me', and safely redirects to next URL or dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            # Support logging in with either username or registered email
            auth_username = username_or_email
            if '@' in username_or_email:
                try:
                    matched_user = User.objects.get(email__iexact=username_or_email)
                    auth_username = matched_user.username
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    auth_username = username_or_email

            user = authenticate(request, username=auth_username, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(request, "This account is currently disabled.")
                    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})

                login(request, user)

                # Control session persistence
                if remember_me:
                    request.session.set_expiry(None)  # Django normal session behavior
                else:
                    request.session.set_expiry(0)  # Browser close expiry

                messages.success(request, f"Welcome back, {user.first_name or user.username}!")

                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """
    User logout view.
    Terminates authenticated session and redirects to homepage with a message.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect(settings.LOGOUT_REDIRECT_URL)


@login_required
def profile_view(request):
    """
    Protected user profile view.
    Handles viewing and editing user details and profile preferences.
    Uses POST-Redirect-GET pattern on successful update.
    """
    profile_instance, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile_instance
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile_instance)

    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'user_form': user_form,
        'profile_form': profile_form,
    })


# Alias for compatibility if referenced as profile
profile = profile_view

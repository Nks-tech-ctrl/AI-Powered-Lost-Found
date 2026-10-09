from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.contrib import messages


def has_admin_permission(user, perm_codename=None):
    """
    Evaluates whether the user has administrator authorization.
    Superusers have full access. Staff users require the specified granular permission.
    Normal users never have access.
    """
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    if not user.is_staff:
        return False
    if perm_codename is None:
        return True
    
    # Check both full permission string and simple codename
    full_perm = perm_codename if '.' in perm_codename else f'admin_dashboard.{perm_codename}'
    return user.has_perm(full_perm)


def admin_required(view_func):
    """
    Decorator requiring authenticated staff or superuser access to the admin dashboard.
    Normal users are strictly rejected with HTTP 403.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/accounts/login/?next={request.path}')
        if not request.user.is_active or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Access denied. Administrator privileges are required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_permission_required(perm_codename):
    """
    Decorator enforcing a specific administrative permission.
    Example: @admin_permission_required('manage_users')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/accounts/login/?next={request.path}')
            if not has_admin_permission(request.user, perm_codename):
                raise PermissionDenied(f"Access denied. Missing required permission: {perm_codename}.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

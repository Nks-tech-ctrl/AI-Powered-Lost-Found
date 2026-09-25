from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    return render(request, 'items/dashboard.html')


@login_required
def report_lost_view(request):
    return render(request, 'items/report-lost.html')


@login_required
def report_found_view(request):
    return render(request, 'items/report-found.html')


def search_view(request):
    return render(request, 'items/search.html')


def item_details_view(request, id=None):
    return render(request, 'items/item-details.html', {'item_id': id})

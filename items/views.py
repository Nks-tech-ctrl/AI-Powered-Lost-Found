from django.shortcuts import render

def dashboard_view(request):
    return render(request, 'items/dashboard.html')

def report_lost_view(request):
    return render(request, 'items/report-lost.html')

def report_found_view(request):
    return render(request, 'items/report-found.html')

def search_view(request):
    return render(request, 'items/search.html')

def item_details_view(request, id=None):
    return render(request, 'items/item-details.html', {'item_id': id})

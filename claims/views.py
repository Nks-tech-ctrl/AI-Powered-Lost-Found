from django.shortcuts import render

def claims_view(request):
    return render(request, 'claims/claims.html')

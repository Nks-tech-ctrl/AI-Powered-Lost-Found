from django.shortcuts import render

def matches_view(request):
    return render(request, 'matches/matches.html')

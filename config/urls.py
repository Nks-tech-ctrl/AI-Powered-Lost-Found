from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView

urlpatterns = [
    # Universal wildcard redirects for any relative or legacy .html paths (checked first)
    re_path(r'.*login\.html$', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    re_path(r'.*register\.html$', RedirectView.as_view(url='/accounts/register/', permanent=False)),
    re_path(r'.*profile\.html$', RedirectView.as_view(url='/accounts/profile/', permanent=False)),
    re_path(r'.*dashboard\.html$', RedirectView.as_view(url='/items/', permanent=False)),
    re_path(r'.*report-lost\.html$', RedirectView.as_view(url='/items/report-lost/', permanent=False)),
    re_path(r'.*report-found\.html$', RedirectView.as_view(url='/items/report-found/', permanent=False)),
    re_path(r'.*search\.html$', RedirectView.as_view(url='/items/search/', permanent=False)),
    re_path(r'.*item-details\.html$', RedirectView.as_view(url='/items/details/', permanent=False)),
    re_path(r'.*matches\.html$', RedirectView.as_view(url='/matches/', permanent=False)),
    re_path(r'.*claims\.html$', RedirectView.as_view(url='/claims/', permanent=False)),
    re_path(r'.*index\.html$', RedirectView.as_view(url='/', permanent=False)),

    # Core and App routing
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('items/', include('items.urls')),
    path('matches/', include('matches.urls')),
    path('claims/', include('claims.urls')),
]

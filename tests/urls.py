from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('sagepay/', include('sagepaypi.urls')),
    path('secure-post-redirect/<tidb64>/<token>/',
         TemplateView.as_view(template_name='home.html'),
         name='secure_post_redirect'),
]

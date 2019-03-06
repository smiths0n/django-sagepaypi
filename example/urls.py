from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from example.views import TransactionCreateView, TransactionListView, TransactionStatusView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sagepay/', include('sagepaypi.urls')),
    path('transactions/<tidb64>/<token>/status/', TransactionStatusView.as_view(), name='transaction_status'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction_create'),
    path('', TransactionListView.as_view(), name='customers'),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

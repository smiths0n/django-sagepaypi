from django.urls import path

from sagepaypi import views


app_name = 'sagepaypi'

urlpatterns = [
    path(
        'transactions/<tidb64>/<token>/3d-secure/complete/',
        views.Complete3DSecureView.as_view(),
        name='complete_3d_secure'
    )
]

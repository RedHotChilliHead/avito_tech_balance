from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet, WithdrawDeposit, TransferView, TransactionViewSet

app_name = "balanceapp"

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)

urlpatterns = [
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('', include(router.urls)),
    path('customers/<int:customer_id>/operations/', WithdrawDeposit.as_view(), name='withdraw-deposit'),
    path('customers/<int:customer_id>/transactions/', TransactionViewSet.as_view({'get': 'list'}), name='transactions'),
]
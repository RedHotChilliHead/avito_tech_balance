from rest_framework import serializers
from balanceapp.models import Customer, Transaction


class CustomerSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользователей
    """
    valute = serializers.SerializerMethodField()

    def get_valute(self, obj):
        return "RUB"

    class Meta:
        model = Customer
        fields = ['id', 'name', 'balance', 'valute']
        read_only_fields = ('balance', 'valute')


class TransactionSerializer(serializers.ModelSerializer):
    """
    Сериализатор транзакций
    """

    class Meta:
        model = Transaction
        fields = "__all__"

from django.db import models


class Customer(models.Model):
    """
    Модель пользователя (для создания schema.sql)
    """
    name = models.CharField(max_length=100, blank=False)
    balance = models.DecimalField(max_digits=99, decimal_places=2)


class Transaction(models.Model):
    """
    Модель транзакции (для создания schema.sql)
    """
    amount = models.DecimalField(max_digits=99, decimal_places=2)
    timestamp = models.DateTimeField(auto_now=True)
    description = models.CharField(max_length=150, blank=False)
    sender = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, blank=True, null=True,
                               related_name='sent_transactions')  # отправитель
    recipient = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, blank=True, null=True,
                                  related_name='received_transactions')  # получатель


from decimal import Decimal
import requests
import xml.etree.ElementTree as ET
from django.db.models import Q

from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Customer, Transaction
from .serializers import CustomerSerializer, TransactionSerializer



class CustomerViewSet(ModelViewSet):
    """
    Представление для создания пользователя, отображения его данных (pk, имя и баланс)
    Изменение имени
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Переопределение метода retrieve для обработки GET-запросов (detail)
        http://127.0.0.1:8000/balance/customers/1/?currency=USD.
        Пример: curl -X POST -H 'Content-Type: application/json' -d '{"name":"test"}' http://127.0.0.1:8000/balance/customers/
        curl -X GET http://127.0.0.1:8000/balance/customers/1/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        currency = self.request.query_params.get('currency')
        if currency:
            response = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
            root = ET.fromstring(response.content)
            for valute in root.findall('Valute'):
                char_code = valute.find('CharCode').text
                if char_code == currency:
                    value = Decimal(float(valute.find('Value').text.replace(",", ".")))  # преобразуем строку в decimal
                    custom_data = serializer.data
                    # вычисляем баланс в валюте и переписываем обозначение валюты
                    custom_data['balance'] = str(round(instance.balance / value, 2))
                    custom_data['valute'] = char_code
                    return Response(custom_data, status=status.HTTP_200_OK)

            return Response({"error": "the currency was not found"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)


class WithdrawDeposit(APIView):
    """
    Представление для зачисления/списания средств со счета пользователя
    http://127.0.0.1:8000/balance/customers/1/
    Пример тела запроса: {"amount": 100.00, "operation": "withdraw", "description": "present"}
    Не обязательное поле - description.
    """

    def post(self, request, customer_id):
        data = request.data
        amount = data.get('amount')
        operation = data.get('operation')
        description = data.get('description')

        customer = get_object_or_404(Customer, pk=customer_id)

        if not amount or not operation:  # если не передали все необходимые аргументы
            return Response({"error": "Amount and operation are required"}, status=status.HTTP_400_BAD_REQUEST)

        if type(amount) is str or amount <= 0:  # если сумма некорректная
            return Response({"error": "The amount must be positive number"}, status=status.HTTP_400_BAD_REQUEST)

        if operation == 'withdraw':  # зачисление средств
            customer.balance += Decimal(amount)
            customer.save()
            Transaction.objects.create(amount=Decimal(amount), recipient=customer, description=description)
            return Response({"OK": "The operation was successful"}, status=status.HTTP_200_OK)

        elif operation == 'deposit':  # списание средств
            if Decimal(amount) > customer.balance:
                return Response({"error": "There are not enough funds in the account"},
                                status=status.HTTP_400_BAD_REQUEST)
            customer.balance -= Decimal(amount)
            customer.save()
            Transaction.objects.create(amount=Decimal(amount), sender=customer, description=description)
            return Response({"OK": "The operation was successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "The field 'operation' is specified incorrectly, "
                                      "you must specify either 'withdraw' or 'deposit'."},
                            status=status.HTTP_400_BAD_REQUEST)


class TransferView(APIView):
    """
    Представление для передачи средств одного пользователя на счет другого пользователя
    http://127.0.0.1:8000/balance/transfer/
    Пример тела запроса: {"amount": 100.00, "sender": "1", "recipient": "2", "description": "present"}
    Не обязательный параметр description
    """

    def post(self, request):
        data = request.data
        amount = data.get('amount')
        sender_id = data.get('sender')
        recipient_id = data.get('recipient')
        description = data.get('description')

        if not amount or not sender_id or not recipient_id:  # если не передали все необходимые аргументы
            return Response({"error": "Amount, sender and recipient are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        if type(amount) is str or amount < 0:  # если сумма некорректная
            return Response({"error": "The amount must be positive number"}, status=status.HTTP_400_BAD_REQUEST)

        sender = get_object_or_404(Customer, pk=sender_id)
        recipient = get_object_or_404(Customer, pk=recipient_id)

        if sender.balance < Decimal(amount):
            return Response({"error": "There are not enough funds in the account"},
                            status=status.HTTP_400_BAD_REQUEST)

        sender.balance -= Decimal(amount)
        recipient.balance += Decimal(amount)
        sender.save()
        recipient.save()
        Transaction.objects.create(amount=Decimal(amount), sender=sender, recipient=recipient,
                                   description=description)
        return Response({"OK": "The operation was successful"}, status=status.HTTP_200_OK)


class TransactionViewSet(ReadOnlyModelViewSet):
    """
    Получение списка транзакций
    GET запрос к  http://127.0.0.1:8000/balance/customers/<int:customer_id>/transactions/?order=timestamp.
    Для сортировки по дате необходимо указать параметр запроса ?order=timestamp, для сортировки по сумме ?order=amount.
    Для сортировки по убыванию параметр запроса должен начинаться с "-", например ?order=-amount
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def get_queryset(self):
        customer = self.kwargs['customer_id']
        order = self.request.query_params.get('order')
        if order:
            if order == 'timestamp' or order == 'amount' or order[1:] == 'timestamp' or order[1:] == 'amount':
                return self.queryset.filter(Q(recipient=customer) | Q(sender=customer)).order_by(order)
        return self.queryset.filter(Q(recipient=customer) | Q(sender=customer))

import json
import xml.etree.ElementTree as ET
from decimal import Decimal

import requests
from django.db.models import Q

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .models import Customer, Transaction


# docker-compose run test
class CustomerTestCase(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Den")
        self.customer.balance = 5000
        self.customer.save()

    def tearDown(self) -> None:
        self.customer.delete()

    def test_customer_create_api_view(self):
        """
        Проверка создания пользователя
        """
        post_data = {"name": "Antonio Banderas"}
        response = self.client.post(reverse('balanceapp:customer-list'), json.dumps(post_data),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Customer.objects.filter(name=post_data['name']).exists())

    def test_customer_list_api_view(self):
        """
        Проверка отображения списка пользователей
        """
        self.customer = Customer.objects.create(name="Natalia Oreiro")
        response = self.client.get(reverse('balanceapp:customer-list'))
        self.assertEqual(response.status_code, 200)
        queryset = Customer.objects.all()
        expected_data = [{'id': customer.pk, 'name': customer.name, 'balance': f'{customer.balance:.2f}', 'valute': 'RUB'}
                         for customer in queryset]
        response_data = json.loads(response.content)
        self.assertEqual(response_data['results'], expected_data)

    def test_customer_detail_api_view(self):
        """
        Проверка отображения детальной информации о пользователе
        """
        # проверяем отображение детальное информации о пользователе с параметром запроса
        query_param = {'currency': 'AED'}
        response = self.client.get(reverse("balanceapp:customer-detail", kwargs={"pk": self.customer.pk}), query_param)
        self.assertEqual(response.status_code, 200)

        response_valute = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
        root = ET.fromstring(response_valute.content)
        for valute in root.findall('Valute'):
            char_code = valute.find('CharCode').text
            if char_code == query_param['currency']:
                value = Decimal(float(valute.find('Value').text.replace(",", ".")))
                expected_data = {'id': self.customer.pk, 'name': self.customer.name,
                                 'balance': f'{self.customer.balance / value:.2f}', 'valute': query_param['currency']}

        response_data = json.loads(response.content)
        self.assertEqual(response_data, expected_data)

    def test_customer_update_api_view(self):
        """
        Проверка редактирования информации о пользователе
        """
        put_data = {'name': 'Antonio Oreiro'}
        response = self.client.put(reverse('balanceapp:customer-detail', kwargs={"pk": self.customer.pk}),
                                   json.dumps(put_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, put_data['name'])

    def test_customer_delete_api_view(self):
        """
        Проверка удаления пользователя
        """
        response = self.client.delete(reverse('balanceapp:customer-detail', kwargs={"pk": self.customer.pk}))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk))


class WithdrawDepositTestCase(APITestCase):
    """
    Проверка возможности снять и зачислить средства
    """
    def setUp(self):
        self.customer = Customer.objects.create(name="Den")

    def tearDown(self):
        self.customer.delete()

    def test_withdraw_deposit_api_view(self):
        withdraw = {'amount': 1000000, 'operation': 'withdraw', 'description': 'for a new car'}
        deposit = {'amount': 500, 'operation': 'deposit'}

        # проверка зачисления средств
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                   json.dumps(withdraw), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'OK': 'The operation was successful'})

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, withdraw['amount'])
        self.assertTrue(Transaction.objects.filter(amount=Decimal(withdraw['amount']),
                                                   recipient=self.customer,
                                                   description=withdraw['description']).exists())

        # проверка списания средств
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                    json.dumps(deposit), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'OK': 'The operation was successful'})

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, Decimal(withdraw['amount'])-Decimal(deposit['amount']))
        self.assertTrue(Transaction.objects.filter(amount=Decimal(deposit['amount']),
                                                   sender=self.customer).exists())

        # проверка валидации на отсутствие типа операции
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                    json.dumps({'amount': 500}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Amount and operation are required'})

        # проверка валидации на отсутствие суммы
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                    json.dumps({'operation': 'deposit'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'Amount and operation are required'})

        # проверка некорректной суммы
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                    json.dumps({'amount': 'ups', 'operation': 'withdraw'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "The amount must be positive number"})

        # проверка отрицательной суммы
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                    json.dumps({'amount': -5, 'operation': 'withdraw'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "The amount must be positive number"})

        # проверка указания некорректного типа операции
        response = self.client.post(reverse('balanceapp:withdraw-deposit', kwargs={'customer_id': self.customer.pk}),
                                    json.dumps({'amount': 500, 'operation': 'ups'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "The field 'operation' is specified incorrectly, "
                                      "you must specify either 'withdraw' or 'deposit'."})


class TransferTestCase(APITestCase):
    """
    Проверка возможности перевести средства от пользователя к пользователю
    """
    def setUp(self):
        self.sender = Customer.objects.create(name="Deineris")
        self.start_balance = 10000
        self.sender.balance = self.start_balance
        self.sender.save()

        self.recipient = Customer.objects.create(name="Khal")

    def tearDown(self):
        self.sender.delete()
        self.recipient.delete()

    def test_transfer_api_view(self):
        transfer = {'amount': 500, 'sender': self.sender.pk, 'recipient': self.recipient.pk, 'description': 'drakaris!'}

        # проверка зачисления средств
        response = self.client.post(reverse('balanceapp:transfer'),
                                   json.dumps(transfer), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'OK': 'The operation was successful'})

        self.sender.refresh_from_db()
        self.recipient.refresh_from_db()
        self.assertEqual(self.sender.balance, self.start_balance - transfer['amount'])
        self.assertEqual(self.recipient.balance, transfer['amount'])
        self.assertTrue(Transaction.objects.filter(amount=Decimal(transfer['amount']),
                                                   sender=self.sender,
                                                   recipient=self.recipient,
                                                   description=transfer['description']).exists())

        # проверка валидации на отсутствие отправителя
        response = self.client.post(reverse('balanceapp:transfer'),
                                    json.dumps({'amount': 500,
                                                'recipient': self.recipient.pk,
                                                'description': 'drakaris!'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Amount, sender and recipient are required"})

        # проверка валидации на отсутствие получателя
        response = self.client.post(reverse('balanceapp:transfer'),
                                    json.dumps({'amount': 500,
                                                'sender': self.sender.pk,
                                                'description': 'drakaris!'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Amount, sender and recipient are required"})

        # проверка валидации на отсутствие суммы
        response = self.client.post(reverse('balanceapp:transfer'),
                                    json.dumps({'sender': self.sender.pk,
                                                'recipient': self.recipient.pk,
                                                'description': 'drakaris!'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "Amount, sender and recipient are required"})

        # проверка на строку вместо суммы
        response = self.client.post(reverse('balanceapp:transfer'),
                                    json.dumps({'amount': 'ups',
                                                'sender': self.sender.pk,
                                                'recipient': self.recipient.pk,
                                                'description': 'drakaris!'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "The amount must be positive number"})

        # проверка отрицательной суммы
        response = self.client.post(reverse('balanceapp:transfer'),
                                    json.dumps({'amount': -5,
                                                'sender': self.sender.pk,
                                                'recipient': self.recipient.pk,
                                                'description': 'drakaris!'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "The amount must be positive number"})

        # проверка на возможность уйти в отрицательный баланс
        response = self.client.post(reverse('balanceapp:transfer'),
                                    json.dumps({'amount': 20000,
                                                'sender': self.sender.pk,
                                                'recipient': self.recipient.pk,
                                                'description': 'drakaris!'}), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": "There are not enough funds in the account"})


class TransactionTestCase(APITestCase):
    """
    Проверка отображения транзакций
    """
    def setUp(self):
        self.sender = Customer.objects.create(name="Daineris")
        self.recipient = Customer.objects.create(name="Khal")
        self.an_customer = Customer.objects.create(name="John")
        self.tran_1 = Transaction.objects.create(sender=self.sender, recipient=self.recipient, amount=500)
        self.tran_2 = Transaction.objects.create(sender=self.recipient, recipient=self.sender, amount=100)
        self.tran_3 = Transaction.objects.create(sender=self.an_customer, recipient=self.an_customer, amount=200)

    def tearDown(self):
        self.sender.delete()
        self.recipient.delete()

    def test_transaction_api_view(self):
        # проверка отображения списка транзакций без сортировки
        response = self.client.get(reverse('balanceapp:transactions', kwargs={'customer_id': self.sender.pk}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        response_data = response_data['results']
        queryset = Transaction.objects.filter(Q(recipient=self.sender) | Q(sender=self.sender)).order_by('pk')

        expected_data = list()
        for transaction in queryset:
            dictionary = dict()
            dictionary['id'] = transaction.pk
            dictionary['amount'] = f'{transaction.amount:.2f}'
            dictionary['timestamp'] = transaction.timestamp.isoformat(timespec='microseconds').replace('+00:00', 'Z')
            dictionary['description'] = transaction.description
            dictionary['sender'] = transaction.sender.pk
            dictionary['recipient'] = transaction.recipient.pk
            expected_data.append(dictionary)
        self.assertEqual(response_data, expected_data)

        # проверка отображения списка транзакций с сортировкой по дате
        response = self.client.get(reverse('balanceapp:transactions', kwargs={'customer_id': self.sender.pk}),
                                   data={'order': 'timestamp'},
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        response_data = response_data['results']
        queryset = Transaction.objects.filter(Q(recipient=self.sender) | Q(sender=self.sender)).order_by('timestamp')

        expected_data = list()
        for transaction in queryset:
            dictionary = dict()
            dictionary['id'] = transaction.pk
            dictionary['amount'] = f'{transaction.amount:.2f}'
            dictionary['timestamp'] = transaction.timestamp.isoformat(timespec='microseconds').replace('+00:00', 'Z')
            dictionary['description'] = transaction.description
            dictionary['sender'] = transaction.sender.pk
            dictionary['recipient'] = transaction.recipient.pk
            expected_data.append(dictionary)
        self.assertEqual(response_data, expected_data)

        # проверка отображения списка транзакций с сортировкой по сумме в убывающем порядке
        response = self.client.get(reverse('balanceapp:transactions', kwargs={'customer_id': self.sender.pk}),
                                   data={'order': '-amount'},
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        response_data = response_data['results']
        queryset = Transaction.objects.filter(Q(recipient=self.sender) | Q(sender=self.sender)).order_by('-amount')

        expected_data = list()
        for transaction in queryset:
            dictionary = dict()
            dictionary['id'] = transaction.pk
            dictionary['amount'] = f'{transaction.amount:.2f}'
            dictionary['timestamp'] = transaction.timestamp.isoformat(timespec='microseconds').replace('+00:00', 'Z')
            dictionary['description'] = transaction.description
            dictionary['sender'] = transaction.sender.pk
            dictionary['recipient'] = transaction.recipient.pk
            expected_data.append(dictionary)
        self.assertEqual(response_data, expected_data)

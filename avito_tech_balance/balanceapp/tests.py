from rest_framework.test import APITestCase

from balanceapp.models import Customer


class CustomerTestCase(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Den")

    def tearDown(self) -> None:
        self.customer.delete()

    def test_customer_create_api_view(self):
        """
        Проверка создания поставщика
        """
        post_data = {"name": "CCC"}
        response = self.client.post(reverse('contentapp:supplier-list'), json.dumps(post_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Supplier.objects.filter(name=post_data['name']).exists())
    #
    # def test_supplier_list_api_view(self):
    #     """
    #     Проверка отображения списка поставщиков
    #     """
    #     self.supplier = Supplier.objects.create(name="DDD")
    #     response = self.client.get(reverse('contentapp:supplier-list'))
    #     self.assertEqual(response.status_code, 200)
    #     queryset = Supplier.objects.all()
    #     expected_data = [{'id': supplier.pk, 'name': supplier.name} for supplier in queryset]
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response_data['results'], expected_data)
    #
    # def test_supplier_detail_api_view(self):
    #     """
    #     Проверка отображения детальной информации о поставщике
    #     """
    #     response = self.client.get(reverse('contentapp:supplier-detail', kwargs={"pk": self.supplier.pk}))
    #     self.assertEqual(response.status_code, 200)
    #     expected_data = {'id': self.supplier.pk, 'name': self.supplier.name}
    #     response_data = json.loads(response.content)
    #     self.assertEqual(response_data, expected_data)
    #
    # def test_supplier_update_api_view(self):
    #     """
    #     Проверка редактирования информации о поставщике
    #     """
    #     put_data = {'name': 'EEE'}
    #     response = self.client.put(reverse('contentapp:supplier-detail', kwargs={"pk": self.supplier.pk}),
    #                                json.dumps(put_data), content_type='application/json')
    #     self.assertEqual(response.status_code, 200)
    #     self.supplier.refresh_from_db()
    #     self.assertEqual(self.supplier.name, put_data['name'])
    #
    # def test_supplier_delete_api_view(self):
    #     """
    #     Проверка удаления поставщика
    #     """
    #     response = self.client.delete(reverse('contentapp:supplier-detail', kwargs={"pk": self.supplier.pk}))
    #     self.assertEqual(response.status_code, 204)
    #     self.assertFalse(Supplier.objects.filter(pk=self.supplier.pk))



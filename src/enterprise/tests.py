from rest_framework.test import APITestCase
from enterprise.models import GroupProperty, CorporateEntity
from enterprise.serializers import GroupPropertySerializer
from accounts.models import User
from django.db import connection

def reset_sqlite_sequence():
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='enterprise_groupproperty';")

class GroupPropertySerializerTest(APITestCase):
    def setUp(self):
        reset_sqlite_sequence()  # Reset the sequence for auto-increment
        self.user = User.objects.create_user(name='testuser', email='email@gmail.com', password='password')
        self.client.login(username='testuser', password='password')
        self.group = CorporateEntity.objects.create(name="Test Group", created_by=self.user)
        
        property_data = {
            "title": "Test Property",
            "address": "123 Real Estate Lane",
            "location": "Test City",
            "status": "available",
            "property_type": "land",
            "num_units": 1,
            "total_slots": 100,
            "initial_cost": 100000.00,
            "current_value": 120000.00,
            "currency": "USD",
            "group_owner": self.group,
        }
        self.property_instance = GroupProperty.objects.create(**property_data)

    def test_serializer_create(self):
        serializer = GroupPropertySerializer(data=self.property_instance)
        self.assertTrue(serializer.is_valid())
        property_instance = serializer.save()
        self.assertEqual(property_instance.slot_price, 1000.00)
        self.assertEqual(property_instance.slot_price_current, 1200.00)

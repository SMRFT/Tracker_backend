from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import serializers


from bson import ObjectId
class ObjectIdField(serializers.Field):
    def to_representation(self, value):
        return str(value)
    def to_internal_value(self, data):
        return ObjectId(data)
    

from .models import Employee
class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])  # Encrypt the password
        return super(EmployeeSerializer, self).create(validated_data)
    


from .models import Board
class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['boardId','boardName','boardColor','employeeId','employeeName','createdDate','createdTime']




from .models import Card
class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['boardId','boardName','employeeId','employeeName','cardId','cardName','columnId','createdDate','createdTime','startdate','enddate']
        

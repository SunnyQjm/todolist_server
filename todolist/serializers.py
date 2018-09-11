from rest_framework import serializers
from todolist.models import Task
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Task
        fields = ('id', 'content', 'tags', 'priority', 'finished', 'expire_date', 'owner')


class UserSerializer(serializers.ModelSerializer):
    # tasks = serializers.PrimaryKeyRelatedField(many=True, queryset=Task.objects.all())
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.password = make_password(user.password)
        user.save()
        return user



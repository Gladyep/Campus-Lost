from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'campus', 'role')
        read_only_fields = ('id', 'email', 'role')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'campus', 'password')
        read_only_fields = ('id',)

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        from django.contrib.auth import authenticate

        user = authenticate(request=self.context.get('request'), email=attrs['email'].lower(), password=attrs['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError('Email or password is incorrect.')
        refresh = RefreshToken.for_user(user)
        return {'access': str(refresh.access_token), 'refresh': str(refresh), 'user': ProfileSerializer(user).data}
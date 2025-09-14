# serializers.py

from rest_framework import serializers

class EmailSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=100)
    message = serializers.CharField()
    to_email = serializers.EmailField()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(required=False)  # Optional for initial request
    new_password = serializers.CharField(required=False)  # Optional for initial request

    def validate(self, data):
        # If OTP is present, new_password should also be present
        if 'otp' in data and not data.get('new_password'):
            raise serializers.ValidationError("New password is required when providing OTP")
        return data

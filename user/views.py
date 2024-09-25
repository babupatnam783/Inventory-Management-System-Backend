from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth.models import User

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .serializers import UserSerializer
from rest_framework import status


from django.shortcuts import get_object_or_404

@api_view(['POST'])
def registration(request):
    try:
        data = request.data
        serializer = UserSerializer(data= data)
        print(serializer)
        if not serializer.is_valid():
            return Response({ "errors": serializer.errors},status = status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username = data.get('username')).exists():
            return Response({"message": "Username already exists."},status = status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User created successfully.",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login(request):
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
    
        # user = User.objects.get(username=username)
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({"message":"User Login Successfully",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                },status=status.HTTP_200_OK)

        else:
            return Response({"status": 400, "message": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

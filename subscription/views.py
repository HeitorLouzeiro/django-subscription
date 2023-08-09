from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .serializers import RegisterSerializer


# Create your views here.
def home(request):
    return render(request, 'subscription/pages/home.html')


def check_mail_ajax(request):
    # check if this is an ajax request
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        email = request.GET.get('email', None)
        check_email = User.objects.filter(email=email).exists()
        if check_email:
            response = {'error': 'Email already exists'}
            return JsonResponse(response)
        else:
            response = {'success': 'Email is available'}
            return JsonResponse(response)
    else:
        response = {'error': 'Error email checking'}
        return JsonResponse(response)


class Register(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            password = make_password(serializer.data.get('password'))
            User.objects.filter(email=serializer.data.get(
                'email')).update(password=password)
            return Response({'success': 'Registration successful.'})
        else:
            return Response({'error': 'Error. Try again'})


class Login(APIView):
    def get(self, request):
        return render(request, 'subscription/pages/login.html')

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Let us check if the user exists or not...
        check_email = User.objects.filter(email=email).exists()
        if check_email is False:
            return Response({'error': 'No account with such email'})
        # We need to check if the user password is correct
        user = User.objects.get(email=email)
        if user.check_password(password) is False:
            return Response({'error': 'Password is not correct. Try again'})
        # Now let us log the user in
        log_user = auth.authenticate(email=email, password=password)
        if user is not None:
            auth.login(request, log_user)
            return Response({'success': 'Login successful'})
        else:
            return Response({'error': 'Invalid email/password. Try again later.'})

from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .serializers import RegisterSerializer


# Create your views here.
@login_required(login_url='login', redirect_field_name='next')
def home(request):
    try:
        user_membership = UserMembership.objects.get(user=request.user)
    except ObjectDoesNotExist:
        return redirect('endSubscription')

    subscriptions_exist = Subscription.objects.filter(
        user_membership=user_membership).exists()

    if not subscriptions_exist:
        # Redirect to subscription creation page
        return redirect('endSubscription')
    else:
        subscription = Subscription.objects.filter(
            user_membership=user_membership).last()

    return render(request, 'subscription/pages/home.html', {'subscription': subscription})


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
    def get(self, request):
        return render(request, 'subscription/pages/register.html')

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        userExist = User.objects.filter(
            username=request.data.get('username')).exists()

        if userExist:
            return Response({'error': 'User already exists'})

        if serializer.is_valid():
            serializer.save()
            obj = serializer.save(is_active=True)
            password = make_password(serializer.data.get('password'))
            User.objects.filter(email=serializer.data.get(
                'email')).update(password=password)
            get_membership = Membership.objects.get(membership_type='Free')
            instance = UserMembership.objects.create(
                user=obj, membership=get_membership)

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
        if not check_email:
            return Response({'error': 'No account with such email'})

        # Use the authenticate function to check email and password
        print(email, password)
        log_user = authenticate(request, email=email, password=password)
        if log_user is not None:
            # Authenticate successful, log the user in
            login(request, log_user)
            return Response({'success': 'Login successful'})
        else:
            return Response({'error': 'Invalid email/password. Try again later.'})


@login_required(login_url='login', redirect_field_name='next')
def logout(request):
    auth.logout(request)
    return redirect('login')


def subscription(request):
    return render(request, 'subscription/pages/subscription.html')


def subscribe(request):
    return render(request, 'subscription/pages/subscribe.html')


def endSubscription(request):
    return render(request, 'subscription/pages/end-subscription.html')

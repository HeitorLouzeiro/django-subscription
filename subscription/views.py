from datetime import datetime as dt
from datetime import timedelta

from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.crypto import get_random_string
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
        if request.user.is_authenticated:
            return redirect('home')
        else:
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
        if request.user.is_authenticated:
            return redirect('home')
        else:
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


@login_required(login_url='login', redirect_field_name='next')
def subscription(request):
    # All plans other than Free
    subscriptions = Membership.objects.filter(~Q(membership_type='Free'))
    context = {'subscriptions': subscriptions}
    return render(request, 'subscription/pages/subscription.html', context)


@login_required(login_url='login', redirect_field_name='next')
def subscribe(request):
    plan = request.GET.get('sub_plan')
    fecth_membership = Membership.objects.filter(membership_type=plan).exists()
    if not fecth_membership:
        return redirect('subscription')

    payment_for = Membership.objects.get(membership_type=plan)
    user_membership = UserMembership.objects.get(user=request.user)

    paystack_charge_id = get_random_string(50)
    paystack_access_code = get_random_string(50)
    amount = payment_for.price

    payhistory = PayHistory.objects.create(
        user=request.user, payment_for=payment_for,
        paystack_charge_id=paystack_charge_id,
        paystack_access_code=paystack_access_code, amount=amount, paid=True)

    payhistory.save()
    callback_url = reverse('callback')
    return redirect(callback_url + f'?paystack_charge_id={payhistory.paystack_charge_id}')


@login_required(login_url='login', redirect_field_name='next')
def callback(request):
    paystack_charge_id = request.GET.get('paystack_charge_id')

    # Retrieve the PayHistory instance or return a 404 response
    payhistory = get_object_or_404(
        PayHistory, paystack_charge_id=paystack_charge_id)

    # Retrieve the Membership instance associated with the PayHistory
    membership_instance = payhistory.payment_for

    # Retrieve the UserMembership instance for the current user
    subscribeplan = UserMembership.objects.get(user=request.user)

    # Update the membership attribute of the UserMembership instance

    subscribeplan.membership = membership_instance
    subscribeplan.save()

    return redirect('home')


@login_required(login_url='login', redirect_field_name='next')
def endSubscription(request):
    return render(request, 'subscription/pages/end-subscription.html')

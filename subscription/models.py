import calendar
from datetime import date
from datetime import datetime
from datetime import datetime as dt
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

today = date.today()

# Custom User Model Used Here


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of username.
    """

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        # Create the superuser using the parent class's method
        user = self.create_user(email, password, **extra_fields)

        # Create UserMembership for the superuser
        membership = Membership.objects.get(
            membership_type='Free')  # Change this as needed
        UserMembership.objects.create(user=user, membership=membership)

        return user


# This is User Profile
class User(AbstractUser):
    user_gender = (
        ('Male', 'Male'),
        ('Female', 'Female')
    )
    username = models.CharField(
        _('Username'), max_length=100, default='', unique=True)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    gender = models.CharField(max_length=10, default='', choices=user_gender)
    # mobile = models.CharField(max_length=200, null=True)
    photo = models.ImageField(
        upload_to='users', default="/static/images/profile1.png", null=True, blank=True)
    country = models.CharField(max_length=200, null=True)
    bio = models.TextField(default='', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    objects = UserManager()

    def __str__(self):
        return self.first_name + ' ' + self.last_name


# This is user settings
class UserSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, default=None)
    account_verified = models.BooleanField(default=False)
    verified_code = models.CharField(max_length=100, default='', blank=True)
    verification_expires = models.DateField(
        default=dt.now().date() + timedelta(days=settings.VERIFY_EXPIRE_DAYS))
    code_expired = models.BooleanField(default=False)
    recieve_email_notice = models.BooleanField(default=True)

# User Payment History


class PayHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    paystack_charge_id = models.CharField(
        max_length=100, default='', blank=True)
    paystack_access_code = models.CharField(
        max_length=100, default='', blank=True)
    payment_for = models.ForeignKey(
        'Membership', on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

# Membership


class Membership(models.Model):
    MEMBERSHIP_CHOICES = (
        ('Extended', 'Extended'),  # Note that they are all capitalize//
        ('Advanced', 'Advanced'),
        ('Medium', 'Medium'),
        ('Basic', 'Basic'),
        ('Free', 'Free')
    )
    PERIOD_DURATION = (
        ('Days', 'Days'),
        ('Week', 'Week'),
        ('Months', 'Months'),
    )
    slug = models.SlugField(null=True, blank=True)
    membership_type = models.CharField(
        choices=MEMBERSHIP_CHOICES, default='Free', max_length=30)
    duration = models.PositiveIntegerField(default=7)
    duration_period = models.CharField(
        max_length=100, default='Days', choices=PERIOD_DURATION)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.membership_type

# User Membership


class UserMembership(models.Model):
    user = models.OneToOneField(
        User, related_name='user_membership', on_delete=models.CASCADE)
    membership = models.ForeignKey(
        Membership, related_name='user_membership', on_delete=models.SET_NULL, null=True)
    reference_code = models.CharField(max_length=100, default='', blank=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=UserMembership)
def create_subscription(sender, instance, *args, **kwargs):
    # Definir a função add_months aqui
    def add_months(sourcedate, months):
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        # Convert to date object (Converta para objeto date)
        return datetime(year, month, day).date()

    try:
        subscription = Subscription.objects.get(user_membership=instance)

        if instance.membership.duration_period == 'Months':
            # Calculate new expiration date taking into account months
            # (Calcule a nova data de validade levando em consideração os meses)
            new_expiration_date = add_months(
                datetime.now().date(), instance.membership.duration)
        else:
            # Calculate new expiration date for other duration periods (Days, Weeks)
            # Calcular nova data de vencimento para outros períodos de duração (dias, semanas)
            new_expiration_date = datetime.now().date(
            ) + timedelta(days=instance.membership.duration)

        subscription.expires_in = new_expiration_date
        subscription.save()
    except Subscription.DoesNotExist:
        if instance.membership.duration_period == 'Months':
            new_expiration_date = add_months(
                datetime.now().date(), instance.membership.duration)
        else:
            new_expiration_date = datetime.now().date(
            ) + timedelta(days=instance.membership.duration)

        Subscription.objects.create(
            user_membership=instance, expires_in=new_expiration_date)

# User Subscription


class Subscription(models.Model):
    user_membership = models.ForeignKey(
        UserMembership, related_name='subscription', on_delete=models.CASCADE, default=None)
    expires_in = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.user_membership.user.username


@receiver(post_save, sender=Subscription)
def update_active(sender, instance, *args, **kwargs):
    if instance.expires_in < today:
        subscription = Subscription.objects.get(id=instance.id)
        subscription.delete()

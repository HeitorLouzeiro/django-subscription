# create_data.py
from django.core.management.base import BaseCommand

from subscription.models import Membership


def create_subscription():
    memberships = [
        {
            'slug': 'free',
            'membership_type': 'Free',
            'duration': 0,
            'duration_period': 'Days',
            'price': 0.00,
        },
        {
            'slug': 'basic',
            'membership_type': 'Basic',
            'duration': 7,
            'duration_period': 'Days',
            'price': 5.00,
        },
        {
            'slug': 'medium',
            'membership_type': 'Medium',
            'duration': 1,
            'duration_period': 'Months',
            'price': 15.00,
        },
        {
            'slug': 'advanced',
            'membership_type': 'Advanced',
            'duration': 3,
            'duration_period': 'Months',
            'price': 30.00,
        },
        {
            'slug': 'extended',
            'membership_type': 'Extended',
            'duration': 6,
            'duration_period': 'Months',
            'price': 60.00,
        },

    ]
    for membership_data in memberships:
        Membership.objects.create(
            slug=membership_data['slug'],
            membership_type=membership_data['membership_type'],
            duration=membership_data['duration'],
            duration_period=membership_data['duration_period'],
            price=membership_data['price']
        )


class Command(BaseCommand):
    help = 'Create subscription'

    def handle(self, *args, **options):
        create_subscription()
        self.stdout.write(self.style.SUCCESS(
            'Successfully created subscription'))

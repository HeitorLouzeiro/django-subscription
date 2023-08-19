import logging
from datetime import date

from django_cron import CronJobBase, Schedule

from .models import Subscription


class DailySubscriptionCleanup(CronJobBase):
    RUN_EVERY_MINS = 10  #

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    # Um código único para sua tarefa
    code = 'subscription.daily_subscription_cleanup'

    def do(self):
        today = date.today()
        subscriptions_to_delete = Subscription.objects.filter(
            expires_in__lt=today)
        subscriptions_to_delete.delete()
        logging.info('A tarefa cron foi executada com sucesso.')

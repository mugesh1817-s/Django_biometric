from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

class MyappConfig(AppConfig):
    name = 'myapp'


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: call_command('sync_attendance'), 'interval', minutes=20)
    scheduler.start()

from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: call_command('sync_attendance'), 'interval', minutes=3)
    scheduler.start()

from django.apps import AppConfig


class RegisterConfig(AppConfig):
    name = 'register'
    name1 = 'reports'
    def ready(self):
    	import register.signals
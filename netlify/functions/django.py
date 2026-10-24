import os

from serverless_wsgi import handle_request

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartcart.settings")

from smartcart.wsgi import application


def handler(event, context):
    return handle_request(application, event, context)
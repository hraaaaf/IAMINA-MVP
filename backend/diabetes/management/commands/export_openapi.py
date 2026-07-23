"""Export OpenAPI schema for the API."""
import json

from django.core.management.base import BaseCommand

from diabetes.api.main import api


class Command(BaseCommand):
    help = 'Export OpenAPI schema to JSON'

    def handle(self, *args, **options):
        schema = api.get_openapi_schema()
        print(json.dumps(schema, indent=2))

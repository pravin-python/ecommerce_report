# apps/pages/management/commands/save_urls_to_db.py

from django.core.management.base import BaseCommand
from apps.pages.management.save_urls_to_db import extract_and_save_urls

class Command(BaseCommand):
    help = 'Extract all project URLs (excluding apps.pages) and store them in the database'

    def handle(self, *args, **kwargs):
        extract_and_save_urls()
        self.stdout.write(self.style.SUCCESS('URLs saved to database (excluding apps.pages)'))

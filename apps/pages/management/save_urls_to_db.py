# apps/pages/utils/save_urls_to_db.py
import re 
from django.urls import get_resolver
from apps.pages.models import URLRecord
from django.urls.resolvers import URLPattern, URLResolver

EXCLUDED_NAMESPACE = "apps.pages"

def prettify_name(name: str) -> str:
    """Convert 'update-dashboard-component-position' to 'Update Dashboard Component Position'"""
    if not name:
        return ''
    return name.replace('_', ' ').replace('-', ' ').title()

def extract_and_save_urls():
    url_patterns = get_resolver().url_patterns
    flat_urls = []

    URLRecord.objects.all().delete()

    def collect_urls(patterns, prefix='', namespace=None):
        for entry in patterns:
            if isinstance(entry, URLResolver):
                module_str = getattr(entry.urlconf_module, '__name__', '')
                if EXCLUDED_NAMESPACE in module_str:
                    continue
                collect_urls(entry.url_patterns, prefix + str(entry.pattern._route), entry.namespace or namespace)
            elif isinstance(entry, URLPattern):
                full_pattern = prefix + str(entry.pattern._route)

                if re.search(r'<[^>]+>', full_pattern):
                    continue

                name = entry.name or ''
                show_name = prettify_name(name)
                flat_urls.append((full_pattern, name, show_name))

    collect_urls(url_patterns)

    for pattern, name, show_name in flat_urls:
        URLRecord.objects.get_or_create(
            url_pattern=pattern,
            name=name,
            defaults={'show_name': show_name}
        )

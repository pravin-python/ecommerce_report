from django.db import models

CHART_TYPES = (
    ('bar', 'Bar Chart'),
    ('area', 'Area Chart'),
    ('pie', 'Circular Chart'),
)

class DashboardComponent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_chart = models.BooleanField(default=False)
    is_table = models.BooleanField(default=False)
    chart_type = models.CharField(max_length=10, choices=CHART_TYPES, null=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    ajax_url = models.CharField(max_length=350, null=True)
    page_url = models.CharField(max_length=350, null=True)
    is_fillter = models.BooleanField(default=False)
    fillter_value = models.JSONField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self._state.adding and self.position == 0:
            max_position = DashboardComponent.objects.aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        super().save(*args, **kwargs)

    class Meta:
        db_table = "dashboardcomponent"
        ordering = ['position']

    def __str__(self):
        return self.name

class URLRecord(models.Model):
    url_pattern = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True, null=True)
    show_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('url_pattern', 'name')

    def __str__(self):
        return self.show_name or self.url_pattern
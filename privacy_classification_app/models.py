from django.db import models

class PolicyCache(models.Model):
    url = models.URLField(unique=True)
    last_updated_date = models.CharField(max_length=100, null=True, blank=True)
    cached_result = models.JSONField()
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url

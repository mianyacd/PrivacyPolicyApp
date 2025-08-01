from django.db import models

class PolicyCache(models.Model):
    url = models.URLField(unique=True)
    last_updated_date = models.CharField(max_length=100, null=True, blank=True)
    cached_result = models.JSONField()
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url


class AnalyzedSentence(models.Model):
    url = models.URLField()
    category = models.CharField(max_length=100)  # e.g., "First Party Collection/Use"
    sentence = models.TextField()

    attribute = models.CharField(max_length=100)  # e.g., "Personal Information Type"
    span = models.TextField()
    predicted_value = models.TextField()

    does_or_not_value = models.CharField(max_length=20, null=True, blank=True)
    does_or_not_span = models.TextField(null=True, blank=True)

    purpose_value = models.TextField(null=True, blank=True)
    purpose_span = models.TextField(null=True, blank=True)

    third_party_entity = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} | {self.attribute} | {self.predicted_value}"

from django.conf import settings
from django.db import models


class Garage(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='garages',
    )
    garage_name = models.CharField(max_length=200)
    address = models.TextField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'garages'
        ordering = ['garage_name']

    def __str__(self):
        return self.garage_name

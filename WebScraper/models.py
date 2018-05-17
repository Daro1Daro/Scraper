from django.db import models


class Product(models.Model):
    #id = models.ForeignKey('auth.User')
    index = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    producer = models.CharField(max_length=50)
    price = models.CharField(max_length=20)
    price_old = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=15)
    url = models.URLField()

    def __str__(self):
        return self.name

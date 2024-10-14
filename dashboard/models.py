from django.db import models


class Resource(models.Model): 
    resource = models.ImageField(max_length=254, upload_to="resources", null=False, blank=False)
    
    def __str__(self):
        return self.resource.url


class Tag(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    tag = models.CharField(max_length=254, null=False, blank=False)
    embedding = models.JSONField(null=True, blank=True)

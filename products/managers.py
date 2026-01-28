from django.db import models

# QuerySet and Manager to handle active/inactive products
class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)



class ActiveManager(models.Manager):
    def get_queryset(self):
        return ActiveQuerySet(self.model, using=self._db).active()

    def all_with_inactive(self):
        return ActiveQuerySet(self.model, using=self._db)


from __future__ import unicode_literals

from django.db import models

# class Ssh_keys(models.Model):
#     ENVIRONMENTS = (
#         ('DEV', 'Development'),
#         ('STG', 'Staging'),
#         ('PROD', 'Production'),
#     )

#     hostname   =   models.CharField(max_length=200)
#     env        =   models.CharField(max_length=4, choices=ENVIRONMENTS)
#     username   =   models.CharField(max_length=200)
#     key        =   models.CharField(max_length=512)

#     def __str__(self):
#         return "[SSH_KEYS] Hostname: %s, Username: %s" % (self.hostname, self.username)

from __future__ import unicode_literals

from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.db import models
import logging

COMMENT_PHRASE = "#CronUI#"
CONNECT_TIMEOUT = 16

class Server(models.Model):
    ENVIRONMENTS = (
        ('DEV', 'Development'),
        ('STG', 'Staging'),
        ('PROD', 'Production'),
    )
    hostname   =   models.CharField(max_length=200, primary_key=True)
    env        =   models.CharField(max_length=4, choices=ENVIRONMENTS)

    def __str__(self):
        return "[SERVER] Hostname: %s, Env: %s" % (self.hostname, self.env)

    @classmethod
    def create(cls, hostname, env):
        server = cls(hostname=hostname, env=env)
        return server


class User(models.Model):
    server     =   models.ForeignKey(Server, on_delete=models.CASCADE)
    username   =   models.CharField(max_length=200)

    def __str__(self):
        return "[USER] Server: %s, Username: %s" % (self.server.hostname, self.username)

class Cron(models.Model):
    user            =   models.ForeignKey(User, on_delete=models.CASCADE)
    title           =   models.CharField(max_length=999)
    comment         =   models.CharField(max_length=999)
    minute          =   models.CharField(max_length=999)
    hour            =   models.CharField(max_length=999)
    day             =   models.CharField(max_length=999)
    month           =   models.CharField(max_length=999)
    weekday         =   models.CharField(max_length=999)
    command         =   models.CharField(max_length=999)
    active          =   models.BooleanField(default=True)
    timestamp       =   models.DateTimeField(auto_now_add=True)
    prevTimestamp  =   models.DateTimeField(auto_now_add=True)

    def prettyPrint(self):
        if not self.active:
            return "%s%s %s %s %s %s %s\n" % (COMMENT_PHRASE, self.minute, self.hour, self.day, self.month, self.weekday, self.command)
        return "%s %s %s %s %s %s\n" % (self.minute, self.hour, self.day, self.month, self.weekday, self.command)

    def __eq__(self, target):
        return (
            isinstance(target, self.__class__) and \
            (self.user == target.user and \
            self.minute == target.minute and \
            self.hour == target.hour and \
            self.day == target.day and \
            self.month == target.month and \
            self.weekday == target.weekday and \
            self.command == target.command)
        )

    def __ne__(self, target):
        return not self.__eq__(other)

    def __str__(self):
        return "[CRON] id: %s, %s/%s, job: %s" % (self.id, self.user.server.hostname, self.user.username, self.prettyPrint())

# Custom Exception for logic implementations
class DisplayLogicException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
from django.shortcuts import render, get_object_or_404
from .models import *
from logic import *
from django import forms
import logging

logger = logging.getLogger(__name__)

class AddJobForm(forms.Form):
    minute   =   forms.CharField(widget=forms.Textarea, label='Minute', max_length=999)
    hour     =   forms.CharField(widget=forms.Textarea, label='Hour', max_length=999)
    day      =   forms.CharField(widget=forms.Textarea, label='Day', max_length=999)
    month    =   forms.CharField(widget=forms.Textarea, label='Month', max_length=999)
    weekday  =   forms.CharField(widget=forms.Textarea, label='Weekday', max_length=999)
    comment  =   forms.CharField(widget=forms.Textarea, label='Comment', max_length=999)
    command  =   forms.CharField(widget=forms.Textarea, label='Command', max_length=999)

    def __init__(self, *args, **kwargs):
        super(AddJobForm, self).__init__(*args, **kwargs)
        self.fields['minute'].widget.attrs['cols'] = 1
        self.fields['minute'].widget.attrs['rows'] = 1
        self.fields['hour'].widget.attrs['cols'] = 1
        self.fields['hour'].widget.attrs['rows'] = 1
        self.fields['day'].widget.attrs['cols'] = 1
        self.fields['day'].widget.attrs['rows'] = 1
        self.fields['month'].widget.attrs['cols'] = 1
        self.fields['month'].widget.attrs['rows'] = 1
        self.fields['weekday'].widget.attrs['cols'] = 1
        self.fields['weekday'].widget.attrs['rows'] = 1
        self.fields['comment'].widget.attrs['rows'] = 1
        self.fields['command'].widget.attrs['rows'] = 1

def index(request):
    userList = []
    context = {}
    if request.method == 'POST':
        targetUser = User.objects.get(id=request.POST.get('user-id'))
        if request.POST.get("DEL"):
            logger.info("Removing %s from database..", targetUser)
            targetUser.delete()
            context['result'] = 'success'
            context['msg'] = "User %s removed from database" % targetUser.username
        elif request.POST.get("SYNC"):
            logger.info("Sync %s/%s to database..", targetUser.server.hostname, targetUser.username)
            try:
                context = { "result": "success", "msg": syncCrontabToDatabase(targetUser) }
            except DisplayLogicException as e:
                context = { "result": "failure", "msg": e }
    for userObject in User.objects.all().order_by('server', 'username'):
        userList.append(userObject)
    context['userList'] = userList
    return render(request, 'display/index.html', context)

def show(request, hostname, username):
    context = {}
    userObject = get_object_or_404(User, username=username, server=hostname)
    add_job_form = AddJobForm(auto_id=False, initial={'server': hostname, 'user': username})
    if request.method == 'POST':
        # get all cron jobs
        jobList = Cron.objects.filter(id__in=request.POST.getlist('job'))
        # Triage depending on which button clicked
        if request.POST.get("DEL"):
            for job in jobList:
                logger.info("Removing %s from database..", job)
                job.delete()
        elif request.POST.get("ON"):
            try:
                context = { "result": "success", "msg": processCronRequest(userObject, jobList, "ON") }
            except DisplayLogicException as e:
                context = { "result": "failure", "msg": e }
        elif request.POST.get("OFF"):
            try:
                context = { "result": "success", "msg": processCronRequest(userObject, jobList, "OFF") }
            except DisplayLogicException as e:
                context = { "result": "failure", "msg": e }
        elif request.POST.get("ADD"):
            add_job_form = AddJobForm(request.POST)
            if add_job_form.is_valid():
                # Add new cron here and insert into jobList
                jobList = [Cron(user=userObject, minute=add_job_form.cleaned_data["minute"], hour=add_job_form.cleaned_data["hour"], day=add_job_form.cleaned_data["day"], \
                                month=add_job_form.cleaned_data["month"], weekday=add_job_form.cleaned_data["weekday"], comment=add_job_form.cleaned_data["comment"], \
                                command=add_job_form.cleaned_data["command"])]
                try:
                    context = { "result": "success", "msg": processCronRequest(userObject, jobList, "ADD") }
                except DisplayLogicException as e:
                    context = { "result": "failure", "msg": e }
            else:
                logger.warn("Form is not valid...")
        elif request.POST.get("SYNC"):
            logger.info("Sync %s/%s to database..", userObject.server.hostname, userObject.username)
            try:
                context = { "result": "success", "msg": syncCrontabToDatabase(userObject) }
            except DisplayLogicException as e:
                context = { "result": "failure", "msg": e }
        elif request.POST.get("REMOVE"):
            logger.info("Removing user %s from server %s from database..", userObject.username. userObject.server.hostname)
            userObject.delete()
            context['result'] = 'success'
            context['msg'] = "User %s/%s removed from database" % (userObject.server.hostname, userObject.username)
            userList = []
            for userObject in User.objects.all().order_by('server', 'username'):
                userList.append(userObject)
            context['userList'] = userList
            return render(request, 'display/index.html', context)

    cronList = Cron.objects.filter(user=userObject)

    context['username'] = userObject.username
    context['hostname'] = hostname
    context['cronList'] = cronList
    context['form']     = add_job_form

    return render(request, 'display/show.html', context)

#get_list_or_404

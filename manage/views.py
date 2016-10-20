from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django import forms
from logic import *
from display.models import *

logger = logging.getLogger(__name__)
class ImportForm(forms.Form):
    server   =   forms.CharField(label='Server Name', max_length=200)
    env      =   forms.ChoiceField(choices=[("DEV", "DEV"), ("STG", "STG"), ("PROD", "PROD"),])
    user     =   forms.CharField(label='User Name', max_length=200)
    crontab  =   forms.CharField(widget=forms.Textarea, required=False)

class SSHForm(forms.Form):
    server   =   forms.CharField(label='Server Name', max_length=200)
    env      =   forms.ChoiceField(choices=[("DEV", "DEV"), ("STG", "STG"), ("PROD", "PROD"),])
    user     =   forms.CharField(label='User Name', max_length=200)
    ssh_key  =   forms.CharField(widget=forms.Textarea)


def index(request):
    import_form = ImportForm(auto_id=False)
    context = {}
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        import_form = ImportForm(request.POST)

        # check whether it's valid:
        if import_form.is_valid():
            # process the data in form.cleaned_data as required
            context = processForm(import_form)
            try:
                if len(context["errJobs"]) > 0:
                    context['error'] = context["errJobs"]
            except (TypeError, KeyError) as e:
                pass

    context['form'] = import_form
    return render(request, 'manage/index.html', context)

def ssh(request):
    userList = []
    context = {}
    if request.method == 'POST':
        logger.debug("POST payload is: %s" % request.POST)
        # Test SSH Key
        if request.POST.get('action') == "test":
            userObj = User.objects.all().get(id=request.POST.get("userid"))
            resultDict = testServerConnection(userObj)
            context['result'] = resultDict['result']
            context['msg'] = resultDict['msg']

    # retrieve ssh key from user
    pkey = retrievePublicKey()

    for userObject in User.objects.all().order_by('server', 'username'):
        userList.append(userObject)

    context['userList'] = userList
    context['pkey'] = pkey
    return render(request, 'manage/ssh.html', context)

# This method is unused. Remove during refactor
# def ssh(request):
#     ssh_form = SSHForm(auto_id=False)
#     keyList = []
#     context = {}
#     if request.method == 'POST':
#         # There are several possible posts: add, test, or delete SSH Key

#         # Add SSH Key
#         ssh_form = SSHForm(request.POST)

#         if ssh_form.is_valid():
#             addSshKey(ssh_form.cleaned_data["server"], ssh_form.cleaned_data["env"], ssh_form.cleaned_data["user"], ssh_form.cleaned_data["ssh_key"])
#             context['result'] = "OK"

#         # Test SSH Key
#         if request.POST.get('action') == "test":
#             sshKeyObject = Ssh_keys.objects.all().get(id=request.POST.get("key"))
#             testSshKey(sshKeyObject)

#         # Remove SSH Key[s]
#         if request.POST.get('action') == "delete":
#             existingKeyList = Ssh_keys.objects.filter(id__in=request.POST.getlist('key'))
#             for key in existingKeyList:
#                 logger.debug("Deleting", key)
#                 key.delete()

#     for keyObject in Ssh_keys.objects.all().order_by('hostname', 'username'):
#         masked_key = keyObject.key[:10] + "..." + keyObject.key[-10:]
#         keyObject.key = masked_key
#         keyList.append(keyObject)

#     context['keyList'] = keyList
#     context['form'] = ssh_form
#     logger.debug(context)
#     return render(request, 'manage/ssh.html', context)

#
# TODO: Implement DELETE SSH!!!
#

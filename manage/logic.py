from display.models import *
from display.logic import parseJobs
from models import *
import os
import paramiko
import re
import socket
from crontab import CronTab, CronSlices
import logging

#Valid952HostnameRegex = r'(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])'
CronRegex = r''
logger = logging.getLogger(__name__)

# If there is invalid cron, returns dictionary with key "errJobs" will contain list of error crontabs
def processForm(form):
	server = form.cleaned_data["server"]
	env  = form.cleaned_data["env"]
	user = form.cleaned_data["user"]
	crontab = form.cleaned_data["crontab"]
	resultDict = {}
	logger.debug("server: %s\tenv: %s\tuser: %s" % (server, env, user))
	# # Server name must conform to standard
	# if ( not re.search(Valid952HostnameRegex, server) ):
	# 	logger.error("INVALID SERVER SETTING. EXIT")
	# 	resultDict["msg"] = "INVALID SERVER SETTING."
	# 	resultDict["result"] = "Failure"
	# 	return resultDict

	# create new if not existing
	if not Server.objects.filter(hostname=server, env=env):
		serverObj = Server(hostname=server, env=env)
		serverObj.save()
	else:
		serverObj = Server.objects.get(hostname=server, env=env)
	if not User.objects.filter(server=serverObj, username=user):
		userObj = User(server=serverObj, username=user)
		userObj.save()
	else:
		userObj = User.objects.get(server=serverObj, username=user)

	parseResult = parseJobs(crontab.split("\n"), userObj)

	resultDict["errJobs"] = parseResult['errorJobs']
	# Do not proceed if there are any error jobs
	if (len(parseResult['errorJobs']) > 0):
		logger.error("There are some jobs which are not valid. returning error")
		resultDict["msg"] = "The following cron jobs are invalid:"
		resultDict["result"] = "Failure"
		return resultDict

	#
	# Insert all successJobs to DB
	#
	# If there are existing crons, DELETE THEM ALL
	existingJobList = Cron.objects.filter(user=userObj)
	for job in existingJobList:
		job.delete()
	# Insert
	for newJob in parseResult['successJobs']:
		newJob.save()

	resultDict["result"] = "Success"
	resultDict["msg"] = "Cron import successful"

	return resultDict

def retrievePublicKey():
	cmdpt = os.popen("cat ~/.ssh/id_rsa.pub",'r',1)
	return cmdpt.read()

def testServerConnection(userObj):
	TIMEOUT = 16
	sshClient = paramiko.SSHClient()
	sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		sshClient.connect(userObj.server.hostname, username=userObj.username, look_for_keys=True, timeout=TIMEOUT)
	except (paramiko.SSHException, socket.error, paramiko.AuthenticationException) as se:
		logger.error("Error with connecting to target server %s as user %s" % (userObj.server.hostname, userObj.username), exc_info=True)
		return { "result": "failure", "msg": se }
	return { "result": "success", "msg": "Successfully connected to server '%s' as user '%s'" % (userObj.server.hostname, userObj.username) }


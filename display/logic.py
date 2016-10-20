from .models import *
from datetime import datetime, date
from django.utils import timezone
from django.db import transaction
import os
import paramiko
import re
import socket
import codecs
import logging
from crontab import CronTab, CronSlices

logger = logging.getLogger(__name__)
def syncCrontabToDatabase(userObj):
    if not userObj:
        raise DisplayLogicException("User object is null or not specified." )

    try:
        sshClient = initSsh(userObj.server.hostname, userObj.username)
        crontabAsList = getRemoteCrontab(sshClient, userObj)
        if (len(crontabAsList) == 0):
            for cronObj in Cron.objects.filter(user=userObj):
                cronObj.delete()
            raise DisplayLogicException("No jobs exist in remote's crontab. Removed all cron entries.")
        # process each cron (logic similar to "import" implementation)
        parseResult = parseJobs(crontabAsList, userObj)
    except DisplayLogicException:
        raise

    with transaction.atomic():
        # delete all crons not in target list first
        for serverJob in Cron.objects.filter(user=userObj):
            if objectInList(parseResult['successJobs'], serverJob) is None:
                logger.debug("Deleting cron: %s", serverJob)
                serverJob.delete()
        # modify or add new crons to DB
        serverJobList = Cron.objects.filter(user=userObj)
        for job in parseResult['successJobs']:
            serverJob = objectInList(serverJobList, job)
            if serverJob is not None:
                # need to only set active flag (since all else is same)
                serverJob.active = job.active
                serverJob.save()
                logger.info("Updated cron: %s", serverJob)
            else:
                logger.info("Created new cron: %s", job)
                job.save()

    return "Cron sync successful."

def getRemoteCrontab(ssh_client, userObj):
    stdin, stdout, stderr = ssh_client.exec_command("crontab -l")
    crontabAsList = stdout.readlines()
    stderrMsg = stderr.readlines()
    if (stderrMsg and "no crontab for %s" % userObj.username in stderrMsg[0]):
        logger.warn("no crontabs set for user %s" % userObj.username)
        return []
    elif (stderrMsg):
        errorMsg = ""
        for line in stderrMsg:
            errorMsg += line
        logger.error(errorMsg)
        raise DisplayLogicException("Error with extracting crontab for user %s/%s" % (userObj.server.hostname, userObj.username))
    return crontabAsList


def objectInList(list, object):
    for item in list:
        if item == object:
            return item
    return None
        

def parseJobs(crontab, userObj):
    successJobs = []
    errorJobs = []
    # Parse each line of cron
    for line in crontab:
        line = line.strip()
        activeFlag = True
        # if cron starts with COMMENT_PHRASE, then init Cron object with active = False
        if line.find(COMMENT_PHRASE) == 0:
            line = line[len(COMMENT_PHRASE):].strip()
            activeFlag = False
        elif not line or line[0] == "#":
            continue

        cronObj = CronTab()
        cronSplit = line.split(None, 5)
        # Create a CronTab object from the python-crontab library. This is different from "Crontab" object which is defined in display/models.py
        try:
            jobObj = cronObj.new(command=cronSplit[5])
            # setall() returns false if cron slice validity check fails
            if not jobObj.setall("%s %s %s %s %s" % (cronSplit[0], cronSplit[1], cronSplit[2], cronSplit[3], cronSplit[4])):
                logger.warn("Crontab '%s' is invalid. Skipping...", line)
                errorJobs.append(line)
                continue
        except IndexError:
            logger.error("Crontab '%s' has insufficient parameters. Skipping...", line)
            errorJobs.append(line)
            continue

        successJobs.append(Cron(user=userObj, minute=cronSplit[0], hour=cronSplit[1], day=cronSplit[2],\
                                 month=cronSplit[3], weekday=cronSplit[4], command=cronSplit[5], active = activeFlag))

    if len(errorJobs) > 0:
        raise DisplayLogicException("Server-side Cron parsing failed. Aborting sync on server %s." % userObj.server.hostname)
    return {'successJobs' : successJobs, 'errorJobs' : errorJobs}


def exec_command_or_error(sshClient, command, errorMsg=""):
    stdin, stdout, stderr = sshClient.exec_command(command)
    if stderr.readlines():
        logger.error(stderr.readlines())
        raise DisplayLogicException(errorMsg)
    return stdout

# mode = "OFF", "ON", "ADD"
# In the case of add, jobList should contain the cron to be appended to the crontab.
def processCronRequest(userObj, jobList, mode):
    # Some parameter checking
    if mode not in ["OFF", "ON", "ADD"]:
        raise DisplayLogicException("Invalid mode set (problem with internal logic)" )
    if not userObj:
        raise DisplayLogicException("UserObj is empty (problem with internal logic)" )
    if len(jobList) == 0:
        raise DisplayLogicException("No target jobs selected." )

    # initialize some variables
    dateObj = datetime.now()
    curTime = dateObj.strftime("%Y%m%d%H%M%S")
    curTimeYear = dateObj.strftime("%Y")
    curTimeMonthDay = dateObj.strftime("%m%d")
    serverBackupFilename  = "./work/%s/%s/cronUI_backup/crontab.%s.bck" % (curTimeYear, curTimeMonthDay, curTime)
    serverReleaseFilename = "./work/%s/%s/cronUI_backup/crontab.%s.release" % (curTimeYear, curTimeMonthDay, curTime)
    localBackupFilename   = "./%s.%s.crontab.%s" % (userObj.server.hostname, userObj.username, curTime)
    localReleaseFilename  = "./%s.%s.crontab.%s.release" % (userObj.server.hostname, userObj.username, curTime)

    try:
        sshClient = initSsh(userObj.server.hostname, userObj.username)
        # create work directory
        exec_command_or_error(sshClient, "mkdir -p ~/work/`date '+%Y'`/`date '+%m%d'`/cronUI_backup/", "Unable to create work directory on remote server.")
        # backup cron on server
        stdin, stdout, stderr = sshClient.exec_command("crontab -l > %s" % serverBackupFilename)
        if "no crontabs set for user" in stderr.readlines():
            logger.warn("[%s] %s" % (userObj.server.hostname, stderr.readlines()))
        # get crontab
        ftp = sshClient.open_sftp()
        try:
            getFile(ftp, localBackupFilename, serverBackupFilename, 3)
        except IOError:
            logger.error("Unable to copy backup cron file to local server.", exc_info=True)
            raise DisplayLogicException("Unable to copy backup cron file to local server.")
        # make modifications and create new local file
        if (mode in ["ON", "OFF"]):
            jobListAsString = []
            for cronObj in jobList:
                jobListAsString.append(cronObj.prettyPrint())
            toggleJobs(localBackupFilename, localReleaseFilename, jobListAsString, mode)
        elif (mode == "ADD"):
            addJob(localBackupFilename, localReleaseFilename, jobList[0])
            
        # put release file to server
        ftp.put(localReleaseFilename, serverReleaseFilename, confirm = True)
        
        exec_command_or_error(sshClient, "crontab %s" % serverReleaseFilename, "Unable to set crontab for %s/%s" % (userObj.server.hostname,userObj.username))
        stdout = exec_command_or_error(sshClient, "crontab -l | diff -b %s -" % serverReleaseFilename, "Unable to execute diff command for %s/%s" % (userObj.server.hostname,userObj.username))
        if len(stdout.readlines()) != 0:
            errorMsg = "[CRIT] Set cron does NOT match released version:\n"
            for line in stdout.readlines():
                errorMsg += line
            logger.error(errorMsg)
            raise DisplayLogicException("Set cron does NOT match released version.\nThis is a critical error, please investigate in %s" % userObj.server.hostname)
    except DisplayLogicException:
        raise

    # Success at this point. Update DB
    with transaction.atomic():
        for cronJob in jobList:
            prevActive = cronJob.active
            if mode is "OFF":
                cronJob.active = False;
            elif mode is "ON":
                cronJob.active = True;
            cronJob.prevTimestamp = cronJob.timestamp
            cronJob.timestamp = timezone.now()
            cronJob.save()
            if (prevActive != cronJob.active):
                logger.info("Job toggled to %s: %s", mode, cronJob)

    # Remove files from local system
    os.remove(localBackupFilename)
    os.remove(localReleaseFilename)
    return "Set cron for server '%s' as user '%s' at time %s" % (userObj.server.hostname, userObj.username, datetime.now().strftime("%B %d, %Y, %H:%M:%S"))

def getFile(ftp_client, local, remote, retries):
    count = 0
    while True:
        try:
            ftp_client.get(remote, local)
            break
        except IOError as e:
            if (count > retries):
                raise e
            else:
                count += 1

def toggleJobs(inputFile, outputFile, jobList, mode):
    try:
        inp  = codecs.open(inputFile, "r")
        outp = codecs.open(outputFile, "w")
    except IOError as e:
        logger.error("Opening file failed:", exc_info=True)
        return

    strippedList = stripAll(jobList)
    newJobList = modifyJobs(crontabAsList=inp, targetsAsList=strippedList, mode=mode)

    for line in newJobList:
        outp.write(line)

    inp.close()
    outp.close()
    
def addJob(inputFile, outputFile, targetJob):
    try:
        inp  = codecs.open(inputFile, "r")
        outp = codecs.open(outputFile, "w")
    except IOError as e:
        logger.error("Opening file failed:", exc_info=True)
        return

    for line in inp:
        outp.write(line)
        
    if not targetJob:
        logger.warn("Job to add is not specified for input file [%s]." % inputFile)
    else:
        jobAsString = ""
        # If comment is provided, then add that line before cron job
        if (len(targetJob.comment) > 0):
            jobAsString = "# %s\n" % targetJob.comment
        jobAsString += targetJob.prettyPrint()
        outp.write(jobAsString)

    inp.close()
    outp.close()
    
    if not os.path.isfile(outputFile):
        raise DisplayLogicException("Unable to create release version of cron file on local server.")

def modifyJobs(crontabAsList = [], targetsAsList = [], mode = ""):
    jobList = []
    for job in crontabAsList:
        jobLine = job
        if job.strip() in targetsAsList:
            index = jobLine.find(COMMENT_PHRASE)
            if mode == "OFF":
                if index != -1:
                    jobLine = job
                else:
                    jobLine = COMMENT_PHRASE + job
            elif mode == "ON":
                if index == -1:
                    jobLine = job
                else:
                    jobLine = jobLine[index+len(COMMENT_PHRASE):]

        jobList.append(jobLine)

    return jobList

def stripAll(list):
    newList = []
    for item in list:
        newList.append(item.strip())

    return newList

def initSsh(hostname, username):
    sshClient = paramiko.SSHClient()
    sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        sshClient.connect(hostname, username=username, look_for_keys=True, timeout=CONNECT_TIMEOUT)
        return sshClient
    except (paramiko.SSHException, socket.error, paramiko.AuthenticationException) as se:
        logger.error("Error with connecting to target server %s as user %s" % (hostname, username), exc_info=True)
        raise DisplayLogicException("Unable to connect to %s as user %s. Please check ssh key and/or security settings." % (hostname, username))

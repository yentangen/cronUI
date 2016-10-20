CronUI
==========

## Release Notes
- 0.0.1
Initial Commit

==========================================================================================================================

CronUI is a simple, centralized crontab management tool developed in Python2.7 using the Django framework.
This tool utilizes a web interface and SSH (non-pass) in order to provide users with the following features:

1. Import a crontab, providing details such as server and user (imports into CronUI database).
2. Turn ON/OFF a crontab via SSH.
3. Remove a cron job from CronUI management console.
4. Sync a crontab to CronUI database via SSH.

After starting the Django project, it's only the matter of inputting the host server's public SSH key into the target server/user's authorized_keys file before CronUI can begin managing the user's crontab.

## Using Brand New CentOS Server

  yum install -y centos-release-scl
  yum install -y python27
  yum groupinstall "Development tools"
  yum install -y gcc gcc-c++ libffi-devel python-devel openssl-devel zlib python-setuptools


  (postgresql) yum install postgresql-devel

## Required Packages

  python-crontab
  paramiko
  django
  django-nose


## Setting Up

1. Start CronUI after connecting it to webserver of your choice.
2. On server hosting CronUI, create a RSA key pair in ~/.ssh directory of user hosting CronUI.
3. Check http://<hostname>:<port>/manage/ssh and check that the public key for the server exists.
4. Insert the public key into target server/user's authorized_keys file.
5. [OPTIONAL] http://<hostname>:<port>/manage/ssh should have the server listed as an entry below the public key. Pressing "Test" button will perform simple SSH connection test.
6. On http://<hostname>:<port>/manage page, type in server/env/user information and, optionally, the crontab (can leave blank and "sync" later)
7. [Optional] Go to Display tab and "Sync" the server
8. Clicking on the user in the Display tab will display the jobs parsed or synced from the target server.


## Risk Hedge

CronUI logic attempts to preserve the current state of the crontab on the server as much as possible.
Thus, when performing operations using the interface, ordering, comments, and cron jobs themselves are all kept the same.
The only change performed in the crontab is the comment out phrase (ie "#CronUI#") that is prepended or removed from a cron job, indicating "OFF" or "ON", respectively, of the job managed by CronUI.

All before/after crontab changes will be saved as backup files in the target server's ~/work/<<YEAR>>/<<MMDD>>/cronUI_backup/ directory.
In the event that this tool fails, manual recovery to a previous state is still possible.


## Contribute
CronUI was originally created with the intent of learning Python/Django framework, as well as provide a simple solution to crontab management in place of a more sophisticated tool such as some open-source job schedulers.

Feedback is encouraged, and contributions are even more welcomed.
Please fork away!

## License
[MIT](LICENSE.md)


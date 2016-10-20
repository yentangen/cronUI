from django.test import TestCase

from .models import *
from .logic import *

class CrontabManipulateTests(TestCase):

    SERVER = "192.168.33.7"
    USERNAME = "vagrant"
    SERVEROBJ = None
    USEROBJ = None

    SSHCLIENT = None

    CRONTAB = [ "# This is a comment", \
                "* * * * * This is correct syntax", \
                "1 1 1 2 3 This should also be accepted", \
                "#CronUI# Comment in middle", \
                "* * * * missing one parameter", \
                "a b c d e invalid parameters", \
                "# Comment in middle", \
                "# Comment in middle", \
                "*/3 1 1 1 1 should pass",
              ]

    @classmethod
    def setUpClass(cls):
        super(CrontabManipulateTests, cls).setUpClass()
        cls.SERVEROBJ = Server(hostname = cls.SERVER, env = "DEV")
        cls.SERVEROBJ.save()
        cls.USEROBJ = User(server = cls.SERVEROBJ, username = cls.USERNAME)
        cls.USEROBJ.save()

        cls.SSHCLIENT = paramiko.SSHClient()
        cls.SSHCLIENT.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cls.SSHCLIENT.connect(cls.SERVER, username=cls.USERNAME, look_for_keys=True, timeout=CONNECT_TIMEOUT)

    # helper assert function
    def assertRaisesWithMessage(self, exc, msg, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            self.fail()
        except Exception as inst:
            self.assertRaises(exc)
            self.assertEqual(inst.message, msg)

#     def test_get_remote_crontab_normal(self):
#
#         result = getRemoteCrontab(self.SSHCLIENT, self.USEROBJ)
#         self.assertEqual(result, [])


    def test_get_remote_crontab_no_crontab(self):

        self.SSHCLIENT.exec_command("crontab -r")
        result = getRemoteCrontab(self.SSHCLIENT, self.USEROBJ)
        self.assertEqual(result, [])

    def test_modify_jobs_comment_out(self):
        """
        Comments out cron, prepending it with "COMMENT_PHRASE" value
        """

        targetList = [ "* * * * missing one parameter", \
                       "*/3 1 1 1 1 should pass", \
                       "#CronUI# Comment in middle",
                     ]

        resultList = modifyJobs(crontabAsList = self.CRONTAB, targetsAsList = targetList, mode = "OFF")
        self.assertIn("# This is a comment", resultList)
        self.assertIn("* * * * * This is correct syntax", resultList)
        self.assertIn("1 1 1 2 3 This should also be accepted", resultList)
        self.assertIn("#CronUI# Comment in middle", resultList)
        self.assertIn("#CronUI#* * * * missing one parameter", resultList)
        self.assertIn("a b c d e invalid parameters", resultList)
        self.assertIn("# Comment in middle", resultList)
        self.assertIn("#CronUI#*/3 1 1 1 1 should pass", resultList)

    def test_modify_jobs_comment_in(self):
        """
        Comments in cron, removing the "COMMENT_PHRASE" value from beginning of job
        """

        targetList = [
                       "#CronUI# Comment in middle",
                       "*/3 1 1 1 1 should pass",
                     ]

        resultList = modifyJobs(crontabAsList = self.CRONTAB, targetsAsList = targetList, mode = "ON")
        self.assertIn(" Comment in middle", resultList)
        self.assertIn("*/3 1 1 1 1 should pass", resultList)

    def test_strip_all(self):
        """
        Tests for removal of all whitespace-type characters from beginning and end of each job line.
        """

        input = [ "\t\tLine1\t\t", \
                  "  Line2", \
                  "Line3 (no change)",
                ]
        resultList = stripAll(input)

        self.assertIn("Line1", resultList)
        self.assertIn("Line2", resultList)
        self.assertIn("Line3 (no change)", resultList)

    def test_toggle_jobs_normal(self):
        """
        Tests for normal execution of toggleJobs method
        """

        toggleJobs("display/examplecron", "display/examplecron2", \
                    ["* * * * missing one parameter", "*/3 1 1 1 1 should pass", "#CronUI# Comment in middle"], \
                    "OFF")
        self.assertTrue(os.path.isfile("display/examplecron2"), msg="Output file not successfully generated.")

        outp = codecs.open("display/examplecron2", "r")
        outputList = stripAll(outp)

        self.assertIn("# This is a comment", outputList)
        self.assertIn("* * * * * This is correct syntax", outputList)
        self.assertIn("1 1 1 2 3 This should also be accepted", outputList)
        self.assertIn("#CronUI# Comment in middle", outputList)
        self.assertIn("#CronUI#* * * * missing one parameter", outputList)
        self.assertIn("a b c d e invalid parameters", outputList)
        self.assertIn("# Comment in middle", outputList)
        self.assertIn("#CronUI#*/3 1 1 1 1 should pass", outputList)

        outp.close()
        os.remove("display/examplecron2")

    def test_toggle_jobs_invalid_input_file(self):
        """
        Tests for invalid input file of toggleJobs method
        """

        toggleJobs("display/hogehogehoge", "display/hogehogehoge3", \
                    ["* * * * missing one parameter", "*/3 1 1 1 1 should pass", "#CronUI# Comment in middle"], \
                    "OFF")
        self.assertTrue(not os.path.isfile("display/hogehogehoge3"))

    def test_add_job_normal(self):
        """
        Tests for normal execution of addJob method
        """

        targetJob = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="Test for add job", comment="comment for add job", active=False)
        addJob("display/examplecron", "display/examplecron2", targetJob)
        self.assertTrue(os.path.isfile("display/examplecron2"), msg="Output file not successfully generated.")

        outp = codecs.open("display/examplecron2", "r")
        outputList = stripAll(outp)

        self.assertIn("# This is a comment", outputList)
        self.assertIn("* * * * * This is correct syntax", outputList)
        self.assertIn("1 1 1 2 3 This should also be accepted", outputList)
        self.assertIn("#CronUI# Comment in middle", outputList)
        self.assertIn("* * * * missing one parameter", outputList)
        self.assertIn("a b c d e invalid parameters", outputList)
        self.assertIn("# Comment in middle", outputList)
        self.assertIn("*/3 1 1 1 1 should pass", outputList)
        self.assertIn("# comment for add job", outputList)
        self.assertIn("#CronUI#* * * * * Test for add job", outputList)

        outp.close()
        os.remove("display/examplecron2")

    def test_add_job_invalid_input_file(self):
        """
        Tests for invalid input file of addJob method
        """

        addJob("display/hogehogehoge", "display/hogehogehoge3", None)
        self.assertTrue(not os.path.isfile("display/hogehogehoge3"))

    def test_add_job_invalid_no_target_job(self):
        """
        Tests for invalid no target job of addJob method
        """

        addJob("display/examplecron", "display/examplecron2", None)
        self.assertTrue(os.path.isfile("display/examplecron2"), msg="Output file not successfully generated.")

        outp = codecs.open("display/examplecron2", "r")
        outputList = stripAll(outp)

        self.assertIn("# This is a comment", outputList)
        self.assertIn("* * * * * This is correct syntax", outputList)
        self.assertIn("1 1 1 2 3 This should also be accepted", outputList)
        self.assertIn("#CronUI# Comment in middle", outputList)
        self.assertIn("* * * * missing one parameter", outputList)
        self.assertIn("a b c d e invalid parameters", outputList)
        self.assertIn("# Comment in middle", outputList)
        self.assertIn("*/3 1 1 1 1 should pass", outputList)

        outp.close()
        os.remove("display/examplecron2")

    def test_object_in_list_found(self):
        """
        Tests mainly the "equality" operator overwritten in models.Cron in a list context
        """

        cron = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="This is correct syntax", active=1)

        cron1 = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="This is correct syntax", active=0)
        cron2 = Cron(user=self.USEROBJ, minute="1", hour="2", day="3", month="4", weekday="5", command="Another cron")
        cron3 = Cron(user=self.USEROBJ, minute="*/3", hour="1", day="1", month="1", weekday="1", command="should pass")


        self.assertTrue(objectInList([cron1, cron2, cron3], cron))

    def test_object_in_list_not_found(self):
        """
        Tests mainly the "equality" operator overwritten in models.Cron in a list context
        """

        cron = Cron(user=self.USEROBJ, minute="*/6", hour="*", day="*", month="*", weekday="*", command="This is correct syntax", active=1)

        cron1 = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="This is correct syntax", active=0)
        cron2 = Cron(user=self.USEROBJ, minute="1", hour="2", day="3", month="4", weekday="5", command="Another cron")
        cron3 = Cron(user=self.USEROBJ, minute="*/3", hour="1", day="1", month="1", weekday="1", command="should pass")

        self.assertFalse(objectInList([cron1, cron2, cron3], cron))

    def test_object_in_list_empty_list(self):
        """
        Tests mainly the "equality" operator overwritten in models.Cron in a list context
        """

        cron = Cron(user=self.USEROBJ, minute="*/6", hour="*", day="*", month="*", weekday="*", command="This is correct syntax", active=1)
        self.assertFalse(objectInList([], cron))

    def test_object_in_list_null_item(self):
        """
        Tests mainly the "equality" operator overwritten in models.Cron in a list context
        """

        cron1 = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="This is correct syntax", active=0)
        cron2 = Cron(user=self.USEROBJ, minute="1", hour="2", day="3", month="4", weekday="5", command="Another cron")
        cron3 = Cron(user=self.USEROBJ, minute="*/3", hour="1", day="1", month="1", weekday="1", command="should pass")
        self.assertFalse(objectInList([cron1, cron2, cron3], None))

    def test_send_file_normal(self):
        """
        Tests normal execution of getFile method
        """

        ftp = self.SSHCLIENT.open_sftp()
        getFile(ftp, "./testtest.py", "/home/vagrant/.ssh/authorized_keys", 3)
        os.remove("testtest.py")

    def test_send_file_invalid_source(self):
        """
        Tests invalid source in getFile method
        """

        ftp = self.SSHCLIENT.open_sftp()
        with self.assertRaises(IOError):
            getFile(ftp, "hogehogehoge", "hogehogehoge", 3)
        os.remove("hogehogehoge")

    def test_send_file_invalid_target(self):
        """
        Tests invalid target in getFile method
        """

        ftp = self.SSHCLIENT.open_sftp()
        with self.assertRaises(IOError):
            getFile(ftp, "testtest.txt", "/invalidfileatroot.txt", 3)
        os.remove("testtest.txt")

    def test_parse_jobs_normal(self):
        """
        Tests normal execution of parseJobs method
        """

        cronList = ["* * * * * normal", "1 2 3 4 5 normal2", "*/3 3 4 2 1-4 normal3"]
        cron1 = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="normal")
        cron2 = Cron(user=self.USEROBJ, minute="1", hour="2", day="3", month="4", weekday="5", command="normal2")
        cron3 = Cron(user=self.USEROBJ, minute="*/3", hour="3", day="4", month="2", weekday="1-4", command="normal3")
        result = parseJobs(cronList, self.USEROBJ)

        self.assertEqual(result['errorJobs'], [] )
        self.assertEqual(result['successJobs'], [cron1, cron2, cron3]  )


    def test_parse_jobs_active_false(self):
        """
        Tests active false logic of parseJobs method
        """

        cronList = ["%s* * * * * normal" % COMMENT_PHRASE]
        cron1 = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="normal", active = False)
        result = parseJobs(cronList, self.USEROBJ)

        self.assertEqual(result['errorJobs'], [] )
        self.assertEqual(result['successJobs'], [cron1]  )
        self.assertEqual(result['successJobs'][0].active, False  )

    def test_parse_jobs_invalid_job_insufficient_parameters(self):
        """
        Tests invalid job logic of parseJobs method (insufficient parameters)
        """

        cronList = ["* * * * normal"]
        self.assertRaisesWithMessage(DisplayLogicException, "Server-side Cron parsing failed. Aborting sync on server %s." % self.SERVER, parseJobs, cronList, self.USEROBJ)

    def test_parse_jobs_invalid_job_invalid_parameters(self):
        """
        Tests invalid job logic of parseJobs method (invalid parameters)
        """

        cronList = ["A B C D E normal"]
        self.assertRaisesWithMessage(DisplayLogicException, "Server-side Cron parsing failed. Aborting sync on server %s." % self.SERVER, parseJobs, cronList, self.USEROBJ)

    def test_parse_jobs_comment(self):
        """
        Tests comment logic of parseJobs method
        """

        cronList = ["#* * * * * normal"]
        result = parseJobs(cronList, self.USEROBJ)

        self.assertEqual(result['errorJobs'], [] )
        self.assertEqual(result['successJobs'], []  )

    def test_parse_jobs_empty_line(self):
        """
        Tests empty line logic of parseJobs method
        """

        cronList = [""]
        result = parseJobs(cronList, self.USEROBJ)
        self.assertEqual(result['errorJobs'], [] )
        self.assertEqual(result['successJobs'], []  )

    def test_process_cron_request_invalid_mode(self):
        self.assertRaisesWithMessage(DisplayLogicException, "Invalid mode set (problem with internal logic)", processCronRequest, self.USEROBJ, [], "HOGEHOGE")

    def test_process_cron_request_null_user(self):
        self.assertRaisesWithMessage(DisplayLogicException, "UserObj is empty (problem with internal logic)", processCronRequest, None, [], "OFF")

    def test_process_cron_request_empty_joblist(self):
        self.assertRaisesWithMessage(DisplayLogicException, "No target jobs selected.", processCronRequest, self.USEROBJ, [], "ON")

    def test_process_cron_request_no_connect_ssh(self):
        tempUserObj = User(server = self.SERVEROBJ, username = "hogehogehoge")
        tempUserObj.save()
        cron1 = Cron(user=tempUserObj, minute="*", hour="*", day="*", month="*", weekday="*", command="This is correct syntax")
        cron1.save()
        OFF_LIST = [cron1]
        self.assertRaisesWithMessage(DisplayLogicException, \
            "Unable to connect to %s as user %s. Please check ssh key and/or security settings." % (tempUserObj.server.hostname, tempUserObj.username),\
            processCronRequest, tempUserObj, OFF_LIST, "ON")

    # To be completed...
#     def test_process_cron_request_off_normal(self):
#
#         OFF_LIST = []
#         cron1 = Cron(user=self.USEROBJ, minute="*", hour="*", day="*", month="*", weekday="*", command="This is correct syntax")
#         cron2 = Cron(user=self.USEROBJ, minute="1", hour="2", day="3", month="4", weekday="5", command="Another cron")
#         cron3 = Cron(user=self.USEROBJ, minute="*/3", hour="1", day="1", month="1", weekday="1", command="should pass")
#
#         cron1.save()
#         cron2.save()
#         cron3.save()
#
#         OFF_LIST.append(cron1)
#         OFF_LIST.append(cron2)
#         OFF_LIST.append(cron3)
#
#         processCronRequest(self.USEROBJ, OFF_LIST, "OFF")
        # To be completed...

    def test_sync_crontab_to_database_null_user_object(self):
        self.assertRaisesWithMessage(DisplayLogicException, "User object is null or not specified.", syncCrontabToDatabase, None)

    def test_sync_crontab_to_database_invalid_ssh_client(self):
        tempUserObj = User(server = self.SERVEROBJ, username = "hogehogehoge")
        tempUserObj.save()
        self.assertRaisesWithMessage(DisplayLogicException, \
            "Unable to connect to %s as user %s. Please check ssh key and/or security settings." % (tempUserObj.server.hostname, tempUserObj.username),\
            syncCrontabToDatabase, tempUserObj)

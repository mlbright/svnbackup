#!/usr/bin/python

from subprocess import call
import sys, time, os

touch = "/tmp/svn-remote-backup.touch"
source = "/svn/backups/" # Note trailing slash
target = "some@remote.host"
rsync  = "/usr/bin/rsync"
arguments = "-avz --delete -e ssh"
cmd = "%s %s %s %s &> %s" % (rsync, arguments, source, target, touch)
recipients = "martin.bright"
timer = time.time

msg = ["svn backup is complete: rsync finished successfully",
    "running time: %d seconds",
    "=====================================================" ]

def sync():

    if os.path.exists(touch):
        return

    fd = open(touch, "w")
    fd.close()

    start = timer()

    while True:
        ret = call(cmd, shell=True)
        if ret != 0:
            time.sleep(30)
        else:
            break

    end = timer()

    rsync_output = file(touch).read()
    msg.append(rsync_output)
    body = os.linesep.join(msg)
    body = body % (end - start)
    mailcmd = "echo '%s' | mail -s 'svn rsync done' %s" % (body, recipients)
    call(mailcmd, shell=True)
    os.remove(touch)

sync()

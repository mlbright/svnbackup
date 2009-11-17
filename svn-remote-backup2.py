#!/usr/bin/python

import subprocess
import sys, time, os

touch = "/tmp/svn-remote-backup.touch"
source = "/svn/backups/" # Note trailing slash
target = "some@remote-host.com/path"
rsync  = "/usr/bin/rsync"
arguments = "-avz --delete -e ssh"
cmd = "%s %s %s %s &> %s" % (rsync, arguments, source, target, touch)
recipients = "martin.bright"
timer = time.time

msg = ["svn backup is complete: rsync finished sucessfully",
    "running time: %.2f seconds",
    "=====================================================" ]

help_message = "Usage: svn-remote-backup.py REPOSITORYDIR BACKUPDIR"

class Usage(Exception):

    def __init__(self, msg=help_message):
        self.msg = msg

def removeOldBackups(directory, cutoff=21):
    day = 24 * 60 * 60 # seconds in a day
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        for file in filenames:
            f = os.path.join(dirpath, file)
            mtime = os.stat(f)[-2]
            now = int(time.time())
            if now - mtime >= cutoff * day:
                os.remove(f)

def mkdirp(newdir):
    """
    http://code.activestate.com/recipes/82465/
    - Limitations: it doesn't take the optional 'mode' argument yet
    - already exists, silently complete
    - regular file in the way, raise an exception
    - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdirp(head)
        if tail:
            try:
                os.mkdir(newdir)
            except:
                raise OSError("Cannot create directory.")

def backup(repodir, backupdir):
    youngest_rev = "svnlook youngest %s"
    svndump = "svnadmin dump -q %s > %s"
    svndumpincr = "svnadmin dump -q --incremental --revision %s:%s %s > %s"
    bzip = "bzip2 %s"
    for repo in os.listdir(repodir):
        backup = backupdir + os.sep + repo
        full = backup + os.sep + 'full'
        incr = backup + os.sep + 'incr'
        mkdirp(full)
        mkdirp(incr)
        rev_file = backup + os.sep + 'rev'
            
        rev1 = 0
        if os.path.isfile(rev_file):
            rev1 = int(file(rev_file).read())

        p = subprocess.Popen(youngest_rev % (repodir + os.sep + repo),
                            shell=True, stdout=subprocess.PIPE)
        rev2 = int(p.stdout.read().strip())

        if rev1 == 0 or datetime.date.today().isoweekday() == 5:

            # full backup
            abbrevdate = str(datetime.date.today()).replace('-', '')
            fname = full + os.sep + '-'.join([repo, abbrevdate, "R" + rev2])
            if not os.path.isfile(fname):
                subprocess.call(svndump % (repo, fname), shell=True)
                subprocess.call(bzip % (fname))

        elif rev1 != rev2:

            # incremental backup
            rev1 += 1            
            fname = incr + os.sep + '-'.join([repo, rev1, rev2])
            subprocess.call(svndumpincr % (rev1, rev2, repo, fname), shell=True)
            subprocess.call(bzip % (fname))

        else:
            continue
    
        # update the state file
        fd = open(rev_file, 'w')
        fd.write(rev2)
        fd.close()

        # delete backups older than 21 days (cutoff = 21 by default)
        removeOldBackups(backup + os.sep + 'full')
        removeOldBackups(backup + os.sep + 'incr')

def sync():

    if os.path.exists(touch):
        return

    fd = open(touch, "w")
    fd.close()

    start = timer()

    while True:
        ret = subprocess.call(cmd, shell=True)
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
    subprocess.call(mailcmd, shell=True)
    os.remove(touch)

def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        if len(argv) < 2:
            raise Usage()
        
        repodir = sys.argv[1]
        backupdir = sys.argv[2]

        baddir = "%s is not a directory"

        if not os.path.isdir(repodir):
            raise Usage(baddir % (repodir))

        if not os.path.isdir(backupdir):
            raise Usage(baddir % (repodir))

        backup(repodir, backupdir)
        sync()

    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg) 
        return 1
    
if __name__ == "__main__":
    sys.exit(main())

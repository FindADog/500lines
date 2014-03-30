"""
in written part, talk about design decisions you made (using poll system, using remote machine code vs. forking, etc)

Issues: 
- This is may be posix specific (proc ids and subprocess in windows?)
- Assume we have *some* VCS system, can I use github in my example?

"""
import argparse
import os
import re
import socket
import SocketServer
import subprocess
import sys 
import time


def bail(reason):
    raise Exception(reason)
    sys.exit(1)
    

def poll():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatcher-server",
                        help="dispatcher host:port, by default it uses localhost:8888",
                        default="localhost:8888",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    while True:
        try:
            # call the bash script that will update the repo and check for changes.
            # if there's a change, it will drop a .commit_hash file with the latest
            # commit in the current working directory
            # TODO: uncomment following line for it all to work!
            output = subprocess.check_output(["./update_repo.sh %s" % args.repo], shell=True)
            if os.path.isfile(".commit_hash"):
                #great, we have a change! let's execute the tests
                # TODO ping dispatcher to make sure its still running
                # TODO send runner server the commit_hash
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((dispatcher_host, int(dispatcher_port)))
                s.send("status")
                response = s.recv(1024)
                s.close()
                if response == "OK":
                    commit = ""
                    with open(".commit_hash", "r") as f:
                        commit = f.readline()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((dispatcher_host, int(dispatcher_port)))
                    s.send("dispatch:%s" % commit)
                    response = s.recv(1024)
                    s.close()
                    if response != "OK":
                        bail("Dispatcher could not dispatch the test: %s" % response)
                    print 'dispatched!'
                else:
                    bail("Could not communicate with dispatcher server!")
            time.sleep(90)
        except subprocess.CalledProcessError as e:
            bail("Could not update and check repository. Reason: %s" % e.output)


if __name__ == "__main__":
    poll()

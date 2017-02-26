#!/usr/bin/python
import os, traceback, auditparser, socket
from optparse import OptionParser

# Send the single request
def sendRequest(filename,host,port,ssl):
    if auditparser.isValidFile(filename):
        print "I: Valid audit file found %s" % (filename)
        try: 
            # Get headers, remove X-REPLAY-ID if found and add it again
            headers = filter( lambda x: not x.startswith("X-Replay-Id:"), auditparser.getAuditPart(filename,"REQUEST-HEADER").split("\n"))
            headers.insert(1,"X-Replay-Id: %s" % auditparser.requestHash(filename))
            body = auditparser.getAuditPart(filename,"REQUEST-BODY")

            # TODO: send additional header that contains request-id needed by the loop
            s = socket.socket(socket.AF_INET)
            s.settimeout(1)
            s.connect((str(host),int(port)))

            for header in headers:
                s.send("%s\r\n" % header.decode('string_escape'))

            if body != "":
                s.send(body)

            if options.verbose >= 2:
                print "D: SENT =============================="
                for li in headers:
                    print "   %s" % li
                for li in body.split("\n"):
                    print "   %s" % li
                print "   ==================================="


            s.settimeout(1)
            response = ""
            try:
                response = response + s.recv(2048)    
            except socket.timeout:
                pass
            finally:
                if options.verbose >= 2:
                    print "D: RECEIVED =========================="
                    for li in response.split("\n"):
                        print "   %s" % li
                    print "   ==================================="
                try:
                    s.close()
                except:
                    pass

        except Exception, e:
            print "E: unable to send %s to %s:%s" % (filename,host,port)
            traceback.print_exc()
    else:
        print "E: Invalid audit file %s" % (filename)

parser = OptionParser()
parser.add_option("--source", dest="source", help="use recursively the specified audit directory as source", default="/var/log/apache/audit/")
parser.add_option("--only-url", dest="url", help="consider only the request to the specified URL (startswith is in use)", default="")
parser.add_option("--host", dest="remotehost", help="send request to the specified host", default="localhost")
parser.add_option("--port", dest="remoteport", help="send request to the specified port", type="int", default=80)
parser.add_option("--usessl", dest="usessl", help="send request to the specified host:port (TBD)", default=False)
parser.add_option("--timeout", dest="timeout", help="send timeout", type="int", default=10)
parser.add_option("-v", "--verbose", dest="verbose", help="increase verbosity level (0..9)", action="count", default=0)
parser.add_option("--delay", dest="delay", help="delay between two requests in ms", type="int", default=100)
(options, args) = parser.parse_args()

if options.verbose > 0:
    print "I: Verbose %d" % options.verbose

if os.path.isfile(options.source):
    sendRequest(options.source,options.remotehost,options.remoteport,options.usessl)
elif os.path.isdir(options.source):
    for filename in auditparser.findFiles(options.source, '*'):
        sendRequest(filename,options.remotehost,options.remoteport,options.usessl)
else:
    print "E: File or dir does not exist: %s" % (options.source)
    
#
#...but I don't support globs at the moment 
#
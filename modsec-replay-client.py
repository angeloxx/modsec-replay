#!/usr/bin/python
#
#
# serial format support by spartantri

import os, traceback, auditparser, socket
from optparse import OptionParser

# Send the single request
def sendRequest(filename,host,port,ssl,offset):
    if auditparser.isValidFile(filename):
        print "I: Valid audit file found %s" % (filename)
        max_offset = 0
        if offset>0:
            max_offset=auditparser.isValidOffset(filename,offset)
            if max_offset == 0:
                offset=0
        for pointer in xrange(offset,max_offset):
            try: 
                # Get headers, remove X-REPLAY-ID if found and add it again
                headers = filter( lambda x: not (x.startswith("X-Replay-Id:") or x.startswith("X-Forwarded") or x.startswith("Connection: Keep-Alive")), auditparser.getAuditPart(filename,"REQUEST-HEADER",pointer).split("\n"))
                headers.insert(2,"X-Replay-Id: %s" % auditparser.requestHash(filename))
                headers.insert(3,"X-Original-Id: %s" % auditparser.getAuditPart(filename,"UNIQUE-ID",pointer))
                headers.insert(4,"Connection: Close")
                body = auditparser.getAuditPart(filename,"REQUEST-BODY",pointer)

                # TODO: send additional header that contains request-id needed by the loop
                s = socket.socket(socket.AF_INET)
                s.connect((str(host),int(port)))

                for header in headers:
                    s.send(header.decode('string_escape') + "\r\n")

                if body != "":
                    s.send(body)

                if options.verbose >= 2:
                    print "D: SENT =============================="
                    for li in headers:
                        print "   %s" % li
                    for li in body.split("\n"):
                        print "   %s" % li
                    print "   ==================================="

                s.settimeout(5)
                response = ""
                answer = True
                while answer:
                    try:
                        newdata = s.recv(2048)
                        if newdata == "":
                            answer = False
                        else:
                            response = response + newdata
                    except:
                        answer = False
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
parser.add_option("--offset", dest="offset", help="jump to offset in the logfile", type="int", default=0)
(options, args) = parser.parse_args()

if options.verbose > 0:
    print "I: Verbose %d" % options.verbose

if os.path.isfile(options.source):
    sendRequest(options.source,options.remotehost,options.remoteport,options.usessl,options.offset)
elif os.path.isdir(options.source):
    for filename in auditparser.findFiles(options.source, '*'):
        sendRequest(filename,options.remotehost,options.remoteport,options.usessl,options.offset)
else:
    print "E: File or dir does not exist: %s" % (options.source)
    
#
#...but I don't support globs at the moment 
#

#!/usr/bin/python

import socket, auditparser, os
from threading import Thread
from SocketServer import ThreadingMixIn
from optparse import OptionParser
requests = {}


class ClientThread(Thread):
    def __init__(self,ip,port,conn): 
        Thread.__init__(self) 
        self.ip = ip 
        self.port = port 
        self.conn = conn
        self._is_running = True
        if options.verbose >= 2:
            print "3: New server socket thread started for port %d" % port
        self.data = ""
                
    def run(self): 
        self.conn.settimeout(0.1)
        while self._is_running: 
            try:
                newdata = self.conn.recv(2048)
                self.data = self.data + newdata
            except socket.timeout:
                # No more data
                if options.verbose >= 1:
                    print "D: Received =========================="
                    for li in self.data.split("\n"):
                        print "   %s" % li
                    print "   ==================================="
                if self.data.split("\n")[1].startswith("X-Replay-Id"):
                    # Ready of send answer
                    sessionId = (self.data.split("\n")[1].split(":",2)[1]).strip()
                    if sessionId in requests:
                        print "I: Valid replayed session: %s" % requests[sessionId]
                        self.conn.send(auditparser.getAuditPart(requests[sessionId],"RESPONSE-HEADER"))
                        self.conn.send(auditparser.getAuditPart(requests[sessionId],"RESPONSE-BODY"))
                        if options.verbose >= 2:
                            print "D: SENT =============================="
                            for li in auditparser.getAuditPart(requests[sessionId],"RESPONSE-HEADER").split("\n"):
                                print "   %s" % li
                            for li in auditparser.getAuditPart(requests[sessionId],"RESPONSE-BODY").split("\n"):
                                print "   %s" % li
                            print "   ==================================="
                        
                self._is_running = False
                try:
                    self.conn.close()
                except:
                    pass
        if options.verbose >= 2:
            print "D: Thread closed for port %d" % port
        self._Thread__stop()

parser = OptionParser()
parser.add_option("--source", dest="source", help="use recursively the specified audit directory as source", default="/var/log/apache/audit/")
parser.add_option("--port", dest="listenport", help="receives request to the specified port", type="int", default=8080)
parser.add_option("--timeout", dest="timeout", help="send timeout", default=10)
parser.add_option("-v", "--verbose", dest="verbose", help="increase verbosity level", action="count", default=0)
(options, args) = parser.parse_args()

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0' 
TCP_PORT = options.listenport 
BUFFER_SIZE = 20  # Usually 1024, but we need quick response 

# Index audit files (even if is not valid, 'cause the client will send only a valid request)
if os.path.isfile(options.source):
    requests[auditparser.requestHash(options.source)] = options.source
elif os.path.isdir(options.source):
    for filename in auditparser.findFiles(options.source, '*'):
        requests[auditparser.requestHash(filename)] = filename
else:
    print "E: File or dir does not exist: %s" % (options.source)

print "I: %d file indexed" % (len(requests))

tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
tcpServer.bind((TCP_IP, TCP_PORT)) 
threads = [] 

while True: 
    tcpServer.listen(4) 
    print "Multithreaded Python server : Waiting for connections from TCP clients (%d still active)..." % len(threads)
    (conn, (ip,port)) = tcpServer.accept() 
    newthread = ClientThread(ip,port,conn) 
    newthread.start() 
    threads.append(newthread) 
    threads = [t.join(1000) for t in threads if t is not None and t.isAlive()]

for t in threads: 
    t.join() 
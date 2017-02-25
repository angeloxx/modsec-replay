#!/usr/bin/python

import socket, auditparser, os
from threading import Thread
from SocketServer import ThreadingMixIn
from optparse import OptionParser
requests = {}


class ClientThread(Thread):
    def __init__(self,ip,port): 
        Thread.__init__(self) 
        self.ip = ip 
        self.port = port 
        print "[+] New server socket thread started for " + ip + ":" + str(port) 
        self.data = ""
    def run(self): 
        while True: 
            newdata = conn.recv(2048)
            if len(newdata) > 0:
                self.data = self.data + newdata
            else:
                print self.data
                if self.data.split("\n")[1].startswith("X-Replay-Id"):
                    # Ready of send answer
                    sessionId = (self.data.split("\n")[1].split(":",2)[1]).strip()
                    print sessionId
                    if sessionId in requests:
                        conn.send(auditparser.getAuditPart(requests[sessionId],"RESPONSE-HEADER"))
                        conn.send(auditparser.getAuditPart(requests[sessionId],"RESPONSE-BODY"))
                break


parser = OptionParser()
parser.add_option("--source", dest="source", help="use recursively the specified audit directory as source", default="/var/log/apache/audit/")
parser.add_option("--port", dest="listenport", help="receives request to the specified port", type="int", default=8080)
parser.add_option("--timeout", dest="timeout", help="send timeout", default=10)
parser.add_option("--verbose", dest="verbose", help="verbosity level", default=1)
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
    print "Multithreaded Python server : Waiting for connections from TCP clients..." 
    (conn, (ip,port)) = tcpServer.accept() 
    newthread = ClientThread(ip,port) 
    newthread.start() 
    threads.append(newthread) 

for t in threads: 
    t.join() 
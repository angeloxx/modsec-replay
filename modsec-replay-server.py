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
        self.sessionId = ""
        if options.verbose >= 2:
            print "D: New server socket thread started for port %d" % port
        self.data = ""
                
    def run(self): 
        self.conn.settimeout(1)
        answer = True
        while answer: 
            try:
                newdata = self.conn.recv(2048)
                self.data = self.data + newdata
                if newdata == "":
                    answer = False
            except socket.timeout:
                answer = False
        if options.verbose >= 1:
            print "D: Received =========================="
            for li in self.data.split("\n"):
                print "   %s" % li
            print "   ==================================="
        for item in self.data.split("\n"):
            if item.startswith("X-Replay-Id"):
                self.sessionId = (item.split(":",2)[1]).strip()
        if self.sessionId != "":
            # Ready of send answer
            
            if self.sessionId in requests:
                print "I: Valid replayed session: %s" % requests[self.sessionId]
                headers = filter( lambda x: not (x.startswith("Connection: Keep-Alive") or x.startswith("Transfer-Encoding: chunked")), auditparser.getAuditPart(requests[self.sessionId],"RESPONSE-HEADER").split("\n"))
                for header in headers:
                    self.conn.send(header.decode('string_escape') + "\r\n")
                body = auditparser.getAuditPart(requests[self.sessionId],"RESPONSE-BODY")
                if body != "":
                    self.conn.send(body)
                if options.verbose >= 2:
                    print "D: SENT =============================="
                    for li in headers:
                        print "   %s" % li.strip()
                    if body != "":
                        for li in body.split("\n"):
                            print "   %s" % li.strip()
                    print "   ==================================="
            else:
                print "E: Invalid session, return with a kind answer to the remote client"
                self.conn.send("HTTP/1.1 200 OK\r\nServer: modsec-replay-server\r\nContent-Type: text/html; charset=iso-8859-1\r\nConnection: Close\r\n\r\nINVALID-SESSION")
        else:
            print "E: Missing session, return with a kind answer to the remote client"
            self.conn.send("HTTP/1.1 200 OK\r\nServer: modsec-replay-server\r\nContent-Type: text/html; charset=iso-8859-1\r\nConnection: Close\r\n\r\nMISSING-SESSION")
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
    (conn, (ip,port)) = tcpServer.accept() 
    newthread = ClientThread(ip,port,conn) 
    newthread.start() 
    threads.append(newthread) 
    threads = [t.join(1000) for t in threads if t is not None and t.isAlive()]

for t in threads: 
    t.join() 

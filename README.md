# Introduction

This suite was born to answer to the simple question: how can we migrate from Modsecurity CRS 2 to CRS 3 without issue? How can we test the impact of the new rules on current application? The answer could be simple, we can capture all production (or preproduction) traffic with modsec in "audit-all-mode" on production and replay that traffic (and answers) in the test environment. But this means that:

- you need a tool to send all these request to a new web server, and that tool is modsec-replay-client.py
- you need a backend that answers like the production one, but it isn't possibile if the dataset is different, so you can use an Apache configuration that reverse-proxy a fake backend server and that tool is modsec-replay-server.py

# How does it work?

The client component reads an audit file (or audit directory) and sends all the requests to a different server, using same header and content of the original request and adding a X-Replay-Id header that permit to the server component to find the correct audit file
The server component receives the request, reads the X-Replay-Id and send the associated answer from the same audit file

## Compatibility

Tested with:

- python 2.7 on Ubuntu 16.10
- modsecurity 2.9.1
- apache 2.4.25

## Usage

- Configure your Apache Web Server to log all requests so you can capture, in current running environment, all requests:


    SecAuditEngine                On     
    SecAuditLogParts              ABEFHIJKZ    
    ErrorLogFormat          "[%{cu}t] [%-m:%-l] %-a %-L %M"

- Copy the audit (and log) file to the test Apache Web Server
- Add a proxy configuration that sends requests to the modsec-replay-server all the requests and log the X-Original-Id that contains the original request identifier to easily compare the behaviour of new configuration with the same request:
	

    <VirtualHost 0.0.0.0:80>
        ProxyPass           / http://127.0.0.1:8081/   
        ProxyPassReverse    / http://127.0.0.1:8081/   
        ErrorLogFormat          "[%{cu}t] [%-m:%-l] %-a %{X-Original-Id}i %M"   
        ErrorLog                logs/error.log   
	    <Directory /apache/htdocs>   
	       Require all granted   
	       Options None   
	       AllowOverride None   
	    </Directory>   
    </VirtualHost>    

- Start the server on 8081/tcp port and feed it with the audit log directory


	./modsec-replay-server.py --source /apache/saved-logs/audit/ --port 8081

- Start the request sender:


	./modsec-replay-client.py --source /apache/saved-logs/audit/ --port 80 --host localhost

# Todo

- Probably can be useful to have a tool that compare the error log of the original request to the replayed one to check if the new modified configuration is good or not.
	- The tool is not binary safe, I need to check if ModSecurity audit file contains all info to reproduce some binary operation like file upload/download         
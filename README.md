# Introduction

This suite was born to answer to the simple question: how can we migrate from Modsecurity CRS 2 to CRS 3 without issue? How can we test the impact of the new rules on current application? The answer could be simple, we can capture all production (or preproduction) traffic with modsec in "audit-all-mode" on production and replay that traffic (and answers) in the test environment. But this means that:

- you need a tool to send all these request to a new web server, and that tool is modsec-replay-client.py
- you need a backend that answers like the production one, but it isn't possibile if the dataset is different, so you can use an Apache configuration that reverse-proxy a fake backend server and that tool is modsec-replay-server.py

## How does it work?

The client component reads an audit file (or audit directory) and sends all the requests to a different server, using same header and content of the original request and adding a X-Replay-Id header that permit to the server component to find the correct audit file
The server component receives the request, reads the X-Replay-Id and send the associated answer from the same audit file

## Compatibility

Tested with:

- python 2.7 on Ubuntu 16.10
- modsecurity 2.9.1
- apache 2.4.25

## Usage

- Start the server on 8080/tcp port and feed it with the audit log directory
     ./modsec-replay-server.py --source /apache/logs/audit/ --port 8080


## Todo
Probably can be useful to have a tool that compare the error log of the original request to the replayed one to check if the new modified configuration is good or not. TODO.
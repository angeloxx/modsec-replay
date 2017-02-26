# Introduction

This suite was born to answer to the simple question: how can we migrate from Modsecurity CRS 2 to CRS 3 without issue? How can we test the impact of the new rules on current application? The answer could be simple, we can capture all production (or preproduction) traffic with modsec in "audit-all-mode" on production and replay that traffic (and answers) in the test environment. But this means that:

- you need a tool to send all these request to a new web server, and that tool is modsec-replay-client.py
- you need a backend that answers like the production one, but it isn't possibile if the dataset is different, so you can use an Apache configuration that reverse-proxy a fake backend server and that tool is modsec-replay-server.py

# How does it work?

The client component reads an audit file (or audit directory) and sends all the requests to a different server, using same header and content of the original request and adding a X-Replay-Id header that permit to the server component to find the correct audit file
The server component receives the request, reads the X-Replay-Id and send the associated answer from the same audit file; if the request is not not valid the server reply with a basic 200 page.

## Compatibility

Tested with:

- python 2.7 on Ubuntu 16.10
- modsecurity 2.9.1
- apache 2.4.25

## Usage

- Configure your Apache Web Server to log all requests so you can capture, in current running environment, all requests:

```
    SecAuditEngine                On     
    SecAuditLogParts              ABEFHIJKZ    
    ErrorLogFormat                "[%{cu}t] [%-m:%-l] %-a %-L %M"
```

- Copy the audit (and log) file to the test Apache Web Server
- Add a proxy configuration that sends requests to the modsec-replay-server all the requests and log the X-Original-Id that contains the original request identifier to easily compare the behaviour of new configuration with the same request:
	
```
    <VirtualHost 0.0.0.0:80>
        ProxyPass           / http://127.0.0.1:8081/   
        ProxyPassReverse    / http://127.0.0.1:8081/   
        ErrorLogFormat          "[%{cu}t] [%-m:%-l] %-a %{X-Original-Id}i %M"   
        ErrorLog                logs/error.log   

        # Original log format should be (see https://www.netnea.com/cms/apache-tutorial-5_extending-access-log/)
        # LogFormat               "%h %{GEOIP_COUNTRY_CODE}e %u [%{%Y-%m-%d %H:%M:%S}t.%{usec_frac}t] \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %v %A %p %R %{BALANCER_WORKER_ROUTE}e %X \"%{cookie}n\" %{UNIQUE_ID}e %{SSL_PROTOCOL}x %{SSL_CIPHER}x %I %O %{ratio}n%% %D %{ModSecTimeIn}e %{ApplicationTime}e %{ModSecTimeOut}e %{ModSecAnomalyScoreIn}e %{ModSecAnomalyScoreOut}e" extended

        LogFormat               "%h %{GEOIP_COUNTRY_CODE}e %u [%{%Y-%m-%d %H:%M:%S}t.%{usec_frac}t] \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" %v %A %p %R %{BALANCER_WORKER_ROUTE}e %X \"%{cookie}n\" %{X-Original-Id}i %{SSL_PROTOCOL}x %{SSL_CIPHER}x %I %O %{ratio}n%% %D %{ModSecTimeIn}e %{ApplicationTime}e %{ModSecTimeOut}e %{ModSecAnomalyScoreIn}e %{ModSecAnomalyScoreOut}e" extended2
        CustomLog               logs/access-replay.log extended2

	    <Directory /apache/htdocs>   
	       Require all granted   
	       Options None   
	       AllowOverride None   
	    </Directory>   
    </VirtualHost>    
```

- Start the server on 8081/tcp port and feed it with the audit log directory

```
	./modsec-replay-server.py --source /apache/saved-logs/audit/ --port 8081
```

- Start the request sender:

```
	./modsec-replay-client.py --source /apache/saved-logs/audit/ --port 80 --host localhost
```

- Check the difference between two requests, eg:

```
     /apache/logs/access.log:127.0.0.1 - - [2017-02-26 18:41:49.904468] "GET /S3oEgTCt.se HTTP/1.1" 200 15 "-" "Mozilla/5.00 (Nikto/2.1.5) (Evasions:None) (Test:map_codes)" localhost 127.0.0.1 81 proxy-server - + "-" - - - 146 221 -% 1035295 13314 1008631 1444 5 0
     /apache/logs/access-replay.log:127.0.0.1 - - [2017-02-26 18:42:05.730041] "GET /S3oEgTCt.se HTTP/1.1" 200 15 "-" "Mozilla/5.00 (Nikto/2.1.5) (Evasions:None) (Test:map_codes)" localhost 127.0.0.1 81 proxy-server - - "-" WLMTXX8AAQEAACgGnrcAAAAL - - 229 185 -% 1021614 2717 1013479 883 7 0
```

The original request is sent to a web server with paranoia level 1 and the replayed request is sent to web server with paranoia level 5

# Todo

- Probably can be useful to have a tool that compare the error log of the original request to the replayed one to check if the new modified configuration is good or not.
- The tool is not binary safe, I need to check if ModSecurity audit file contains all info to reproduce some binary operation like file upload/download
- Replace the socket server with a real http server in modsec-replay-server
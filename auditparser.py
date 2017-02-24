#!/usr/bin/python 
#
#
# This script parses the audit log
#

import os

"""
returns a structure that contains requestid, request header, request body, response header and response body
"""
def isValidFile(filename):
    validCount = 0
    with open(filename, "r") as f:
        for line in f.readlines():
            li = line.strip()
            if li.startswith("--") and li.endswith("-A--"):
                validCount = validCount+1
            elif li.startswith("--") and li.endswith("-B--"):
                validCount = validCount+1
            elif li.startswith("--") and li.endswith("-F--"):
                validCount = validCount+1
            elif li.startswith("--") and li.endswith("-E--"):
                validCount = validCount+1
    return validCount >= 4

def getAuditPart(filename,part):
    captureFlag = False 
    lineNumber = 0
    outBuffer = ""
    if os.path.isfile(filename) and isValidFile(filename):
        with open(filename, "r") as f:
            for line in f.readlines():
                li = line.strip()
                if li.startswith("--") and li.endswith("-A--"):
                    if part == "LOG":
                        captureFlag = True
                    else:
                        captureFlag = False

                elif li.startswith("--") and li.endswith("-B--"):
                    if part == "REQUEST":
                        captureFlag = True
                    else:
                        captureFlag = False

                elif li.startswith("--") and li.endswith("-F--"):
                    if part == "RESPONSE-HEADER":
                        captureFlag = True
                    else:
                        captureFlag = False

                elif li.startswith("--") and li.endswith("-E--"):
                    if part == "RESPONSE-BODY":
                        captureFlag = True
                    else:
                        captureFlag = False
        
                if captureFlag:
                    if lineNumber > 0:
                        outBuffer = outBuffer + line
                    lineNumber = lineNumber + 1
        return outBuffer
    return None
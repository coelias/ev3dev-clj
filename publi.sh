#!/bin/bash
socat TCP-LISTEN:12345,reuseaddr,fork EXEC:"pypy -u devices.py",pty,stderr

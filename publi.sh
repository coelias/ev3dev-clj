#!/bin/bash
socat TCP-LISTEN:12345,reuseaddr,fork EXEC:"python3 -u devices.py",pty,stderr

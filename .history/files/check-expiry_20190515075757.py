'''This file checks for certificate expiry (with specified grace period) and 
returns a value to indiate whether the certificate is still within the renewal
grace period cutoff. 1 = within renewal grace, 0 = should be renewed'''

import argparse
import os
import subprocess
import sys
from datetime import datetime, timedelta

import pytz


def check_cert(domain, cutoff):

    cert_path = f'/etc/letsencrypt/live/{domain}/fullchain.pem'
    if not os.path.exists(cert_path):
        # No certificate found
        return 0

    output = subprocess.check_output(f'openssl x509 -enddate -noout -in {cert_path}', shell=True)
    output = output.decode().strip().rsplit(' ', 1)[0].split('notAfter=', 1)[1]  # Decode to str, remove the '\n', 'GMT' and 'notAfter='
    
    expiry = datetime.strptime(output, '%b %d %H:%M:%S %Y').astimezone(pytz.timezone('GMT'))  # Assume output is GMT

    if expiry <= datetime.now(pytz.utc)+timedelta(days=cutoff):
        return 0
    else:
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check X509 encoded SSL certificates for expiry date, returns 1 for good, 0 for needs renewal.')
    parser.add_argument('domain', type=str, help='Main domain name (assumes certificate is at /etc/letsencrypt/live/[domain]/fullchain.pem)')
    parser.add_argument('-c', '--cutoff', type=int, default=14, help='Grace period cutoff (in days)')
    args = parser.parse_args()

    print(check_cert(domain=args.domain, cutoff=args.cutoff))
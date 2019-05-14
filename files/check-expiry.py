'''This file checks for certificate expiry (with specified grace period) and 
returns a value to indiate whether the certificate is still within the renewal
grace period. 1 = within renewal grace, 0 = should be renewed'''

import os
import subprocess
import sys
from datetime import datetime, timedelta

import pytz


def check_cert(domain, cert_file='fullchain.pem', grace=14):

    cert_path = f'/etc/letsencrypt/live/{domain}/{cert_file}'
    if not os.path.exists(cert_path):
        # No certificate found
        return 0

    output = subprocess.check_output(f"openssl x509 -enddate -noout -in {cert_path} | sed -e 's#notAfter=##'", shell=True)
    output = output.decode().replace('\n', '').strip()  # Decode to str, trim and remove \n
    
    expiry = datetime.strptime(output, '%b %d %H:%M:%S %Y %Z').astimezone(pytz.timezone('GMT'))  # Assume output is GMT

    if expiry <= datetime.now(pytz.utc)+timedelta(days=grace):
        return 0
    else:
        return 1


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print(check_cert(sys.argv[1]))
    else:
        print('Usage: python check-expiry.py [DOMAIN]')

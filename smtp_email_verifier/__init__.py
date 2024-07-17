#!/usr/bin/env python

# python -u verify.py /tmp/emails.txt | tee /tmp/vemails.txt

# from verify_email import verify_email

import os
import sys
import argparse
import dns.resolver
import smtplib
import socket

__version__ = '0.1.0'


class EmailVerifierError(Exception):
    pass

class EmailVerifier:
    def __init__(self, helo: str, mailfrom: str, verbose=False):
        self.helo = helo
        self.mailfrom = mailfrom
        self.verbose = verbose

    def get_best_mx(self, mxlist: list[dns.resolver.Answer]):
        mx_sorted = sorted([(int(x.preference), str(x.exchange)) for x in mxlist])
        return mx_sorted[0][1]

    def verify_email(self, email):

        if self.verbose:
            print(f"# Verifying {email}", flush=True)

        try:
            addressToVerify = email
            domain = addressToVerify.split('@')[1]            
            records = dns.resolver.resolve(domain, 'MX')

            mxRecord = self.get_best_mx(records)

            # test resolve
            mx_ip = dns.resolver.resolve(mxRecord, 'A')[0].address

            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(self.verbose)
            server.connect(mxRecord)
            server.helo(self.helo)
            server.mail(self.mailfrom)
            code, message = server.rcpt(email)
            server.quit()
            if self.verbose:
                print()
            if code == 250:
                return True            
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            raise EmailVerifierError(f"DNS error for {domain}")
        except Exception as e:
            raise EmailVerifierError(f"Other Error: {e}")

        raise EmailVerifierError(f"RCPT TO error: {code} {message}")

def get_args():

    def_from = 'noreply@example.com'
    def_helo = socket.getfqdn()

    parser = argparse.ArgumentParser()
    parser.add_argument('email', nargs='?', help='Email address to verify')
    parser.add_argument('--file', '-f', help='email list')
    parser.add_argument('--from', dest='_from', default=def_from, help='email for MAIL FROM')
    parser.add_argument('--helo', default=def_helo, help='HELO host')
    parser.add_argument('--verbose', '-v', default=False, action='store_true', help='verbose')

    args = parser.parse_args()

    if not args.email and not args.file:
        print("No email address or file provided", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    return args


def main():

    args = get_args()

    ev = EmailVerifier(helo=args.helo, mailfrom=args._from, verbose=args.verbose)


    if args.email:
        try:
            r = ev.verify_email(args.email)
            print(args.email, flush=True)
        except EmailVerifierError as e:
            print(f"{args.email}: {e}", file=sys.stderr)
    else:
        with open(args.file, 'r') as f:
            for line in f:
                email = line.strip()
                if not email:
                    continue
                try:
                    r = ev.verify_email(email)
                    print(email, flush=True)
                except EmailVerifierError as e:
                    print(f"{email}: {e}", file=sys.stderr)


                    
if __name__ == '__main__':
    main()
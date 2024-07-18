#!/usr/bin/env python

import os
import sys
import argparse
import dns.resolver
import smtplib
import socket
import time
import datetime

__version__ = '0.1.5'

verbose = False

def vprint(*args, **kwargs):
    if verbose:
        if args:
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            print("#", timestamp, *args, **kwargs, flush=True)
        else:
            print(**kwargs, flush=True)

class EmailVerifierError(Exception):
    def __init__(self, message, smtp_code=None):
        self.message = message
        self.smtp_code = smtp_code
        super().__init__(message)


class EmailVerifier:
    def __init__(self, helo: str, mailfrom: str, verbose=False, timeout=10, dns_only=False):
        self.helo = helo
        self.mailfrom = mailfrom
        self.verbose = verbose
        self.timeout = timeout
        self.dns_only = dns_only

    def get_best_mx(self, mxlist: list[dns.resolver.Answer]):
        mx_sorted = sorted([(int(x.preference), str(x.exchange)) for x in mxlist])
        return mx_sorted[0][1]

    def verify_email(self, email):

        vprint(f"Verifying {email}")

        try:
            addressToVerify = email
            domain = addressToVerify.split('@')[1]            
            records = dns.resolver.resolve(domain, 'MX')

            mxRecord = self.get_best_mx(records)

            # test resolve
            mx_ip = dns.resolver.resolve(mxRecord, 'A')[0].address

            if self.dns_only:
                return True

            server = smtplib.SMTP(timeout=self.timeout)
            server.set_debuglevel(self.verbose)
            server.connect(mxRecord)
            server.helo(self.helo)
            server.mail(self.mailfrom)
            code, message = server.rcpt(email)
            server.quit()
            vprint()
            if code == 250:
                return True            
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            raise EmailVerifierError(f"DNS error for {domain}")
        except Exception as e:
            raise EmailVerifierError(f"Other Error: {e}")

        raise EmailVerifierError(f"RCPT TO error: {code} {message}", smtp_code=code)

def get_args():

    global verbose

    def_from = 'noreply@example.com'
    def_helo = socket.getfqdn()

    parser = argparse.ArgumentParser()
    g = parser.add_argument_group('Main Options')
    g.add_argument('email', nargs='?', help='Email address to verify')
    g.add_argument('--file', '-f', help='email list')

    g = parser.add_argument_group('Verification options')
    g.add_argument('--dns', default=False, action='store_true', help='Simplified DNS-only domain check, without connecting to mailserver and checking mailbox')
    g.add_argument('--from', dest='_from', metavar='EMAIL', default=def_from, help='email for MAIL FROM')
    g.add_argument('--helo', default=def_helo, help='HELO host')
    g.add_argument('--timeout', metavar='N', type=int, default=10, help='Timeout for SMTP operations')

    g = parser.add_argument_group('Options for retries (Greylisting)')
    g.add_argument('--retry', metavar='N', type=int, default=60, help='Delay (in seconds) if get temporary 4xx error (greylisting) for each retry')
    g.add_argument('--max-retry', metavar='N', type=int, default=0, help='Do not retry for more then N seconds (use 180+, maybe 600).')

    g = parser.add_argument_group('Verbosity')
    g.add_argument('--verbose', '-v', default=False, action='store_true', help='Verbosity for verifier logic')
    g.add_argument('--smtp-verbose', '-s', default=False, action='store_true', help='Verbosity for SMTP conversation')

    args = parser.parse_args()

    if not args.email and not args.file:
        print("No email address or file provided", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    verbose = args.verbose

    return args


def verify_list(ev: EmailVerifier, maillist: list, can_retry=False): 

    retry_list = list()

    for email in maillist:
        try:
            r = ev.verify_email(email)
            print(email, flush=True)
        except EmailVerifierError as e:

            if can_retry and e.smtp_code is not None and e.smtp_code >= 400 and e.smtp_code < 500:
                retry_list.append(email)
                vprint(f"{email}: {e} (will retry)")
            else:
                print(f"{email}: {e}", file=sys.stderr)

    return retry_list


def main():

    args = get_args()
    start = time.time()

    if args.max_retry > 0:
        last_retry = start + args.max_retry
    else:
        last_retry = 0

    maillist = list()

    ev = EmailVerifier(helo=args.helo, mailfrom=args._from, timeout=args.timeout, verbose=args.smtp_verbose, dns_only=args.dns)

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
                maillist.append(email)


        while maillist:            
            # check if next retry time will be too late
            next_retry = time.time() + args.retry
            can_retry = next_retry < last_retry
            retry_list = verify_list(ev, maillist, can_retry=can_retry)
            vprint(f"RETRY: {len(retry_list)} emails")
            maillist = retry_list
            if maillist:
                vprint("Sleep", args.retry, "seconds")
                time.sleep(args.retry)

    


if __name__ == '__main__':
    main()
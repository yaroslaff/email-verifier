# Email Verifier (python)
Email Verifier makes correct SMTP conversation to verify email address or list of addresses

This tool could be slow - it's not working parallel.

## Why yet another mail list verifier?
Because many other verifiers are working incorrectly, e.g. They use incorrect `HELO`/`EHLO` host, do not issue `MAIL FROM` command before `RCPT TO` and on some mailserver this makes incorrect result (e.g. RCPT TO fails because of missed MAIL FROM, but not because something wrong with recipient)

## Usage
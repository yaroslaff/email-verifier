# SMTP Email Verifier (python)
SMTP Email Verifier makes correct SMTP conversation to verify email address or list of addresses

This tool could be slow - it's not working parallel.

verifier prints successfully verified email addresses to stdout, and failed addresses (and reason) to stderr.



## Why yet another mail list verifier?
Because many other verifiers are working incorrectly, e.g. They use incorrect `HELO` host, do not issue `MAIL FROM` command before `RCPT TO` and on some mailserver this makes incorrect result (e.g. RCPT TO fails because of missed MAIL FROM, but not because something wrong with recipient).

SMTP Email verifier:
1. Connects to main MX for domain (with lowest MX priority)
2. Makes correct (configurable) SMTP conversation with `HELO` / `MAIL FROM` / `RCPT TO`
3. For each failed email prints (easy to parse with `cut -f 1 -d:` )
4. Supports Greylisting! If verification returns a temporary error, it will retry every `--retry` seconds for up to `--max-retry` seconds.

## Install
~~~
pipx install smtp-email-verifier
~~~

## Usage
### Verify one email address
~~~
$ email_verifier yaroslaff@gmail.com
yaroslaff@gmail.com

$ email_verifier yaroslaff-nosuchemail@gmail.com > /dev/null 
yaroslaff-nosuchemail@gmail.com: RCPT TO error: 550 b"5.1.1 The email account that you tried to reach does not exist. Please try\n5.1.1 double-checking the recipient's email address for typos or\n5.1.1 unnecessary spaces. For more information, go to\n5.1.1  https://support.google.com/mail/?p=NoSuchUser 41be03b00d2f7-78e43192d3esi9685918a12.435 - gsmtp"
~~~

Optionally provide options `--helo HOSTNAME` and `--from ADDRESS`.


### Verify list
~~~
# See verification status for each email address
$ email_verifier -f /tmp/test.txt 
aaa@example.com: DNS error for example.com
bbb@example.com: DNS error for example.com
yaroslaff@gmail.com

# Get only verified emails
$ email_verifier -f /tmp/test.txt 2> /dev/null 
yaroslaff@gmail.com

# Or with redirections and custom HELO and MAIL FROM address
$ email_verifier -f /tmp/test.txt --helo localhost --from noreply@example.com > /tmp/test-ok.txt 2> /tmp/test-fail.txt
# now get all failed addresses:
$cut -f 1 -d: < /tmp/test-fail.txt
~~~

### Verbose
If you want to see how exactly verification happens for email address, use `-v` / `--verbose`:

~~~
$ email_verifier -v yaroslaff@gmail.com --helo localhost --from noreply@example.com
# Verifying yaroslaff@gmail.com
connect: to ('gmail-smtp-in.l.google.com.', 25) None
reply: b'220 mx.google.com ESMTP 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp\r\n'
reply: retcode (220); Msg: b'mx.google.com ESMTP 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp'
connect: b'mx.google.com ESMTP 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp'
send: 'helo localhost\r\n'
reply: b'250 mx.google.com at your service\r\n'
reply: retcode (250); Msg: b'mx.google.com at your service'
send: 'mail FROM:<noreply@example.com>\r\n'
reply: b'250 2.1.0 OK 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp\r\n'
reply: retcode (250); Msg: b'2.1.0 OK 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp'
send: 'rcpt TO:<yaroslaff@gmail.com>\r\n'
reply: b'250 2.1.5 OK 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp\r\n'
reply: retcode (250); Msg: b'2.1.5 OK 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp'
send: 'quit\r\n'
reply: b'221 2.0.0 closing connection 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp\r\n'
reply: retcode (221); Msg: b'2.0.0 closing connection 38308e7fff4ca-2eee192b083si25595201fa.355 - gsmtp'

yaroslaff@gmail.com
~~~

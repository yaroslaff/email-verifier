# Grey verifier: Smart SMTP Email Verifier (python)
Grey Verifier makes correct SMTP conversation to verify email address or list of addresses and properly handles 4xx SMTP errors (such as greylisting).

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
pipx install grey-verifier
~~~

## Usage
### Verify one email address
~~~
$ grey_verifier yaroslaff@gmail.com
yaroslaff@gmail.com

$ grey_verifier yaroslaff-NoSuchEmail@gmail.com
yaroslaff-NoSuchEmail@gmail.com: RCPT TO error: 550 b"5.1.1 The email account that you tried to reach does not exist. Please try\n5.1.1 double-checking the recipient's email address for typos or\n5.1.1 unnecessary spaces. For more information, go to\n5.1.1  https://support.google.com/mail/?p=NoSuchUser 38308e7fff4ca-2ef05d163c2si289891fa.270 - gsmtp"
~~~

Optionally provide options `--helo HOSTNAME` and `--from ADDRESS`. Some mail servers will give false negative results if will not like HELO or FROM address.


### Verify list
~~~
# See verification status for each email address
$ grey_verifier -f /tmp/test.txt 
aaa@example.com: DNS error for example.com
bbb@example.com: DNS error for example.com
yaroslaff@gmail.com

# Get only verified emails
$ grey_verifier -f /tmp/test.txt 2> /dev/null 
yaroslaff@gmail.com

# Or with redirections and custom HELO and MAIL FROM address
$ grey_verifier -f /tmp/test.txt --helo localhost --from noreply@example.com > /tmp/test-ok.txt 2> /tmp/test-fail.txt
# now get all failed addresses:
$cut -f 1 -d: < /tmp/test-fail.txt
~~~


### Greylisting
To pass greylisting protection, use `--max-retry N` option to set retry limit (in seconds). If `--max-retry` is set, verifier will retry every `--retry N` seconds (default: 60), for up to `--max-retry` limit.

> **Note**: Default value for `--max-retry` is 0 (retries disabled). Set it to something like `--max-retry 600` (or even more) to properly handle greylisting.

### Verbose
If you want to see how exactly verification happens for email address, use `-v` / `--verbose` to see internal debug messages and `-s` / `--smtp-verbose` to see SMTP conversation. Example:

~~~
$ email_verifier -sv yaroslaff@gmail.com
# Verifying yaroslaff@gmail.com
connect: to ('gmail-smtp-in.l.google.com.', 25) None
reply: b'220 mx.google.com ESMTP 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp\r\n'
reply: retcode (220); Msg: b'mx.google.com ESMTP 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp'
connect: b'mx.google.com ESMTP 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp'
send: 'helo mir.localdomain\r\n'
reply: b'250 mx.google.com at your service\r\n'
reply: retcode (250); Msg: b'mx.google.com at your service'
send: 'mail FROM:<noreply@example.com>\r\n'
reply: b'250 2.1.0 OK 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp\r\n'
reply: retcode (250); Msg: b'2.1.0 OK 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp'
send: 'rcpt TO:<yaroslaff@gmail.com>\r\n'
reply: b'250 2.1.5 OK 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp\r\n'
reply: retcode (250); Msg: b'2.1.5 OK 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp'
send: 'quit\r\n'
reply: b'221 2.0.0 closing connection 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp\r\n'
reply: retcode (221); Msg: b'2.0.0 closing connection 2adb3069b0e04-52ed252cfc0si2901698e87.159 - gsmtp'

yaroslaff@gmail.com
~~~


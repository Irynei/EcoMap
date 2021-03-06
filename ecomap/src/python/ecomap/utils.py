# -*- coding: utf-8 -*-
"""Module contains usefull functions."""
import logging
import logging.config
import os
import random
import string
import smtplib

from urlparse import urlparse
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

CONF_PATH = os.path.join(os.environ['CONFROOT'], 'log.conf')


def random_password(length):
    """Generates randow string. Contains lower- and uppercase letters.
       :params: length - length of string
       :return: string"""
    return ''.join(random.choice(string.ascii_letters) for i in range(length))


def get_logger():
    """function for configuring default logger object
    from standard logging library
        Returns:
            configured logger object.
        Usage:
            import this method to your
            module and call it.
            then define a new logger object as usual
    """
    return logging.config.fileConfig(CONF_PATH)


class Singleton(type):
    """
    using a Singleton pattern to work with only one possible instance of Pool
    """
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


def parse_url(url_to_parse, get_arg=None, get_path=None):
    """Function helps to parse url and splits parts of urls.
    :param url_to_parse: input url
    :param get_arg: [optional]
    :param get_path: [optional]
    :return: parsed url contains path
    """
    url = urlparse(url_to_parse)
    if get_arg:
        return url.path.split('/')[-1]
    if get_path:
        return '/'.join(url.path.split('/')[:-1])
    return '?'.join((url.path, url.query)) if url.query else url.path


def generate_email(email_type, from_email, to_email, args,
                   custom_template=None, template_str=None, header=None):
    """Sends email."""
    msg = MIMEMultipart('alternative')
    complete_email = os.path.join(os.environ['CONFROOT'],
                                  'email_template.html')
    if custom_template:
        email_body = custom_template
        args = ''
    else:
        email_body = os.path.join(os.environ['CONFROOT'],
                                  '%s.html' % email_type)
    html = None
    html_body = None
    with open(complete_email, 'rb') as template:
        html = template.read().decode('utf-8')

    with open(email_body, 'rb') as template:
        if args:
            html_body = template.read().decode('utf-8') % args
        else:
            html_body = template.read().decode('utf-8')

    if template_str:
        html_body = template_str.decode('utf-8')

    html_formatted = html % html_body
    if header:
        msg['Subject'] = Header('%s' % header, 'utf-8')
    else:
        msg['Subject'] = Header('%s' % email_type, 'utf-8')
    msg['From'] = from_email
    msg['To'] = to_email
    htmltext = MIMEText(html_formatted, 'html', 'utf-8')
    msg.attach(htmltext)

    return msg


def send_email(login, app_key, from_email, to_email, email):
    """Sends email.
       :params: login - email server login
                app_key - email server key
                sender - email of sender
                receiver - email of receiver
                email - body of email
    """
    server = smtplib.SMTP_SSL('smtp.gmail.com')
    server.login(login, app_key)
    server.sendmail(from_email, to_email, email.as_string())
    server.quit()

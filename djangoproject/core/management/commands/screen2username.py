import random
from django.contrib.auth.models import User
from django.core.management.base import NoArgsCommand
from optparse import make_option
from django.template.base import Template
from django.template.context import Context
from django.template.defaultfilters import slugify
from django.conf import settings
from core.services import user_services, mail_services


BODY_USER_WITH_PASSWORD = """
<p>Hello {{screenName}},</p>
<p>We're changing how users are identified on FreedomSponsors.
This affects all users, so please keep reading.</p>
<p>Instead of using <strong>Screen Name</strong>, FreedomSponsors will refer to users by <strong>username</strong>.</p>
<p>So, for example, <em>"&lt;screen_name&gt; sponsored issue X"</em> will become <em>"&lt;username&gt; sponsored issue X".</em>
This will affect everything on the site: pages, emails and URLs.</p>
<p>Unlike Screen Names, usernames must be unique and may not contain spaces or special characters.</p>
<p>Your current Screen Name is <strong>{{screenName}}</strong> and your current username is <strong>{{new_username}}</strong>.</p>
<p>Because of this policy change, we're allowing all users to change their username, once, until the end of the year.</p>
<p>If you wish to change your username, just log on to your account on http://freedomsponsors.org,
click your username on the top right corner and select the "change username" option.
Otherwise, no action is needed.</p>
<p>If you have any questions/feedback, feel free to reply this email or drop a comment on the
<a href="https://github.com/freedomsponsors/www.freedomsponsors.org/issues/209">corresponding issue</a> on Github.</p>
<p></p>
<p>Thanks!<br>
The FreedomSponsors team</p>
"""

BODY_USER_WITH_SAME_SCREENNAME = """
<p>Hello {{screenName}},</p>
<p>We're changing how users are identified on FreedomSponsors.
This affects all users, so please keep reading.</p>
<p>Instead of using <strong>Screen Name</strong>, FreedomSponsors will refer to users by <strong>username</strong>.</p>
<p>So, for example, <em>"&lt;screen_name&gt; sponsored issue X"</em> will become <em>"&lt;username&gt; sponsored issue X".</em>
This will affect everything on the site: pages, emails and URLs.</p>
<p>Unlike Screen Names, usernames must be unique and may not contain spaces or special characters.</p>
<p>Your current Screen Name is <strong>{{screenName}}</strong>.
This is a valid username so we automatically set your username to that.</p>
<p>Anyway, because of this policy change, we're allowing all users to change their username, once, until the end of the year.</p>
<p>If you wish to change your username, just log on to your account on http://freedomsponsors.org,
click your username on the top right corner and select the "change username" option.
Otherwise, no action is needed.</p>
<p>If you have any questions/feedback, feel free to reply this email or drop a comment on the
<a href="https://github.com/freedomsponsors/www.freedomsponsors.org/issues/209">corresponding issue</a> on Github.</p>
<p></p>
<p>Thanks!<br>
The FreedomSponsors team</p>
"""

BODY_USER_WITH_INVALID_SCREENNAME = """
<p>Hello {{screenName}},</p>
<p>We're changing how users are identified on FreedomSponsors.
This affects all users, so please keep reading.</p>
<p>Instead of using <strong>Screen Name</strong>, FreedomSponsors will refer to users by <strong>username</strong>.</p>
<p>So, for example, <em>"&lt;screen_name&gt; sponsored issue X"</em> will become <em>"&lt;username&gt; sponsored issue X".</em>
This will affect everything on the site: pages, emails and URLs.</p>
<p>Unlike Screen Names, usernames must be unique and may not contain spaces or special characters.</p>
<p>Your current Screen Name is <strong>{{screenName}}</strong>.
We were not able to automatically generate a valid username from your Screen Name (most probably because of special characters).
So we automatically generated a temporary random username for you, which is <strong>{{new_username}}</strong>.</p>
<p>But don't worry, you can change your username (once!), and you have until the end of the year to do it.</p>
<p>To choose a new username, just log on to your account on http://freedomsponsors.org,
click your username on the top right corner and select the "change username" option.</p>
<p>If you have any questions/feedback, feel free to reply this email or drop a comment on the
<a href="https://github.com/freedomsponsors/www.freedomsponsors.org/issues/209">corresponding issue</a> on Github.</p>
<p></p>
<p>Thanks!<br>
The FreedomSponsors team</p>
"""

BODY_USER_DEFAULT = """
<p>Hello {{screenName}},</p>
<p>We're changing how users are identified on FreedomSponsors.
This affects all users, so please keep reading.</p>
<p>Instead of using <strong>Screen Name</strong>, FreedomSponsors will refer to users by <strong>username</strong>.</p>
<p>So, for example, <em>"&lt;screen_name&gt; sponsored issue X"</em> will become <em>"&lt;username&gt; sponsored issue X".</em>
This will affect everything on the site: pages, emails and URLs.</p>
<p>Unlike Screen Names, usernames must be unique and may not contain spaces or special characters.</p>
<p>Your current Screen Name is <strong>{{screenName}}</strong> and your automatically-generated username is
<strong>{{new_username}}</strong>.</p>
<p>Anyway, because of this policy change, we're allowing all users to change their username, once, until the end of the year.</p>
<p>If you wish to change your username, just log on to your account on http://freedomsponsors.org,
click your username on the top right corner and select the "change username" option.
Otherwise, no action is needed.</p>
<p>If you have any questions/feedback, feel free to reply this email or drop a comment on the
<a href="https://github.com/freedomsponsors/www.freedomsponsors.org/issues/209">corresponding issue</a> on Github.</p>
<p></p>
<p>Thanks!<br>
The FreedomSponsors team</p>
"""


def _has_password(user):
    return user.password and len(user.password) > 1 and user.has_usable_password()


def _template_render_and_send(subject, source, user, screenName, new_username):
    t = Template(source)
    body = t.render(Context({
        'user': user,
        'screenName': screenName,
        'new_username': new_username,
    }))
    mail_services.plain_send_mail(user.email, subject, body, settings.ADMAIL_FROM_EMAIL)
    # mail_services.plain_send_mail('tonylampada@gmail.com', subject, body, settings.ADMAIL_FROM_EMAIL)


def _user_with_password(user, screenName, new_username):
    subject = 'Important information about your account on FreedomSponsors'
    _template_render_and_send(subject, BODY_USER_WITH_PASSWORD, user, screenName, new_username)
    print('PASSWORD,%s,%s,%s,%s,%s,%s' % (user.id, user.email, screenName, slugify(screenName), user.username, new_username))


def _user_with_same_screenName_already(user, screenName, new_username):
    _set_username(user, new_username)
    subject = 'Important information about your account on FreedomSponsors'
    _template_render_and_send(subject, BODY_USER_WITH_SAME_SCREENNAME, user, screenName, new_username)
    print('SAME_SCREENNAME,%s,%s,%s,%s,%s,%s' % (user.id, user.email, screenName, slugify(screenName), user.username, new_username))


def _user_with_same_username_already(user, screenName, new_username):
    print('SAME_USERNAME,%s,%s,%s,%s,%s,%s' % (user.id, user.email, screenName, slugify(screenName), user.username, new_username))


def _user_with_invalid_screenName(user, screenName, new_username):
    _set_username(user, new_username)
    subject = 'Important information about your account on FreedomSponsors (you need to pick a username!)'
    _template_render_and_send(subject, BODY_USER_WITH_INVALID_SCREENNAME, user, screenName, new_username)
    print('INVALID,%s,%s,%s,%s,%s,%s' % (user.id, user.email, screenName, slugify(screenName), user.username, new_username))


def _user_default(user, screenName, new_username):
    _set_username(user, new_username)
    subject = 'Important information about your account on FreedomSponsors'
    _template_render_and_send(subject, BODY_USER_DEFAULT, user, screenName, new_username)
    print('DEFAULT,%s,%s,%s,%s,%s,%s' % (user.id, user.email, screenName, slugify(screenName), user.username, new_username))


def _make_available(username):
    if user_services.is_username_available(username):
        return username
    else:
        c = 2
        available = False
        while not available:
            _username = '%s%s' % (username, c)
            available = user_services.is_username_available(_username)
            c += 1
        return _username


def _set_username(user, username):
    user = User.objects.get(pk=user.id)
    user.username = username
    user.save()


def _random_username():
    return 'user%s' % random.randint(0, 1E6)


class Command(NoArgsCommand):

    help = "Copy screenName to username - one time deal"

    option_list = NoArgsCommand.option_list + (
        make_option('--verbose', action='store_true'),
    )

    def handle_noargs(self, **options):
        print('TYPE,id,email,screenName,slugify(screenName),old_username,new_username')
        # for user in User.objects.all().order_by('id'):
        for user in User.objects.filter(id__in=(1, 2, 7, 345, 625)).order_by('id'):
            userinfo = user.getUserInfo()
            if userinfo:
                has_password = _has_password(user)
                screenName = userinfo.screenName
                new_username = slugify(screenName)
                new_is_valid = user_services.is_valid_username(new_username)
                if has_password:
                    _user_with_password(user, screenName, new_username)
                elif new_is_valid:
                    if new_username == user.username:
                        _user_with_same_username_already(user, screenName, new_username)
                    elif screenName == new_username:
                        _user_with_same_screenName_already(user, screenName, new_username)
                    else:
                        new_username = _make_available(new_username)
                        _user_default(user, screenName, new_username)
                else:
                    new_username = _random_username()
                    new_username = _make_available(new_username)
                    _user_with_invalid_screenName(user, screenName, new_username)

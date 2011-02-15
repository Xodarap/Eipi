#!/usr/bin/env python

from __future__ import generators

"""POP3DND - provides drag'n'drop training ability for POP3 clients.

This application is a twisted cross between a POP3 proxy and an IMAP
server.  It sits between your mail client and your POP3 server (like any
other POP3 proxy).  While messages classified as ham are simply passed
through the proxy, messages that are classified as spam or unsure are
intercepted and passed to the IMAP server.  The IMAP server offers three
folders - one where messages classified as spam end up, one for messages
it is unsure about, and one for training ham.

In other words, to use this application, setup your mail client to connect
to localhost, rather than directly to your POP3 server.  Additionally, add
a new IMAP account, also connecting to localhost.  Setup the application
via the web interface, and you are ready to go.  Good messages will appear
as per normal, but you will also have two new incoming folders, one for
spam and one for unsure messages.

To train SpamBayes, use the spam folder, and the 'train_as_ham' folder.
Any messages in these folders will be trained appropriately.  This means
that all messages that SpamBayes classifies as spam will also be trained
as such.  If you receive any 'false positives' (ham classified as spam),
you *must* copy the message into the 'train_as_ham' folder to correct the
training.  You may also place any saved spam messages you have into this
folder.

So that SpamBayes knows about ham as well as spam, you will also need to
move or copy mail into the 'train_as_ham' folder.  These may come from
the unsure folder, or from any other mail you have saved.  It is a good
idea to leave messages in the 'train_as_ham' and 'spam' folders, so that
you can retrain from scratch if required.  (However, you should always
clear out your unsure folder, preferably moving or copying the messages
into the appropriate training folder).

This SpamBayes application is designed to work with Outlook Express, and
provide the same sort of ease of use as the Outlook plugin.  Although the
majority of development and testing has been done with Outlook Express and
Eudora, any mail client that supports both IMAP and POP3 should be able to
use this application - if the client enables the user to work with an IMAP
account and POP3 account side-by-side (and move messages between them),
then it should work equally as well.

This module includes the following classes:
 o IMAPMessage
 o DynamicIMAPMessage
 o IMAPFileMessage
 o IMAPFileMessageFactory
 o IMAPMailbox
 o SpambayesMailbox
 o SpambayesInbox
 o Trainer
 o SpambayesAccount
 o SpambayesIMAPServer
 o OneParameterFactory
 o MyBayesProxy
 o MyBayesProxyListener
 o IMAPState
"""

todo = """
 o The RECENT flag should be unset at some point, but when?  The
   RFC says that a message is recent if this is the first session
   to be notified about the message.  Perhaps this can be done
   simply by *not* persisting this flag - i.e. the flag is always
   loaded as not recent, and only new messages are recent.  The
   RFC says that if it is not possible to determine, then all
   messages should be recent, and this is what we currently do.
 o The Mailbox should be calling the appropriate listener
   functions (currently only newMessages is called on addMessage).
   flagsChanged should also be called on store, addMessage, or ???
 o We cannot currently get part of a message via the BODY calls
   (with the <> operands), or get a part of a MIME message (by
   prepending a number).  This should be added!
 o If the user clicks the 'save and shutdown' button on the web
   interface, this will only kill the POP3 proxy and web interface
   threads, and not the IMAP server.  We need to monitor the thread
   that we kick off, and if it dies, we should die too.  Need to figure
   out how to do this in twisted.
 o Apparently, twisted.internet.app is deprecated, and we should
   use twisted.application instead.  Need to figure out what that means!
 o We could have a distinction between messages classified as spam
   and messages to train as spam.  At the moment we force users into
   the 'incremental training' system available with the Outlook plug-in.
 o Suggestions?
"""

# This module is part of the spambayes project, which is Copyright 2002-4
# The Python Software Foundation and is covered by the Python Software
# Foundation license.

__author__ = "Tony Meyer <ta-meyer@ihug.co.nz>"
__credits__ = "All the Spambayes folk."

try:
    True, False
except NameError:
    # Maintain compatibility with Python 2.2
    True, False = 1, 0

import os
import re
import sys
import md5
import time
import errno
import types
import thread
import getopt
import imaplib
import operator
import StringIO
import email.Utils

from twisted import cred
from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.app import Application
from twisted.internet.defer import maybeDeferred
from twisted.internet.protocol import ServerFactory
from twisted.protocols.imap4 import IMessage
from twisted.protocols.imap4 import parseNestedParens, parseIdList
from twisted.protocols.imap4 import IllegalClientResponse, IAccount
from twisted.protocols.imap4 import collapseNestedLists, MessageSet
from twisted.protocols.imap4 import IMAP4Server, MemoryAccount, IMailbox
from twisted.protocols.imap4 import IMailboxListener, collapseNestedLists

from spambayes import message
from spambayes.Options import options
from spambayes.tokenizer import tokenize
from spambayes import FileCorpus, Dibbler
from spambayes.Version import get_version_string
from spambayes.ServerUI import ServerUserInterface
from spambayes.UserInterface import UserInterfaceServer
from sb_server import POP3ProxyBase, State, _addressPortStr, _recreateState

def ensureDir(dirname):
    """Ensure that the given directory exists - in other words, if it
    does not exist, attempt to create it."""
    try:
        os.mkdir(dirname)
        if options["globals", "verbose"]:
            print "Creating directory", dirname
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise


class IMAPMessage(message.Message):
    '''IMAP Message base class.'''
    __implements__ = (IMessage,)

    def __init__(self, date):
        message.Message.__init__(self)
        # We want to persist more information than the generic
        # Message class.
        self.stored_attributes.extend(["date", "deleted", "flagged",
                                       "seen", "draft", "recent",
                                       "answered"])
        self.date = date
        self.clear_flags()

    # IMessage implementation
    def getHeaders(self, negate, *names):
        """Retrieve a group of message headers."""
        headers = {}
        for header, value in self.items():
            if (header.lower() in names and not negate) or names == ():
                headers[header.lower()] = value
        return headers

    def getFlags(self):
        """Retrieve the flags associated with this message."""
        return self._flags_iter()

    def _flags_iter(self):
        if self.deleted:
            yield "\\DELETED"
        if self.answered:
            yield "\\ANSWERED"
        if self.flagged:
            yield "\\FLAGGED"
        if self.seen:
            yield "\\SEEN"
        if self.draft:
            yield "\\DRAFT"
        if self.recent:
            yield "\\RECENT"

    def getInternalDate(self):
        """Retrieve the date internally associated with this message."""
        return self.date

    def getBodyFile(self):
        """Retrieve a file object containing the body of this message."""
        # Note only body, not headers!
        s = StringIO.StringIO()
        s.write(self.body())
        s.seek(0)
        return s

    def getSize(self):
        """Retrieve the total size, in octets, of this message."""
        return len(self.as_string())

    def getUID(self):
        """Retrieve the unique identifier associated with this message."""
        return self.id

    def isMultipart(self):
        """Indicate whether this message has subparts."""
        return False

    def getSubPart(self, part):
        """Retrieve a MIME sub-message

        @type part: C{int}
        @param part: The number of the part to retrieve, indexed from 0.

        @rtype: Any object implementing C{IMessage}.
        @return: The specified sub-part.
        """
        raise NotImplementedError

    # IMessage implementation ends

    def clear_flags(self):
        """Set all message flags to false."""
        self.deleted = False
        self.answered = False
        self.flagged = False
        self.seen = False
        self.draft = False
        self.recent = False

    def set_flag(self, flag, value):
        # invalid flags are ignored
        flag = flag.upper()
        if flag == "\\DELETED":
            self.deleted = value
        elif flag == "\\ANSWERED":
            self.answered = value
        elif flag == "\\FLAGGED":
            self.flagged = value
        elif flag == "\\SEEN":
            self.seen = value
        elif flag == "\\DRAFT":
            self.draft = value
        else:
            print "Tried to set invalid flag", flag, "to", value

    def flags(self):
        """Return the message flags."""
        all_flags = []
        if self.deleted:
            all_flags.append("\\DELETED")
        if self.answered:
            all_flags.append("\\ANSWERED")
        if self.flagged:
            all_flags.append("\\FLAGGED")
        if self.seen:
            all_flags.append("\\SEEN")
        if self.draft:
            all_flags.append("\\DRAFT")
        if self.draft:
            all_flags.append("\\RECENT")
        return all_flags

    def train(self, classifier, isSpam):
        if self.GetTrained() == (not isSpam):
            classifier.unlearn(self.asTokens(), not isSpam)
            self.RememberTrained(None)
        if self.GetTrained() is None:
            classifier.learn(self.asTokens(), isSpam)
            self.RememberTrained(isSpam)
        classifier.store()

    def structure(self, ext=False):
        """Body structure data describes the MIME-IMB
        format of a message and consists of a sequence of mime type, mime
        subtype, parameters, content id, description, encoding, and size.
        The fields following the size field are variable: if the mime
        type/subtype is message/rfc822, the contained message's envelope
        information, body structure data, and number of lines of text; if
        the mime type is text, the number of lines of text.  Extension fields
        may also be included; if present, they are: the MD5 hash of the body,
        body disposition, body language."""
        s = []
        for part in self.walk():
            if part.get_content_charset() is not None:
                charset = ("charset", part.get_content_charset())
            else:
                charset = None
            part_s = [part.get_main_type(), part.get_subtype(),
                      charset,
                      part.get('Content-Id'),
                      part.get('Content-Description'),
                      part.get('Content-Transfer-Encoding'),
                      str(len(part.as_string()))]
            #if part.get_type() == "message/rfc822":
            #    part_s.extend([envelope, body_structure_data,
            #                  part.as_string().count("\n")])
            #elif part.get_main_type() == "text":
            if part.get_main_type() == "text":
                part_s.append(str(part.as_string().count("\n")))
            if ext:
                part_s.extend([md5.new(part.as_string()).digest(),
                               part.get('Content-Disposition'),
                               part.get('Content-Language')])
            s.append(part_s)
        if len(s) == 1:
            return s[0]
        return s

    def body(self):
        rfc822 = self.as_string()
        bodyRE = re.compile(r"\r?\n(\r?\n)(.*)",
                            re.DOTALL + re.MULTILINE)
        bmatch = bodyRE.search(rfc822)
        return bmatch.group(2)

    def headers(self):
        rfc822 = self.as_string()
        bodyRE = re.compile(r"\r?\n(\r?\n)(.*)",
                            re.DOTALL + re.MULTILINE)
        bmatch = bodyRE.search(rfc822)
        return rfc822[:bmatch.start(2)]


class DynamicIMAPMessage(IMAPMessage):
    """An IMAP Message that may change each time it is loaded."""
    def __init__(self, func):
        date = imaplib.Time2Internaldate(time.time())[1:-1]
        IMAPMessage.__init__(self, date)
        self.func = func
        self.load()
    def load(self):
        self.setPayload(self.func(body=True, headers=True))


class IMAPFileMessage(IMAPMessage, FileCorpus.FileMessage):
    '''IMAP Message that persists as a file system artifact.'''

    def __init__(self, file_name, directory):
        """Constructor(message file name, corpus directory name)."""
        date = imaplib.Time2Internaldate(time.time())[1:-1]
        IMAPMessage.__init__(self, date)
        FileCorpus.FileMessage.__init__(self, file_name, directory)
        self.id = file_name
        self.directory = directory


class IMAPFileMessageFactory(FileCorpus.FileMessageFactory):
    '''MessageFactory for IMAPFileMessage objects'''
    def create(self, key, directory):
        '''Create a message object from a filename in a directory'''
        return IMAPFileMessage(key, directory)


class IMAPMailbox(cred.perspective.Perspective):
    __implements__ = (IMailbox,)

    def __init__(self, name, identity_name, id):
        cred.perspective.Perspective.__init__(self, name, identity_name)
        self.UID_validity = id
        self.listeners = []

    def getUIDValidity(self):
        """Return the unique validity identifier for this mailbox."""
        return self.UID_validity

    def addListener(self, listener):
        """Add a mailbox change listener."""
        self.listeners.append(listener)

    def removeListener(self, listener):
        """Remove a mailbox change listener."""
        self.listeners.remove(listener)


class SpambayesMailbox(IMAPMailbox):
    def __init__(self, name, id, directory):
        IMAPMailbox.__init__(self, name, "spambayes", id)
        self.UID_validity = id
        ensureDir(directory)
        self.storage = FileCorpus.FileCorpus(IMAPFileMessageFactory(),
                                             directory, r"[0123456789]*")
        # UIDs are required to be strictly ascending.
        if len(self.storage.keys()) == 0:
            self.nextUID = 1
        else:
            self.nextUID = long(self.storage.keys()[-1]) + 1
        # Calculate initial recent and unseen counts
        # XXX Note that this will always end up with zero counts
        # XXX until the flags are persisted.
        self.unseen_count = 0
        self.recent_count = 0
        for msg in self.storage:
            if not msg.seen:
                self.unseen_count += 1
            if msg.recent:
                self.recent_count += 1

    def getUIDNext(self, increase=False):
        """Return the likely UID for the next message added to this
        mailbox."""
        reply = str(self.nextUID)
        if increase:
            self.nextUID += 1
        return reply

    def getUID(self, msg):
        """Return the UID of a message in the mailbox."""
        # Note that IMAP messages are 1-based, our messages are 0-based
        d = self.storage
        return long(d.keys()[msg - 1])

    def getFlags(self):
        """Return the flags defined in this mailbox."""
        return ["\\Answered", "\\Flagged", "\\Deleted", "\\Seen",
                "\\Draft"]

    def getMessageCount(self):
        """Return the number of messages in this mailbox."""
        return len(self.storage.keys())

    def getRecentCount(self):
        """Return the number of messages with the 'Recent' flag."""
        return self.recent_count

    def getUnseenCount(self):
        """Return the number of messages with the 'Unseen' flag."""
        return self.unseen_count

    def isWriteable(self):
        """Get the read/write status of the mailbox."""
        return True

    def destroy(self):
        """Called before this mailbox is deleted, permanently."""
        # Our mailboxes cannot be deleted
        raise NotImplementedError

    def getHierarchicalDelimiter(self):
        """Get the character which delimits namespaces for in this
        mailbox."""
        return '.'

    def requestStatus(self, names):
        """Return status information about this mailbox."""
        answer = {}
        for request in names:
            request = request.upper()
            if request == "MESSAGES":
                answer[request] = self.getMessageCount()
            elif request == "RECENT":
                answer[request] = self.getRecentCount()
            elif request == "UIDNEXT":
                answer[request] = self.getUIDNext()
            elif request == "UIDVALIDITY":
                answer[request] = self.getUIDValidity()
            elif request == "UNSEEN":
                answer[request] = self.getUnseenCount()
        return answer

    def addMessage(self, content, flags=(), date=None):
        """Add the given message to this mailbox."""
        msg = self.storage.makeMessage(self.getUIDNext(True))
        msg.date = date
        msg.setPayload(content.read())
        self.storage.addMessage(msg)
        self.store(MessageSet(long(msg.id), long(msg.id)), flags, 1, True)
        msg.recent = True
        msg.store()
        self.recent_count += 1
        self.unseen_count += 1

        for listener in self.listeners:
            listener.newMessages(self.getMessageCount(),
                                 self.getRecentCount())
        d = defer.Deferred()
        reactor.callLater(0, d.callback, self.storage.keys().index(msg.id))
        return d

    def expunge(self):
        """Remove all messages flagged \\Deleted."""
        deleted_messages = []
        for msg in self.storage:
            if msg.deleted:
                if not msg.seen:
                    self.unseen_count -= 1
                if msg.recent:
                    self.recent_count -= 1
                deleted_messages.append(long(msg.id))
                self.storage.removeMessage(msg)
        if deleted_messages != []:
            for listener in self.listeners:
                listener.newMessages(self.getMessageCount(),
                                     self.getRecentCount())
        return deleted_messages

    def search(self, query, uid):
        """Search for messages that meet the given query criteria.

        @type query: C{list}
        @param query: The search criteria

        @rtype: C{list}
        @return: A list of message sequence numbers or message UIDs which
        match the search criteria.
        """
        if self.getMessageCount() == 0:
            return []
        all_msgs = MessageSet(long(self.storage.keys()[0]),
                              long(self.storage.keys()[-1]))
        matches = []
        for id, msg in self._messagesIter(all_msgs, uid):
            for q in query:
                if msg.matches(q):
                    matches.append(id)
                    break
        return matches

    def _messagesIter(self, messages, uid):
        if uid:
            messages.last = long(self.storage.keys()[-1])
        else:
            messages.last = self.getMessageCount()
        for id in messages:
            if uid:
                msg = self.storage.get(str(id))
            else:
                msg = self.storage.get(str(self.getUID(id)))
            if msg is None:
                # Non-existant message.
                continue
            # Load the message, if necessary
            if hasattr(msg, "load"):
                msg.load()
            yield (id, msg)

    def fetch(self, messages, uid):
        """Retrieve one or more messages."""
        return self._messagesIter(messages, uid)

    def store(self, messages, flags, mode, uid):
        """Set the flags of one or more messages."""
        stored_messages = {}
        for id, msg in self._messagesIter(messages, uid):
            if mode == 0:
                msg.clear_flags()
                value = True
            elif mode == -1:
                value = False
            elif mode == 1:
                value = True
            for flag in flags or (): # flags might be None
                if flag == '(' or flag == ')':
                    continue
                if flag == "SEEN" and value == True and msg.seen == False:
                    self.unseen_count -= 1
                if flag == "SEEN" and value == False and msg.seen == True:
                    self.unseen_count += 1
                msg.set_flag(flag, value)
            stored_messages[id] = msg.flags()
        return stored_messages


class SpambayesInbox(SpambayesMailbox):
    """A special mailbox that holds status messages from SpamBayes."""
    def __init__(self, id):
        IMAPMailbox.__init__(self, "INBOX", "spambayes", id)
        self.UID_validity = id
        self.nextUID = 1
        self.unseen_count = 0
        self.recent_count = 0
        self.storage = {}
        self.createMessages()

    def buildStatusMessage(self, body=False, headers=False):
        """Build a message containing the current status message.

        If body is True, then return the body; if headers is True
        return the headers.  If both are true, then return both
        (and insert a newline between them).
        """
        msg = []
        if headers:
            msg.append("Subject:SpamBayes Status")
            msg.append('From:"SpamBayes" <no-reply@localhost>')
            if body:
                msg.append('\r\n')
        if body:
            state.buildStatusStrings()
            msg.append(state.warning or "SpamBayes operating correctly.")
        return "\r\n".join(msg)

    def createMessages(self):
        """Create the special messages that live in this mailbox."""
        state.buildStatusStrings()
        # This about message could have a bit more content!
        about = 'Subject: About SpamBayes\r\n' \
                 'From: "SpamBayes" <no-reply@localhost>\r\n\r\n' \
                 'See <http://spambayes.org>.\r\n'
        date = imaplib.Time2Internaldate(time.time())[1:-1]
        msg = IMAPMessage(date)
        msg.setPayload(about)
        self.addMessage(msg)
        msg = DynamicIMAPMessage(self.buildStatusMessage)
        self.addMessage(msg)
        # XXX Add other messages here, for example
        # XXX statistics
        # XXX information from sb_server homepage about number
        # XXX   of messages classified etc.
        # XXX one with a link to the configuration page
        # XXX   (or maybe even the configuration page itself,
        # XXX    in html!)

    def isWriteable(self):
        """Get the read/write status of the mailbox."""
        return False

    def addMessage(self, msg, flags=(), date=None):
        """Add the given message to this mailbox."""
        msg.id = self.getUIDNext(True)
        self.storage[msg.id] = msg
        d = defer.Deferred()
        reactor.callLater(0, d.callback, self.storage.keys().index(msg.id))
        return d

    def expunge(self):
        """Remove all messages flagged \\Deleted."""
        # Mailbox is read-only.
        return []

    def store(self, messages, flags, mode, uid):
        """Set the flags of one or more messages."""
        # Mailbox is read-only.
        return {}


class Trainer(object):
    """Listens to a given mailbox and trains new messages as spam or
    ham."""
    __implements__ = (IMailboxListener,)

    def __init__(self, mailbox, asSpam):
        self.mailbox = mailbox
        self.asSpam = asSpam

    def modeChanged(self, writeable):
        # We don't care
        pass

    def flagsChanged(self, newFlags):
        # We don't care
        pass

    def newMessages(self, exists, recent):
        # We don't get passed the actual message, or the id of
        # the message, or even the message number.  We just get
        # the total number of new/recent messages.
        # However, this function should be called _every_ time
        # that a new message appears, so we should be able to
        # assume that the last message is the new one.
        # (We ignore the recent count)
        if exists is not None:
            id = self.mailbox.getUID(exists)
            msg = self.mailbox.storage[str(id)]
            msg.train(state.bayes, self.asSpam)


class SpambayesAccount(MemoryAccount):
    """Account for Spambayes server."""

    def __init__(self, id, ham, spam, unsure, inbox):
        MemoryAccount.__init__(self, id)
        self.mailboxes = {"SPAM" : spam,
                          "UNSURE" : unsure,
                          "TRAIN_AS_HAM" : ham,
                          "INBOX" : inbox}

    def select(self, name, readwrite=1):
        # 'INBOX' is a special case-insensitive name meaning the
        # primary mailbox for the user; for our purposes this contains
        # special messages from SpamBayes.
        return MemoryAccount.select(self, name, readwrite)


class SpambayesIMAPServer(IMAP4Server):
    IDENT = "Spambayes IMAP Server IMAP4rev1 Ready"

    def __init__(self, user_account):
        IMAP4Server.__init__(self)
        self.account = user_account

    def authenticateLogin(self, user, passwd):
        """Lookup the account associated with the given parameters."""
        if user == options["imapserver", "username"] and \
           passwd == options["imapserver", "password"]:
            return (IAccount, self.account, None)
        raise cred.error.UnauthorizedLogin()

    def connectionMade(self):
        state.activeIMAPSessions += 1
        state.totalIMAPSessions += 1
        IMAP4Server.connectionMade(self)

    def connectionLost(self, reason):
        state.activeIMAPSessions -= 1
        IMAP4Server.connectionLost(self, reason)

    def do_CREATE(self, tag, args):
        """Creating new folders on the server is not permitted."""
        self.sendNegativeResponse(tag, \
                                  "Creation of new folders is not permitted")
    auth_CREATE = (do_CREATE, IMAP4Server.arg_astring)
    select_CREATE = auth_CREATE

    def do_DELETE(self, tag, args):
        """Deleting folders on the server is not permitted."""
        self.sendNegativeResponse(tag, \
                                  "Deletion of folders is not permitted")
    auth_DELETE = (do_DELETE, IMAP4Server.arg_astring)
    select_DELETE = auth_DELETE


class OneParameterFactory(ServerFactory):
    """A factory that allows a single parameter to be passed to the created
    protocol."""
    def buildProtocol(self, addr):
        """Create an instance of a subclass of Protocol, passing a single
        parameter."""
        if self.parameter is not None:
            p = self.protocol(self.parameter)
        else:
            p = self.protocol()
        p.factory = self
        return p


class MyBayesProxy(POP3ProxyBase):
    """Proxies between an email client and a POP3 server, redirecting
    mail to the imap server as necessary.  It acts on the following
    POP3 commands:

     o RETR:
        o Adds the judgement header based on the raw headers and body
          of the message.
    """

    # This message could be a bit more informative - it could at least
    # say whether it's the spam or unsure folder.  It could give
    # information about who the message was from, or what the subject
    # was, if people thought that would be a good idea.
    intercept_message = 'From: "Spambayes" <no-reply@localhost>\r\n' \
                        'Subject: Spambayes Intercept\r\n\r\nA message ' \
                        'was intercepted by Spambayes (it scored %s).\r\n' \
                        '\r\nYou may find it in the Spam or Unsure ' \
                        'folder.\r\n\r\n'

    def __init__(self, clientSocket, serverName, serverPort, spam, unsure):
        POP3ProxyBase.__init__(self, clientSocket, serverName, serverPort)
        self.handlers = {'RETR': self.onRetr}
        state.totalSessions += 1
        state.activeSessions += 1
        self.isClosed = False
        self.spam_folder = spam
        self.unsure_folder = unsure

    def send(self, data):
        """Logs the data to the log file."""
        if options["globals", "verbose"]:
            state.logFile.write(data)
            state.logFile.flush()
        try:
            return POP3ProxyBase.send(self, data)
        except socket.error:
            self.close()

    def recv(self, size):
        """Logs the data to the log file."""
        data = POP3ProxyBase.recv(self, size)
        if options["globals", "verbose"]:
            state.logFile.write(data)
            state.logFile.flush()
        return data

    def close(self):
        # This can be called multiple times by async.
        if not self.isClosed:
            self.isClosed = True
            state.activeSessions -= 1
            POP3ProxyBase.close(self)

    def onTransaction(self, command, args, response):
        """Takes the raw request and response, and returns the
        (possibly processed) response to pass back to the email client.
        """
        handler = self.handlers.get(command, self.onUnknown)
        return handler(command, args, response)

    def onRetr(self, command, args, response):
        """Classifies the message.  If the result is ham, then simply
        pass it through.  If the result is an unsure or spam, move it
        to the appropriate IMAP folder."""
        # XXX This is all almost from sb_server!  We could just
        # XXX extract that out into a function and call it here.

        # Use '\n\r?\n' to detect the end of the headers in case of
        # broken emails that don't use the proper line separators.
        if re.search(r'\n\r?\n', response):
            # Remove the trailing .\r\n before passing to the email parser.
            # Thanks to Scott Schlesier for this fix.
            terminatingDotPresent = (response[-4:] == '\n.\r\n')
            if terminatingDotPresent:
                response = response[:-3]

            # Break off the first line, which will be '+OK'.
            ok, messageText = response.split('\n', 1)

            try:
                msg = message.SBHeaderMessage()
                msg.setPayload(messageText)
                # Now find the spam disposition and add the header.
                (prob, clues) = state.bayes.spamprob(msg.asTokens(),\
                                 evidence=True)

                msg.addSBHeaders(prob, clues)

                # Check for "RETR" or "TOP N 99999999" - fetchmail without
                # the 'fetchall' option uses the latter to retrieve messages.
                if (command == 'RETR' or
                    (command == 'TOP' and
                     len(args) == 2 and args[1] == '99999999')):
                    cls = msg.GetClassification()
                    dest_folder = None
                    if cls == options["Headers", "header_ham_string"]:
                        state.numHams += 1
                        headers = []
                        for name, value in msg.items():
                            header = "%s: %s" % (name, value)
                            headers.append(re.sub(r'\r?\n', '\r\n', header))
                        body = re.split(r'\n\r?\n', messageText, 1)[1]
                        messageText = "\r\n".join(headers) + "\r\n\r\n" + body
                    elif prob > options["Categorization", "spam_cutoff"]:
                        dest_folder = self.spam_folder
                        state.numSpams += 1
                    else:
                        dest_folder = self.unsure_folder
                        state.numUnsure += 1
                    if dest_folder:
                        msg = StringIO.StringIO(msg.as_string())
                        date = imaplib.Time2Internaldate(time.time())[1:-1]
                        dest_folder.addMessage(msg, (), date)

                        # We have to return something, because the client
                        # is expecting us to.  We return a short message
                        # indicating that a message was intercepted.
                        messageText = self.intercept_message % (prob,)
            except:
                stream = cStringIO.StringIO()
                traceback.print_exc(None, stream)
                details = stream.getvalue()
                detailLines = details.strip().split('\n')
                dottedDetails = '\n.'.join(detailLines)
                headerName = 'X-Spambayes-Exception'
                header = Header(dottedDetails, header_name=headerName)
                headers, body = re.split(r'\n\r?\n', messageText, 1)
                header = re.sub(r'\r?\n', '\r\n', str(header))
                headers += "\n%s: %s\r\n\r\n" % (headerName, header)
                messageText = headers + body
                print >>sys.stderr, details
            retval = ok + "\n" + messageText
            if terminatingDotPresent:
                retval += '.\r\n'
            return retval
        else:
            # Must be an error response.
            return response

    def onUnknown(self, command, args, response):
        """Default handler; returns the server's response verbatim."""
        return response


class MyBayesProxyListener(Dibbler.Listener):
    """Listens for incoming email client connections and spins off
    MyBayesProxy objects to serve them.
    """

    def __init__(self, serverName, serverPort, proxyPort, spam, unsure):
        proxyArgs = (serverName, serverPort, spam, unsure)
        Dibbler.Listener.__init__(self, proxyPort, MyBayesProxy, proxyArgs)
        print 'Listener on port %s is proxying %s:%d' % \
               (_addressPortStr(proxyPort), serverName, serverPort)


class IMAPState(State):
    def __init__(self):
        State.__init__(self)

        # Set up the extra statistics.
        self.totalIMAPSessions = 0
        self.activeIMAPSessions = 0

    def buildServerStrings(self):
        """After the server details have been set up, this creates string
        versions of the details, for display in the Status panel."""
        self.serverPortString = str(self.imap_port)
        # Also build proxy strings
        State.buildServerStrings(self)

state = IMAPState()

# ===================================================================
# __main__ driver.
# ===================================================================

def setup():
    # Setup state, app, boxes, trainers and account
    state.createWorkers()
    proxyListeners = []
    app = Application("SpambayesIMAPServer")

    spam_box = SpambayesMailbox("Spam", 0, options["Storage",
                                                   "spam_cache"])
    unsure_box = SpambayesMailbox("Unsure", 1, options["Storage",
                                                       "unknown_cache"])
    ham_train_box = SpambayesMailbox("TrainAsHam", 2,
                                     options["Storage", "ham_cache"])
    inbox = SpambayesInbox(3)

    spam_trainer = Trainer(spam_box, True)
    ham_trainer = Trainer(ham_train_box, False)
    spam_box.addListener(spam_trainer)
    ham_train_box.addListener(ham_trainer)

    user_account = SpambayesAccount(options["imapserver", "username"],
                                    ham_train_box, spam_box, unsure_box,
                                    inbox)

    # add IMAP4 server
    f = OneParameterFactory()
    f.protocol = SpambayesIMAPServer
    f.parameter = user_account
    state.imap_port = options["imapserver", "port"]
    app.listenTCP(state.imap_port, f)

    # add POP3 proxy
    for (server, serverPort), proxyPort in zip(state.servers,
                                               state.proxyPorts):
        listener = MyBayesProxyListener(server, serverPort, proxyPort,
                                        spam_box, unsure_box)
        proxyListeners.append(listener)
    state.buildServerStrings()

    # add web interface
    httpServer = UserInterfaceServer(state.uiPort)
    serverUI = ServerUserInterface(state, _recreateState)
    httpServer.register(serverUI)

    return app

def run():
    # Read the arguments.
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hbd:D:u:o:')
    except getopt.error, msg:
        print >>sys.stderr, str(msg) + '\n\n' + __doc__
        sys.exit()

    launchUI = False
    for opt, arg in opts:
        if opt == '-h':
            print >>sys.stderr, __doc__
            sys.exit()
        elif opt == '-b':
            launchUI = True
        elif opt == '-o':
            options.set_from_cmdline(arg, sys.stderr)

    # Let the user know what they are using...
    print get_version_string("IMAP Server")
    print get_version_string("POP3 Proxy")
    print "and engine %s," % (get_version_string(),)
    from twisted.copyright import version as twisted_version
    print "with twisted version %s.\n" % (twisted_version,)

    # setup everything
    app = setup()

    # kick things off
    thread.start_new_thread(Dibbler.run, (launchUI,))
    app.run(save=False)

if __name__ == "__main__":
    run()

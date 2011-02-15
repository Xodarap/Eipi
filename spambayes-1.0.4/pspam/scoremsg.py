#! /usr/bin/env python
"""Score a message provided on stdin and show the evidence."""

import sys
import email

import ZODB
from ZEO.ClientStorage import ClientStorage

import pspam.database
from spambayes.Options import options
from spambayes.tokenizer import tokenize

try:
    True, False
except NameError:
    # Maintain compatibility with Python 2.2
    True, False = 1, 0


def main(fp):
    db = pspam.database.open()
    r = db.open().root()

    p = r["profile"]

    msg = email.message_from_file(fp)
    prob, evidence = p.classifier.spamprob(tokenize(msg), True)
    print "Score:", prob
    print
    print "Clues"
    print "-----"
    for clue, prob in evidence:
        print clue, prob
##    print
##    print msg

if __name__ == "__main__":
    main(sys.stdin)

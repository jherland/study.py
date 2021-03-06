"""Automatic permutation of anagrams, aided by a wordlist.

Can surely be done better !

See study.LICENSE for copyright and license information.
"""

class OrdBok:
    def __init__(self, source=None):
        self.__bok = {} # { lowered: [ word, ...] }
        if source is None: self.ingest('/usr/share/dict/words')
        else: self.ingest(source)

    def ingest(self, file):
        fd = open(file)
        try:
            while True:
                line = fd.readline()
                if not line: break
                key = filter(lambda i: i.isalnum(), line.lower())
                try: row = self.__bok[key]
                except KeyError: row = self.__bok[key] = []
                row.append(line.strip())
        finally: fd.close()

    def parse(self, text, store):
        i = len(text)
        while i > 0:
            stem, tail = text[:i], text[i:]
            try: hits = self.__bok[stem]
            except KeyError: pass
            else:
                if tail:
                    work = []
                    self.parse(tail, work)
                    for it in work: store.append(' '.join([stem, it]))
                else:
                    store.append(stem)
            i = i - 1

from study.maths.permute import Permutation

def anagrams(text, dict=OrdBok(), trawl=Permutation.all):
    jam = ''.join(text.split())
    loop, ans = trawl(len(jam)), []
    loop.next() # discard identity, i.e. given text
    for it in loop:
        dict.parse(''.join(it.permute(jam)), ans)

    return ans

del Permutation

import os, sys, tot_sz

db = {}
no_docs = 0

########################## Levinshtein approach -- too slowly

def levenshtein_dist(s, t):
    # char s[1..m], char t[1..n]):
    # for all i and j, d[i,j] will hold the Levenshtein distance between
    # the first i characters of s and the first j characters of t;
    # note that d has (m+1)x(n+1) values
    # declare int d[0..m, 0..n]

    m = len(s)
    n = len(t)

    d = [range(n+1)] +\
        [[i] + [0] * n for i in xrange(1, m+1)]

    # d[i][0] = i # the distance of any first string to an empty second string
    # d[0][j] = j # the distance of any second string to an empty first string

    for j in xrange(1, n+1):
        for i in xrange(1, m+1):
            if s[i-1] == t[j-1]:
                d[i][j] = d[i-1][j-1] # no operation required
            else:
                d[i][j] = min(
                    d[i-1][j],   # deletion
                    d[i][j-1],   # insertion
                    d[i-1][j-1]  # substitution
                    ) + 1

    return d[m][n]

words = {}
similar_words = {}
def index_file_levin(doc_id, content):
    global db, no_docs, words, similar_words

    doc_words = set()

    no_docs += 1
    if no_docs % 10 == 0:
        print no_docs

    w = ''
    content += ' '
    for c in content:
        if c.isalnum():
            w += c
        else:
            if len(w) > 3:
                doc_words.add(w.lower())

            w = ''

    for w in doc_words:
        if w in db:
            db.setdefault(w, []).append(doc_id)
        elif w in similar_words:
            k = similar_words[w]
            if (k == w) or (k not in doc_words):
                db.setdefault(k, []).append(doc_id)
        else:
            found = False
            for i in [len(w), len(w)-1, len(w)+1]:
                for k in words.get(i, set()):
                    if levenshtein_dist(w, k) <= 1:
                        found = True
                        break

                if found:
                    break

            if found:
                print w, k
                db.setdefault(k, []).append(doc_id)
                similar_words[w] = k
            else:
                db.setdefault(w, []).append(doc_id)
                words.setdefault(len(w), set()).add(w)
                similar_words[w] = w

##########################

class DocId:
    def __init__(self, name, prev = None):
        self._name = name
        self._prev = prev

    def __str__(self):
        l = []
        p = self
        while p != None:
            l.append(p._name)
            p = p._prev

        for i in xrange(len(l)/2):
            l[i], l[len(l)-1-i] = l[len(l)-1-i], l[i]
        
        return '/'.join(l)

    def __repr__(self):
        return self.__str__()
 
def index_file(content, doc_id):
    global db, no_docs

    no_docs += 1
    #if no_docs % 1000 == 0:
    #    print no_docs 

    doc_words = set()
    beg = content.find('X-FileName:')
    if beg >= 0:
        beg = content.find('\n', beg)
    assert(beg >= 0)
    content = content.lower() + ' '
    for cur in xrange(beg, len(content)):
        if not content[cur].isalnum():
            if cur - beg > 3:
                doc_words.add(content[beg:cur])

            beg = cur + 1

    for w in doc_words:
        db.setdefault(w, []).append(doc_id)
    
def index_flat_dir(path, doc_id):
    for root, dirs, files in os.walk(path):
        for name in files:
            if not name.startswith('.'):
                with open(os.path.join(root, name), 'r+') as f:
                    index_file(f.read(), DocId(intern(name), doc_id))

def index_subdirs(path, subdirname):
    for name in os.listdir(path):
        if not name.startswith('.'):
            index_flat_dir(os.path.join(path, name, subdirname), DocId(intern(name)))

def index_allsubdirs(dir_path):
    dir_id = DocId('')
    for root, dirs, files in os.walk(dir_path):
        for name in files:
            if not name.startswith('.'):
                with open(os.path.join(root, name), 'r+') as f:
                    if root != dir_id._name:
                        dir_id.name = intern(root)

                    index_file(f.read(), DocId(intern(name), dir_id))

#index_flat_dir('./enron_mail_20110402/maildir/skilling-j/all_documents', DocId('skilling-j'))
#index_subdirs('./enron_mail_20110402/maildir', 'all_documents')
index_allsubdirs('./enron_mail_20110402/maildir')

#print '\n'.join(db.keys())
#print db

print "Queries:"

for key in ['information', 'schedule', 'visit', 'inspection']:
    print
    print 'search:', key
    prev_did = None
    for doc_id in db[key]:
        if doc_id._prev != prev_did:
            prev_did = doc_id._prev
            print
            print ' ', prev_did, ':',

        print doc_id._name,

    print

print '#docs:', no_docs, no_docs / 1024, "K"
print '#keys:', len(db), len(db) / 1024, "K"

try:
    total_size = tot_sz.total_size(db)
    size = sys.getsizeof(db)
    print 'total size:', total_size / 1024, "K"
    print 'size:', size / 1024, "K"
except TypeError:
    print "Running pypy, get size is not implemented"



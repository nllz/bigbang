from pprint import pprint as pp
import email
import re
import dateutil.parser as dp
import pytz
import warnings

re_cache = {
    'top_exp': re.compile("From .*\d\d\d\d\n"),
    'msg_id': re.compile("<\S*@\S*>")
}


def split_references(refs):
    return re_cache['msg_id'].findall(refs)


def get_refs(refs):
    return re_cache['msg_id'].findall(refs)


def clean_mid(mid):
    try:
        return get_refs(mid)[0]
    except IndexError:
        print mid
        return mid

def clean_from(m_from):
    """
    Return a person's name extracted from 'From' field
    of email, based on heuristics.
    """

    cleaned = m_from

    try:
        if "(" in m_from:
            cleaned = m_from[m_from.index("(") + 1:m_from.rindex(")")]
        elif "<" in m_from:
            # if m_from.index("<") > -1:
            cleaned = m_from[0:m_from.index("<") - 1]

    except ValueError:
        warnings.warn("%s is hard to clean" % (m_from))

    cleaned = cleaned.strip("\"")

    return cleaned

def normalize_email_address(address):
    """
    Takes a valid email address and returns a normalized one, for matching purposes.
    """
    # TODO: drop the + labeling
    return address.lower()

def clean_name(name):
    """
    Clean just the name portion from email.utils.parseaddr.

    Returns None if the name portion is missing anything name-like. Otherwise, returns the cleaned name.
    """

    # we see these specific strings due to parsing issues in email somewhere
    name = name.replace('unknown charset', ' ') 
    name = name.replace('wrong string', ' ')
    name = name.replace('_', ' ')

    # these are stop characters we can just delete
    stop_characters = unicode('"<>\\()/:?%!+\'@')
    stop_characters_map = dict((ord(char), None) for char in stop_characters)

    name = unicode(name, 'utf-8', 'ignore').translate(stop_characters_map)

    # do we need to also catch email archives that use anti-spam measures?
    # like: .replace(' at ','@')

    # TODO: decode or collapse rfc2231 encodings, like '=?utf-8?q?carlos_gonz=c3=a1lez-cadenas?=' ?

    name = name.strip() # remove leading and trailing whitespace

    if len(name) > 0:
        return name
    else:
        return None

def tokenize_name(clean_name):
    """
    Create a tokenized version of a name, good for comparison and sorting for entity resolution.

    Takes a Unicode name already cleaned of most punctuation and spurious characters, hopefully.
    """

    # make lower case, remove "." and ",", tokenize and lexicographically sort the tokens, join by spaces, return as a string

    stop_characters = unicode('".,')
    stop_characters_map = dict((ord(char), None) for char in stop_characters)
    name = clean_name.translate(stop_characters_map)

    tokens = name.lower().split() # splits on whitespace
    
    if len(tokens) == 0:
        return None

    tokenized_name = ' '.join(sorted(tokens)) 
    
    return tokenized_name

def guess_first_name(cleaned_from):
    """
    Attempt to extract a person's first name from the cleaned version of their name
    (from a 'From' field). This may or may not be the given name. Returns None
    if heuristic doesn't recognize a separable first name.
    """
    
    cleaned_from = cleaned_from.strip() # remove leading and trailing whitespace
    
    # accomodate Last, First name format
    if ',' in cleaned_from:
        parts = cleaned_from.split(',')
        if len(parts) > 2:
            return None
        first_part = parts[1].strip()
        
        if ' ' in first_part:   # Last, First Middle? Or something entirely different
            return None
        else:
            return first_part
        
    elif ' ' in cleaned_from:
        parts = cleaned_from.split(' ')
        if len(parts) == 2: # e.g. First Last
            return parts[0]
        if len(parts) == 3: # e.g. First Middle Last
            return parts[0]
        return None
    else:   # no spaces or commas? with a single name, more likely to be a handle than a given name
        return None

def get_date(message):
    def safe_unicode(t):
        return t and unicode(t, 'utf-8', 'ignore')
    try:
        # some mail clients add a parenthetical timezone
        ds = safe_unicode(message.get('Date'))
        ds = re.sub("\(.*$", "", ds)
        ds = re.sub("--", "-", ds)
        ds = re.sub(" Hora.*$", "", ds)

        date = dp.parse(ds)

        # this adds noise and could raise trouble
        if date.tzinfo is None:
            date = pytz.utc.localize(date)

        return date
    except TypeError:
        print "Date parsing error on: "
        print ds

        return None
    except ValueError:
        print "Date parsing error on: "
        print ds

        return None

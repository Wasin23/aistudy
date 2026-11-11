# Constituency parsing: sentence -> Penn Treebank-style tree.
# pip install stanza nltk      
# pip install benepar spacy        (optional fallback; may not install on Python 3.13)
#   python -m spacy download en_core_web_md

from nltk import Tree


def parse_stanza(text):
    import stanza
    stanza.download("en", processors="tokenize,pos,constituency", verbose=False)
    nlp = stanza.Pipeline("en", processors="tokenize,pos,constituency", verbose=False)
    return [str(s.constituency) for s in nlp(text).sentences]


def parse(text):
    return parse_stanza(text)


def show(parse_string):
    Tree.fromstring(parse_string).pretty_print()


if __name__ == "__main__":
    for p in parse("The old man the boats. I saw the man with the telescope."):
        print(p)
        show(p)

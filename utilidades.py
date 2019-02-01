# coding=utf-8
# __author__ = 'Mario Romera Fernández'

from __future__ import print_function


def to_unicode(obj, encoding="utf-8"):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def comment(sentence):
    """
    Print header and footer of code delimiter in the form of:
    ################################################################################
    ################################### SENTENCE ###################################
    ################################# END SENTENCE #################################
    ################################################################################
    :param sentence: basestring
    """
    sentence = to_unicode(sentence)
    sentence = u" {} ".format(sentence)
    print(u"{}".format(u"#" * 80))
    print(u"{:#^80}".format(sentence.upper()))
    sentence_end = u" END" + sentence
    print(u"{:#^80}".format(sentence_end.upper()))
    print(u"{}".format(u"#" * 80))


def remove_trailing_zeros(l=None):
    """
    Removes trailing zeros from a list
    :param l: list
    """
    if not l:
        l = []
    for i in reversed(l):
        if i == 0:
            l.pop(-1)
        else:
            return l
    return l


def pf(var, struct=1, key=None, cont=None):
    """
    Prints type, length (if available) and value of a variable recursively.
    (ANSI colors, bad output in cmd.exe, designed for PyCharm console)
    :param var: var to print info from
    :param struct: 0 to avoid print values
    :param key: key of the dictionary
    :param cont: stores the length of nested vars in a list to print proper indentation
    """

    # print("{}".format(cont), end="")

    if not cont:
        cont = []
    try:
        l = len(var)
    except TypeError:
        l = None
    # Prints "|   " if nested, else prints "    "
    if len(cont) > 1:
        remove_trailing_zeros(cont)
        for c in cont[:-1]:
            if c > 0:
                print(u"  \033[96m|\033[00m ", end="")
            else:
                print(u"    ", end="")
    # Prints "  |->"
    if len(cont) >= 1:
        print(u"  \033[96m|->\033[00m", end="")
    # Substracts 1 from the last element of cont list
    if len(cont) > 0 and cont[-1] > 0:
        cont[-1] -= 1
    # Prints the var type
    print(u"\033[91m{}\033[00m".format(str(type(var)).rsplit()[1].replace("'", "").replace(">", "").upper()), end="")
    # Prints the var length
    if l is not None:
        print(u":\033[93m{}\033[00m ".format(l), end="")
    else:
        print(end=" ")
    # Prints the var value
    if struct == 1:
        if key is None:
            print(var)
        else:
            print(u"'\033[95m{}\033[00m':{}".format(key, var))
    else:
        print(end="\n")
    # If var is iterable call pf function for each value
    if hasattr(var, '__iter__'):
        cont.append(l)
        if isinstance(var, dict):
            for k, v in var.items():
                pf(var=v, struct=struct, key=k, cont=cont)
        else:
            for i in var:
                pf(var=i, struct=struct, cont=cont)


if __name__ == '__main__':
    import datetime

    integer = 1
    decimal = 3.14159
    string = "áñ@"
    date = datetime.datetime.now()
    aList = [integer, decimal, u"añ@2", string]
    aList2 = aList[:]
    aList2[1] = aList
    aSet = set(aList)
    aDict = {"key1": aList2, "key2": decimal, "date": date}
    aTuple = (aList2, aDict, aList, aSet, aList2)
    print(end="\n")
    pf(aTuple)
    print(end="\n")
    pf(aTuple, 0)

    comment(u"áñ@")
    print(end="\n")
    comment("áñ@")
    print(end="\n")
    comment(u"operaciones bbdd")

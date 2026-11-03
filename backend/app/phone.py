"""Dial-string syntax only: no country, carrier, reachability or E.164 assumptions."""
import re


def dialable_phone(value):
    text=value.strip()
    if not re.fullmatch(r'\+?[0-9 ()-]+',text) or not re.search(r'[0-9]',text):
        raise ValueError('Use digits, an optional leading plus, spaces, hyphens and balanced parentheses')
    opened=False
    digits=0
    for char in text:
        if char=='(':
            if opened:raise ValueError('Phone parentheses must not nest')
            opened=True;digits=0
        elif char==')':
            if not opened or not digits:raise ValueError('Phone parentheses must enclose digits')
            opened=False
        elif opened and char.isdigit():digits+=1
    if opened:raise ValueError('Phone parentheses must be balanced')
    return re.sub(r'[ ()-]','',text)

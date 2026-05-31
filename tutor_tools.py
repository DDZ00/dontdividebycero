"""Helper tools for the 'Don't divide by cero!' game.

Two functions you will use in every cycle:

  decrypt_message(enc_field, p, q, e)  -> turns an 'ENC:...' payload into text
  sha256_hex(text)                     -> SHA-256 hash of a string

You don't need to understand the maths inside. Just import them:

  from tutor_tools import decrypt_message, sha256_hex
"""

import hashlib

from sympy import mod_inverse  # used to compute d, the inverse of e


def decrypt_message(enc_field: str, p: int, q: int, e: int) -> str:
    """Decrypt an 'ENC:<n1>,<n2>,...' payload using toy RSA.

    enc_field : the full payload_info text, starting with 'ENC:'.
    p, q      : the two prime numbers you worked out with statistics.
    e         : the exponent you worked out with statistics.

    If your p, q or e are wrong, the result will be gibberish.
    """
    n = p * q
    phi = (p - 1) * (q - 1)
    d = int(mod_inverse(e, phi))                          # d = inverse of e mod phi
    numbers = [int(x) for x in enc_field[4:].split(',')]  # drop 'ENC:' then split
    return ''.join(chr(pow(c, d, n)) for c in numbers)


def sha256_hex(text: str) -> str:
    """Return the SHA-256 hash of a string, as 64 hexadecimal characters."""
    return hashlib.sha256(str(text).encode('utf-8')).hexdigest()

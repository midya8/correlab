"""Bounded exact inputs; no float conversion or tolerance."""
from fractions import Fraction as F
import re


def rational(value,name='value'):
    if isinstance(value,bool) or not isinstance(value,(str,int,F)):
        raise ValueError(name+' must be an exact integer, string or Fraction, never float/bool')
    if isinstance(value,str) and (len(value)>160 or not re.fullmatch(r'-?\d+(?:/\d+|\.\d+)?',value)):
        raise ValueError(name+' has invalid exact syntax')
    try:q=F(value)
    except (ValueError,ZeroDivisionError):raise ValueError(name+' is not rational') from None
    if max(abs(q.numerator).bit_length(),q.denominator.bit_length())>512:
        raise ValueError(name+' exceeds 512-bit input components')
    return q


def matrix(payoffs):
    if not isinstance(payoffs,(list,tuple)) or not 1<=len(payoffs)<=4:
        raise ValueError('payoffs needs 1..4 rows')
    if any(not isinstance(r,(list,tuple)) for r in payoffs):raise ValueError('rows must be sequences')
    n=len(payoffs[0])
    if not 1<=n<=4 or any(len(r)!=n for r in payoffs):raise ValueError('payoffs must be rectangular with 1..4 columns')
    return [[rational(a,'payoff') for a in row] for row in payoffs]


def jsonify(value):
    if isinstance(value,F):return str(value)
    if isinstance(value,dict):return {k:jsonify(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [jsonify(v) for v in value]
    return value

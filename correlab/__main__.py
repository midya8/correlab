"""Offline strict JSON CLI: python -m correlab demo|audit FILE|history FILE."""
import argparse,json,sys
from pathlib import Path
from . import audit,history,demo
from .exact import jsonify


def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result:raise ValueError('duplicate JSON key: '+k)
        result[k]=v
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    sub.add_parser('demo')
    for mode in ('audit','history'):sub.add_parser(mode).add_argument('file')
    ns=p.parse_args()
    try:
        if ns.mode=='demo':result=demo()
        else:
            path=Path(ns.file)
            if path.stat().st_size>2_000_000:raise ValueError('input exceeds 2 MB')
            data=json.loads(path.read_text(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
            required={'row_payoffs','column_payoffs',('joint' if ns.mode=='audit' else 'actions')}
            optional=set() if ns.mode=='audit' else {'checkpoints'}
            if not isinstance(data,dict) or not required<=data.keys() or data.keys()-required-optional:
                raise ValueError('wrong input keys')
            result=(audit if ns.mode=='audit' else history)(**data)
        print(json.dumps(jsonify(result),sort_keys=True,indent=2))
    except (ValueError,OSError,TypeError,RecursionError) as e:p.error(str(e))

if __name__=='__main__':main()

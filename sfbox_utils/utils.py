import functools
from itertools import groupby
import itertools
import pathlib
import subprocess
import os
from typing import Dict, List

def ld_to_dl(ld : list, keep_dim = True) -> dict:
    #list of dicts to dict of lists
    dl = {k : [dic[k] for dic in ld if k in dic] for k in functools.reduce(set.union, [set(D.keys()) for D in ld])}
    if keep_dim:
        squeeze = lambda x: x[0] if len(x) == 1 else x
        dl = {k:squeeze(v) for k, v in dl.items()}
    return dl

def dl_to_ld(dl : dict, product = False, repeat_keys = False) -> list:
    only_scalars = {k:v for k,v in dl.items() if not(isinstance(v, list))}
    only_lists = {k:v for k,v in dl.items() if (isinstance(v, list))}

    if not(only_lists):
        return [only_scalars]

    list_lens = [len(v) for v in only_lists.values()]
    if not(all_equal(list_lens)) and not(product):
        raise ValueError("List lengths are not equal")

    if product:
        ld = [{
            k : v for k, v in zip(dl.keys(), values_)
            } for values_ in itertools.product(*only_lists.values())]
    else:
        ld = [dict(zip(only_lists,t)) for t in zip(*only_lists.values())]
    if repeat_keys:
        for d in ld:
            d.update(only_scalars)
    else:
        ld[0].update(only_scalars)
    return ld

def check_int(s : str):
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

def try_cast_to_numeric(s : str, float_only = False):
    if s == 'false' or s == 'False':
        return False
    if s == 'true' or s == 'True':
        return True
    try:
        num = float(s)
    except:
        return s
    if not float_only:
        if check_int(s):
            num = int(s)
    return num

def all_equal(iterable):
    "Returns True if all the elements are equal to each other"
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def check_homogeneous_dtype(iterable, dtype = None):
    if dtype is None:
        types = map(type, iterable)
        return all_equal(types)
    else:
        return all_equal(map(lambda x: isinstance(x, dtype), iterable))

def split_calculations(filename):
    filename = pathlib.Path(filename)
    print(f"Split all calculations in {filename.name} to separate files")
    script_dir = pathlib.Path(__file__).parent
    bash_script = str(script_dir / "scripts" / "split_output.sh")
    subprocess.run(
        [bash_script+f" {filename.name}"],
        shell =True,
        stdout=subprocess.PIPE,
        cwd = filename.parent
        )

def get_number_of_calculations_in_file(filename):
    bashCommand = f"grep 'system delimiter' {str(filename)} | wc -l"
    n = int(subprocess.check_output(bashCommand, shell = True))
    return n

class DictListIterator:
    def __init__(self, dict_of_lists : Dict[str, List]) -> None:
        self.dl = dict_of_lists
        lens = [len(v) for v in self.dl.values()]
        if not all_equal(lens): raise ValueError("All lists length has to be equal")
        self.len = lens[0]

    def __len__(self) -> int:
        return self.len

    def __getitem__(self, key):
        return {k:v[key] for k, v in self.dl.items()}

    #def __setitem__(self, key : int, newvalue : Dict):
    #    if self.dl.keys() != newvalue.keys(): raise ValueError("Dict has to have the same keys")
    #    for k in self.dl.keys():
    #        self.dl[k][key] = newvalue[k]
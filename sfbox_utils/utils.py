import numpy as np
import functools
from itertools import groupby
import itertools
import pathlib
import subprocess
from typing import Dict, List

def ld_to_dl(ld : list, keep_dim = True) -> dict:
    # ist of dicts to dict of lists
    dl = {k : [dic[k] for dic in ld if k in dic] for k in functools.reduce(set.union, [set(D.keys()) for D in ld])}
    if keep_dim:
        squeeze = lambda x: x[0] if len(x) == 1 else x
        dl = {k:squeeze(v) for k, v in dl.items()}
    return dl

def dl_to_ld(dl : dict, product = False, repeat_keys = False) -> list:
    # dict of lists to list of dicts
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
    # check if string is an integer
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

def try_cast_to_numeric(s : str, float_only = False):
    # try to cast to a minimal numeric type, integer or float
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
    # returns True if all the elements are equal to each other
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def check_homogeneous_dtype(iterable, dtype = None):
    # check if all iterables in a collection share the same type
    if dtype is None:
        types = map(type, iterable)
        return all_equal(types)
    else:
        return all_equal(map(lambda x: isinstance(x, dtype), iterable))

def split_calculations(filename):
    # Output files from sfbox may contains results for multiple sequential
    # calculations divided by 'system delimiter' string. The scripts splits the file
    # into multiple ones which contain only one calculation (see split_output.sh). 
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


def read_initial_guess_file(file, reshape = False) -> Dict:
    """Sfbox initial guess file stores scalar and vector values in a text files.
    Function parses sfbox initial guess file into Python dict.
    Scalar parameters are translated into the minimal numeric type 
    float or integer or left as a string.
    Vector parameters are translated into 1d or 2d list 
    of minimal numeric types.

    {   
        scalar_param : scalar_value, 
        vector_param1d : [...], 
        vector_param2d : [[...],[...],...],
        ...
    }
    

    Args:
        file (FileDescriptorOrPath): sfbox initial guess file.
        reshape (bool, optional): If True reshapes the values to 2d list. 
            Defaults to False

    Raises:
        NotImplementedError: initial guess of a format that is not implemented
        ValueError: unexpected keyword read

    Returns:
        dict: parsed initial guess file
    """

    init_guess = open(file)
    line = init_guess.readline().strip()

    ngradients = int(init_guess.readline().strip())

    shape = int(init_guess.readline().strip()), int(init_guess.readline().strip())

    molecules = {}
    line = init_guess.readline().strip()
    while line == "molecule":
        header = [init_guess.readline().strip() for i in range(2)]
        if header != ['all', 'state']:
            raise NotImplementedError("not implemented")
        molecule = init_guess.readline().strip()
        arr_size = shape[0]*shape[1]
        arr = [init_guess.readline().strip() for i in range(arr_size)]
        if reshape:
            arr = np.array(np.reshape(arr, shape), dtype = float)
        else:
            arr = np.array(arr, dtype = float)
        molecules.update({molecule:arr})
        line = init_guess.readline().strip()

    phibulk_solvent = float(init_guess.readline().strip())

    alphabulks = {}
    while line:
        line = init_guess.readline().strip()
        if line=="alphabulk":
            molecule = init_guess.readline().strip()
            val = float(init_guess.readline().strip())
            alphabulks.update({molecule:val})
            continue
        if line == "": continue
        if line is not None:
            raise ValueError("unexpected keyword")

    return_dict = {"state" : molecules, "phibulk solvent" : phibulk_solvent, "alphabulk" : alphabulks, "gradients" : (ngradients, *shape)}

    return return_dict

def write_initial_guess(filename, initial_guess_dict : Dict):
    """Writes sfbox initial guess file

    Args:
        filename (FileDescriptorOrPath): target initial guess file
        initial_guess_dict (dict): initial guess data, provided as a dict
    """

    f = open(filename, 'w')
    def writeline(x):
        f.write(str(x))
        f.write("\n")
    writeline("gradients")
    [writeline(i) for i in initial_guess_dict["gradients"]]
    for molecule, state in initial_guess_dict["state"].items():
        writeline("molecule")
        writeline("all")
        writeline("state")
        writeline(molecule)
        vals = np.ravel(initial_guess_dict["state"][molecule])
        [writeline(v) for v in vals]
    writeline("phibulk solvent")
    writeline(initial_guess_dict["phibulk solvent"])
    for molecule, bulk in initial_guess_dict["alphabulk"].items():
        writeline("alphabulk")
        writeline(molecule)
        writeline(bulk)
    f.write("\n")
import pathlib
from typing import Any, Dict, Union, Callable, List, Optional
import h5py
import numpy as np
import uuid
import functools
import multiprocessing as mp
import shutil

try:
    import tqdm
    _TQDM_TRY_ = tqdm.tqdm
except:
    _TQDM_TRY_ = lambda x, *_, **__: x

from .read_output import parse_file
from .utils import get_number_of_calculations_in_file, split_calculations

ProcessRoutineArgType = Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]
NamingRoutineArgType = Optional[Callable[[Dict[str, Any]], str]]
FieldsArg = Optional[List]
PathType = Union[pathlib.Path, str]

def store_calculation(
    data : dict,
    dir : PathType = None, 
    process_routine : ProcessRoutineArgType = None,
    naming_routine :  NamingRoutineArgType = None
        ):
    
    if dir is None:
        dir = pathlib.Path()
    else:
        dir = pathlib.Path(dir)

    if process_routine is not None:
        data = process_routine(data)

    if naming_routine is not None:
        filename = naming_routine(data)+".h5"
    else:
        filename = str(uuid.uuid4())+".h5"
    filename = pathlib.Path(filename)

    scalars = {k : v for k, v in data.items() if not isinstance(v, np.ndarray)}
    datasets = {k : v for k, v in data.items() if isinstance(v, np.ndarray)}

    h5file = h5py.File(dir/filename, mode = "w")
    
    for k, v in scalars.items():
        #h5file.root._v_attrs.__setattr__(k,v)
        h5file.attrs.create(k,v)

    for k, v in datasets.items():
        #h5file.create_array("/", k, v)
        h5file.create_dataset(name=k, data=v)
    h5file.close()
    return True


def store_file_sequential(
    file : PathType,
    dir : PathType = None, 
    process_routine : ProcessRoutineArgType = None,
    naming_routine :  NamingRoutineArgType = None,
    reader_kwargs : dict = {},
    progress_bar= True,
    ):
    file = pathlib.Path(file)
    if dir is None:
        dir = (file.parent / "h5_files")
        dir.mkdir(parents=True, exist_ok=True)
    else:
        dir = pathlib.Path(dir)
    reader = parse_file(file, **reader_kwargs)
    n_calculations = get_number_of_calculations_in_file(file)
    if progress_bar:
        print(f"{n_calculations} calculation(s) in {file.name}...")
        for calculation in _TQDM_TRY_(reader, total = n_calculations):
            store_calculation(
                data = calculation, 
                dir = dir, 
                process_routine = process_routine, 
                naming_routine = naming_routine,
                )
    else:
        for calculation in reader:
            store_calculation(
                data = calculation, 
                dir = dir, 
                process_routine = process_routine, 
                naming_routine = naming_routine,
                )


def store_files_parallel(
        files,
        dir : PathType = None, 
        process_routine : ProcessRoutineArgType = None,
        naming_routine :  NamingRoutineArgType = None,
        n_jobs = 4,
        reader_kwargs = {}
    ):

    file = pathlib.Path(files[0])
    if dir is None:
        dir = (file.parent / "h5_files")
        dir.mkdir(parents=True, exist_ok=True)
    else:
        dir = pathlib.Path(dir)

    partial_kwargs = dict(
        dir = dir, 
        process_routine = process_routine,
        naming_routine = naming_routine,
        reader_kwargs = reader_kwargs
        )

    with mp.Pool(n_jobs) as pool:
        list(_TQDM_TRY_(
            pool.imap_unordered(functools.partial(store_file_sequential, **partial_kwargs, progress_bar = False), files),
            total=len(files)
        ))

    
def store_file_parallel(
        file : PathType,
        dir : PathType = None, 
        process_routine : ProcessRoutineArgType = None,
        naming_routine :  NamingRoutineArgType = None,
        n_jobs = 4,
        reader_kwargs = {}
    ):
    file = pathlib.Path(file)
    if dir is None:
        dir = (file.parent / "h5_files")
        dir.mkdir(parents=True, exist_ok=True)
    else:
        dir = pathlib.Path(dir)
    
    split_calculations(file)
    
    temp_dir= file.parent / (file.stem+"_tmp")
    files = list(temp_dir.glob("*.out"))

    store_files_parallel(
        files=files, 
        dir=dir, 
        process_routine = process_routine, 
        naming_routine = naming_routine, 
        n_jobs = n_jobs, 
        reader_kwargs = reader_kwargs
        )

    shutil.rmtree(temp_dir)


def add_external_link(
    destination : Union[PathType, h5py.File], 
    source : PathType, 
    name : str = None,
    ):
    close_before_exit = False

    destination = pathlib.Path(destination)
    source = pathlib.Path(source)
    #source = source.relative_to(destination)
    
    if name is None:
        name = source.stem
    
    print(source, name)
    
    if not isinstance(destination, h5py.File):
        destination = h5py.File(destination, mode = "a")
        close_before_exit = True
    
    destination[name] = h5py.ExternalLink(source, "/")

    if close_before_exit:
        destination.close()
    

def create_master_table(
        dir : Union[pathlib.Path, str] = None,
        pandas = True
    ):
    if dir is None:
        dir = pathlib.Path()
    else:
        dir = pathlib.Path(dir)
    h5files = dir.glob("*.h5")

    rows = []
    for f in h5files:
        file = h5py.File(f)
        row = dict(file.attrs.items())
        row.update({"h5file" : str(f), "keys" : list(file.keys())})
        rows.append(row)
        file.close()
    if pandas:
        import pandas as pd
        return pd.DataFrame(rows)
    else:
        return rows

def load_dataset(file, key):
    file = h5py.File(file)
    data = np.array(file[key])
    file.close()
    return data
import pathlib
from typing import Any, Dict, Union, Callable, List, Optional
import h5py
import numpy as np
import uuid
import functools
import multiprocessing as mp
import shutil
from datetime import datetime
import logging
import sys

logging.basicConfig(stream=sys.stdout)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

try:
    import tqdm
    import tqdm.autonotebook
    _TQDM_TRY_ = tqdm.autonotebook.tqdm
    from tqdm.contrib.logging import logging_redirect_tqdm
    class TqdmLoggingHandler(logging.Handler):
        def __init__(self, level=logging.NOTSET):
            super().__init__(level)

        def emit(self, record):
            try:
                msg = self.format(record)
                tqdm.tqdm.write(msg)
                self.flush()
            except Exception:
                self.handleError(record)  
    log.addHandler(TqdmLoggingHandler())
    _TQDM_FOUND_ = True
    
except ModuleNotFoundError:
    _TQDM_TRY_ = lambda x, *_, **__: x
    import contextlib
    logging_redirect_tqdm = contextlib.nullcontext
    _TQDM_FOUND_ = False



from .read_output import parse_file
from .utils import get_number_of_calculations_in_file, split_calculations

ProcessRoutineArgType = Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]
NamingRoutineArgType = Optional[Callable[[Dict[str, Any]], str]]
FieldsArg = Optional[List]
PathType = Union[pathlib.Path, str]

on_file_exist_parameters = ["rename", "raise", "rewrite", "add_timestamp", "keep"]
on_process_ignore_parameters = ["ignore", "raise"]

def store_calculation(
    data : dict,
    dir : PathType = None, 
    process_routine : ProcessRoutineArgType = None,
    naming_routine :  NamingRoutineArgType = None,
    on_file_exist : str = "rename",
    on_process_error : str = "raise",
    suffix : str = ".h5"
        ):
    
    if on_file_exist not in on_file_exist_parameters:
        raise ValueError(f"Invalid value for the action when the file is already exists\n Possible values: {on_file_exist_parameters}")
    if on_process_error not in on_process_ignore_parameters:
        raise ValueError(f"Invalid value for the action when the process routine fails\n Possible values: {on_process_error}")

    if dir is None:
        dir = pathlib.Path()
    else:
        dir = pathlib.Path(dir)

    if process_routine is not None:
        if on_process_error == "ignore":
            try:
                data = process_routine(data)
            except Exception as e:
                log.error(f"Process routine raised an error {e}, the calculation is skipped")
                return False
        else:
            data = process_routine(data)

    if naming_routine is not None:
        filename = naming_routine(data)+suffix
    else:
        #if no naming routine provided fallback to uuid
        filename = str(uuid.uuid4())+suffix
    filename = pathlib.Path(filename)

    is_file_exists = (dir/filename).is_file()
    mode = "w"
    if is_file_exists:
        msg_header = f"File {filename} already exists"
        
        if on_file_exist == "rename":
            i = 0
            while is_file_exists:
                filename = filename.with_stem(str(filename.stem)+f"_{i}")
                i = i+1
                is_file_exists = (dir/filename).is_file()
            log.warning(f"{msg_header}, the file will be renamed to {filename}")

        elif on_file_exist=="add_timestamp":
            timestamp = datetime.now()
            filename = filename.with_stem(str(filename.stem)+f"_{timestamp}")
            log.warning(f"{msg_header}, the file will be renamed to {filename}")

        elif on_file_exist=="rewrite":
            log.warning(f"{msg_header}, the file will be rewritten")
            pass

        elif on_file_exist=="raise":
            log.error(f"{msg_header}, error will be raised")
            mode = "x"

        elif on_file_exist == "keep":
            log.warning(f"{msg_header}, previous version will be kept")
            return True

    h5file = h5py.File(dir/filename, mode = mode)
    log.info(f"File {filename} is created")


    scalars = {k : v for k, v in data.items() if not isinstance(v, np.ndarray)}
    datasets = {k : v for k, v in data.items() if isinstance(v, np.ndarray)}
    
    for k, v in scalars.items():
        h5file.attrs.create(k,v)

    for k, v in datasets.items():
        h5file.create_dataset(name=k, data=v)
    h5file.close()
    return True


def store_file_sequential(
    file : PathType,
    dir : PathType = None, 
    process_routine : ProcessRoutineArgType = None,
    naming_routine :  NamingRoutineArgType = None,
    reader_kwargs : dict = {},
    on_file_exist : str = "rename",
    on_process_error : str = "raise",
    suffix : str = ".h5"
    ):
    file = pathlib.Path(file)
    if dir is None:
        dir = (file.parent / "h5_files")
        dir.mkdir(parents=True, exist_ok=True)
    else:
        dir = pathlib.Path(dir)
    reader = parse_file(file, **reader_kwargs)
    n_calculations = get_number_of_calculations_in_file(file)
    if n_calculations>1:
        with logging_redirect_tqdm():
            log.info(f"{n_calculations} calculation(s) in {file.name}...")
            for calculation in _TQDM_TRY_(reader, total = n_calculations, position=0, leave=True):
                store_calculation(
                    data = calculation, 
                    dir = dir, 
                    process_routine = process_routine, 
                    naming_routine = naming_routine,
                    on_file_exist = on_file_exist,
                    on_process_error = on_process_error,
                    suffix = suffix
                    )
    else:
        for calculation in reader:
                store_calculation(
                    data = calculation, 
                    dir = dir, 
                    process_routine = process_routine, 
                    naming_routine = naming_routine,
                    on_file_exist = on_file_exist,
                    on_process_error = on_process_error,
                    suffix = suffix
                    )


def store_files_parallel(
        files,
        dir : PathType = None, 
        process_routine : ProcessRoutineArgType = None,
        naming_routine :  NamingRoutineArgType = None,
        n_jobs = 4,
        reader_kwargs = {},
        on_file_exist : str = "rename",
        on_process_error : str = "raise",
        suffix : str = ".h5",
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
        reader_kwargs = reader_kwargs,
        on_file_exist = on_file_exist,
        on_process_error = on_process_error,
        suffix = suffix
        )
    if _TQDM_FOUND_: pbar = tqdm.autonotebook.tqdm(total=len(files), leave=True)
    with logging_redirect_tqdm():
        with mp.Pool(n_jobs) as pool:
            for _ in pool.imap_unordered(functools.partial(store_file_sequential, **partial_kwargs), files):
                if _TQDM_FOUND_: pbar.update(1)
    if _TQDM_FOUND_: pbar.close()
        

    
def store_file_parallel(
        file : PathType,
        dir : PathType = None, 
        process_routine : ProcessRoutineArgType = None,
        naming_routine :  NamingRoutineArgType = None,
        n_jobs = 4,
        reader_kwargs = {},
        on_file_exist : str = "rename",
        on_process_error : str = "raise",
        suffix : str = ".h5",
    ):
    file = pathlib.Path(file)
    if dir is None:
        dir = (file.parent / "h5_files")
        dir.mkdir(parents=True, exist_ok=True)
    else:
        dir = pathlib.Path(dir)
    
    n_calculations = get_number_of_calculations_in_file(file)
    log.info(f"{n_calculations} calculation(s) in {file.name}...")

    split_calculations(file)
    
    temp_dir= file.parent / (file.stem+"_tmp")
    files = list(temp_dir.glob("*.out"))

    store_files_parallel(
        files=files, 
        dir=dir, 
        process_routine = process_routine, 
        naming_routine = naming_routine, 
        n_jobs = n_jobs, 
        reader_kwargs = reader_kwargs,
        on_file_exist = on_file_exist,
        on_process_error = on_process_error,
        suffix = suffix,
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
    
    log.debug(source, name)
    
    if not isinstance(destination, h5py.File):
        destination = h5py.File(destination, mode = "a")
        close_before_exit = True
    
    destination[name] = h5py.ExternalLink(source, "/")

    if close_before_exit:
        destination.close()

            
from .reference_table import *
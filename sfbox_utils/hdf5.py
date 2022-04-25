import pathlib
from typing import Any, Dict, Union, Callable, List, Optional
import h5py
import numpy as np
import logging

logger = logging.getLogger(__name__)

from .read_output import parse_file

RoutineArgType = Optional[Callable[[Dict[str, Any]], Dict[str, Any]]]
FieldsArg = Optional[List]

def store_calculation_result(
    hdf_group : h5py.Group, 
    data : dict, 
    process_routine : RoutineArgType = None
        ):
    
    if process_routine is not None:
        logger.debug("routine called")
        data = process_routine(data)

    for k, v in data.items():
        if isinstance(v, np.ndarray):
            hdf_group.create_dataset(k, data = v)
        else:
            hdf_group.attrs.create(k, v)

def store_file(
    hdf_group : h5py.Group, 
    groupname : str, 
    reader, 
    process_routine : RoutineArgType = None,
        ):
    
    i=0
    new_groupname = groupname
    #resolve conflict if the same group already exists
    while True:
        if new_groupname in hdf_group: 
            new_groupname = groupname + f"_{i}"
            i = i+1
        else:
            break
    if new_groupname != groupname:
        logger.warning("Group name already exist, new name assigned")
    
    g = hdf_group.create_group(new_groupname)

    for i, data in enumerate(reader):
        gg = g.create_group(str(i))
        store_calculation_result(gg, data, process_routine)

    logger.info("File is stored in hdf5 database")

def store_files(
            dir : Union[str,pathlib.Path], 
            hdf_group : h5py.Group, 
            ignore_fields : FieldsArg = None, 
            read_fields : FieldsArg = None,
            read_fields_regex : FieldsArg = None,
            process_routine : RoutineArgType = None,
        ):
    if process_routine is not None:
        logger.debug("routine passed as arg")
    for file in pathlib.Path(dir).glob("*.out"):
        reader = parse_file(file,
            read_fields_regex = read_fields_regex, 
            read_fields = read_fields,
            ignore_fields = ignore_fields
            )
        store_file(hdf_group, file.stem, reader, process_routine)
    
    logger.info("All files are stored in hdf5 database")
        


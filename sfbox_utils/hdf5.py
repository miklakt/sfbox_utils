import pathlib
from typing import Union, Callable, List
import h5py
import numpy as np
import logging
logger = logging.getLogger(__name__)

from .read_output import parse_file

def store_calculation_result(hdf_group : h5py.Group, data : dict, process_routine : Callable = None):
    
    if process_routine is not None:
        logger.debug("routine called")
        data = process_routine(data)

    for k, v in data.items():
        if isinstance(v, np.ndarray):
            hdf_group.create_dataset(k, data = v)
        else:
            hdf_group.attrs.create(k, v)

def store_file(hdf_group : h5py.Group, groupname : str, reader, process_routine):
    i=0
    new_groupname = groupname
    #resolve conflict if the same group already exists
    while True:
        if new_groupname in hdf_group: 
            new_groupname = groupname + "_{i}"
            i = i+1
        else:
            break
    if new_groupname != groupname:
        logger.warning("Group name already exist, new name assigned")
    
    g = hdf_group.create_group(new_groupname, process_routine)

    for i, data in enumerate(reader):
        gg = g.create_group(str(i))
        store_calculation_result(gg, data)

    logger.info("File is stored in hdf5 database")

def store_files(
            dir : Union[str,pathlib.Path], 
            hdf_group : h5py.Group, 
            ignore_fields = None, 
            read_fields = None,
            read_fields_regex = None,
            process_routine = None,
        ):
    for file in pathlib.Path(dir).glob("*.out"):
        reader = parse_file(file, read_fields, 
            read_fields_regex = read_fields_regex, 
            read_fields = read_fields,
            ignore_fields = ignore_fields
            )
        store_file(hdf_group, file.stem, reader, process_routine)
    
    logger.info("All files are stored in hdf5 database")
        


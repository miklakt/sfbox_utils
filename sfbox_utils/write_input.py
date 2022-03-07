import pathlib
from typing import Union, List, Dict
import itertools
import logging
logger = logging.getLogger(__name__)

from .utils import dl_to_ld

def write_input_file(filename : Union[str, pathlib.Path], data :  Union[Dict, List[Dict]], product = False) -> bool:

    if isinstance(data, Dict):
        data = dl_to_ld(data, product=product, repeat_keys=False)

    if pathlib.Path(filename).is_file():
        logger.warning("File exist and will be rewritten")

    logger.info(
                f"File {filename} is opened to create an sfbox input")
    f = open(filename, mode='w')
    
    for i, d in enumerate(data):
        for k,v in d.items():
            
            #boolean to string
            if v is False:
                v = 'false'
            elif v is True:
                v = 'true'
            
            f.write(f'{k}:{v}\n')
        f.write('start\n')
        logger.info(
            f"Calculation number {i} is appended to file {filename}")
    logger.info(
            f"File {filename} is closed")
    f.close()

    return True

def write_input_files(
    filenames : Union[List[str], List[pathlib.Path], str], 
    data : List, 
    **kwargs
    ):

    if isinstance(filenames, str):
        # generate input file names based on json_file name
        filenames = [f'{filenames}_{i}.in' for i in range(len(data))]

    for filename, datum in zip(filenames, data):
        write_input_file(filename, datum, **kwargs)
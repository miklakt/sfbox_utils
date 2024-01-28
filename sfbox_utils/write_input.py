import pathlib
from typing import Union, List, Dict
import itertools
import logging
logger = logging.getLogger(__name__)

from .utils import dl_to_ld

def write_input_file(filename : Union[str, pathlib.Path], data :  Union[Dict, List[Dict]], product = False) -> bool:
    """Write input file with provided list of dicts or dict of lists. 
    Writes multiple calculations to one file. 
    One can define sequential calculations either providing list of dicts 
    or dicts with a list as an element or elements

    Args:
        filename (str | pathlib.Path): name of the file to be created
        data (dict | list[dict]): statements to write to the file
        product (bool, optional): if multiple elements in the data are list, write all the combinations possible

    Returns:
        bool: True if successful
    """    

    if isinstance(data, Dict):
        data = dl_to_ld(data, product=product, repeat_keys=False)

    if pathlib.Path(filename).is_file():
        logger.warning("File exist and will be rewritten")

    logger.info(
                f"File {filename} is opened to create an sfbox input")
    f = open(filename, mode='w')
    
    for i, d in enumerate(data):
        for k,v in d.items():
            if not isinstance(v, list): v = [v]
            for v_ in v:
                #boolean to string
                if v_ is False:
                    v_ = 'false'
                elif v_ is True:
                    v_ = 'true'
                f.write(f'{k}:{v_}\n')
                
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
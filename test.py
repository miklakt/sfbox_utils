#%%
import sfbox_utils
import pathlib
import h5py
import logging
import numpy as np
import sys
import time
from sfbox_utils.call import sfbox_calls_sh
from sfbox_utils.utils import get_number_of_calculations_in_file, split_calculations

from sfbox_utils.store import store_file_parallel, store_file_sequential, create_master_table, load_dataset

#%%
def process(data):
    xlayers = data["lat:2G:n_layers_x"]
    ylayers = data["lat:2G:n_layers_y"]
    chi = data["chi list:S:chi - P"]
    filename = pathlib.Path(data["sys:noname:inputfile"]).name
    phi = data["mon:P:phi:profile"].reshape(xlayers+2, ylayers+2)
    phi_0 = data["mon:P0:phi:profile"].reshape(xlayers+2, ylayers+2)
    for i in range(1000000):
        for j in range(100):
            pass
    return {
        "xlayers" : xlayers, 
        "ylayers" : ylayers, 
        "chi" : chi, 
        "phi" : phi,
        "phi_0" : phi_0, 
        "filename" : filename
        }

def naming(data):
    return f"{data['filename']}_chi_{data['chi']}"

# %%
#t = time.time()
files = list(pathlib.Path("test").glob("*.out"))
#%%
store_file_parallel(
    file = "test/test_input_0.out",
    process_routine=process,
    naming_routine=naming,
    reader_kwargs=dict(
        read_fields=[
                    "mon : P : phi : profile",
                    "sys : noname : free energy",
                    "chi list : S : chi - P",
                    "sys : noname : inputfile",
                ],
        read_fields_regex=[
                    "mon : P[0-9] : phi : profile", 
                    "lat : 2G : n_layers"
                ]
        )
    )
# %%
data = create_master_table(dir = "test/h5_files")
filename = data.query("chi == 0.3").h5file.squeeze()
load_dataset(filename, "phi")
# %%
from sfbox_utils.store import add_external_link
add_external_link("test/master.h5", "test/h5_files/test_input_0.in_chi_0.0.h5")
# %%
file = h5py.File("test/master.h5", "r+")
# %%

# %%

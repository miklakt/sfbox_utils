# usually it is what we need
# comment if working directory is different from script directory
import sys, os
os.chdir(sys.path[0])
import pathlib

from sfbox_utils.store import create_reference_table, store_files_parallel, store_file_parallel
# import logging
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# in the process function user has to provide how to process sfbox output data
# the result has to be stored in a dict
# provided function processes every calculation one by one or in parallel
def process(data):
    xlayers = data["lat:2G:n_layers_x"]
    ylayers = data["lat:2G:n_layers_y"]
    chi = data["chi list:S:chi - P"]
    chi_PC = data["chi list:P:chi - C"]
    filename = pathlib.Path(data["sys:noname:inputfile"]).name
    phi = data["mon:P:phi:profile"].reshape(xlayers+2, ylayers+2)
    phi_0 = data["mon:P0:phi:profile"].reshape(xlayers+2, ylayers+2)
    fe = data["sys:noname:free energy"]
    # Make it slower for testing
    # for i in range(1000000):
    #     for j in range(100):
    #         pass
    return {
        "xlayers" : xlayers, 
        "ylayers" : ylayers, 
        "chi" : chi,
        "chi_PC" : chi_PC, 
        "phi" : phi,
        "phi_0" : phi_0, 
        "filename" : filename,
        "free_energy" : fe,
        }

# in the process function user must describe how to name each calculation
# preferably in a unique way, based on the processed calculation result
def naming(data):
    return f"{data['filename']}_chi_{data['chi']}_chi_PC_{data['chi_PC']}"

# additional reader arguments
reader_kwargs=dict(
        # explicitly define which parameters to read from the output files
        read_fields=[
                    "mon : P : phi : profile",
                    "sys : noname : free energy",
                    "sys : noname : inputfile",
                ],
        # parameters that pass any regex is to be read
        read_fields_regex=[
                     "chi list : (.*?)",
                     "mon : P[0-9] : phi : profile", 
                     "lat : 2G : n_layers"
                 ]
        )

# search for all sfbox output files
files = list(pathlib.Path().glob("*.out"))

# store file/files each calculation into separate hdf5 file
store_files_parallel(
    files = files,
    process_routine=process,
    naming_routine=naming,
    reader_kwargs=reader_kwargs,
    # rewrite if a calculation with this name exists
    on_file_exist="rewrite"
    )

# processed data across all calculation gathered into one table
# each row is a sfbox calculation
# scalar parameters are stored in table cells
# vector values are referenced to hdf5 file
reference_tbl = create_reference_table(storage_dir = "h5_files")
reference_tbl.to_pickle("test_sfbox_reference.pkl")
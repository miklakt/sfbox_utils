import pathlib
from typing import Any, Dict, Union, Callable, List, Optional
import h5py
import numpy as np
from datetime import datetime

def create_reference_dict(
        dir : Union[pathlib.Path, str] = None,
    ):
    if dir is None:
        dir = pathlib.Path()
    else:
        dir = pathlib.Path(dir)
    h5files = dir.glob("*.h5")

    rows = []
    for f in h5files:
        creation_time = datetime.fromtimestamp(f.stat().st_ctime) 
        file = h5py.File(f)
        row = dict(file.attrs.items())
        row.update({"h5file" : str(f), "keys" : list(file.keys()), "creation_time" : creation_time})
        rows.append(row)
        file.close()
    return rows

try:
    import pandas as pd
    def create_reference_table(storage_dir = "h5", load_inplace = False):        
        
        class H5StorageAccessor:
            def __init__(self, pandas_obj):
                self._obj = pandas_obj

            @staticmethod
            def _validate(obj):
                if not all(col in obj.columns for col in ['h5file','keys']):
                    raise AttributeError("Columns must include 'h5file', 'keys'")
                
            @staticmethod
            def load_dataset(file, key):
                file = h5py.File(file)
                if isinstance(key, list):
                    data = [np.array(file[k]) for k in key]
                else:
                    data = np.array(file[key])
                file.close()
                return data
                
            def __getitem__(self, keys):
                if not isinstance(keys, list):
                    keys = [keys]
                if load_inplace:
                    df = self._obj
                else:
                    df = pd.DataFrame(columns=keys)

                for key in keys:
                    df[key] = np.nan
                    df[key] = df[key].astype(object)
                    df[key] = df.apply(lambda _: H5StorageAccessor.load_dataset(_.h5file, f"/{key}"), axis=1)
                
                return df[keys]
        pd.api.extensions.register_dataframe_accessor("dataset")(H5StorageAccessor)

        class H5StorageAccessorSeries(H5StorageAccessor):
            def __getitem__(self, keys):
                if not isinstance(keys, list):
                    keys = [keys]
                if load_inplace:
                    df = self._obj
                else:
                    df = pd.Series(index=keys)
                for key in keys:
                    df[key] = H5StorageAccessor.load_dataset(df.h5file, f"/{key}")
                
                return df[keys]
        pd.api.extensions.register_series_accessor("dataset")(H5StorageAccessorSeries)
            
        dataframe = pd.DataFrame(create_reference_dict(storage_dir))
        return dataframe
            
except ModuleNotFoundError:
    pass
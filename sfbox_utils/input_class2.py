#%%
from typing import Any, Dict, List, Callable
import inspect

class AlwaysNoneIterable:
    def __iter__(self):
        while True:
            yield None

class DictTracker:
    def __init__(self):
        self.accessed_keys = set()
        self.set_keys = set()

    def __getitem__(self, key):
        self.accessed_keys.add(key)
        return None

    def __setitem__(self, key, value):
        self.set_keys.add(key)

    def __delitem__(self, key):
        del self.data[key]

    def update(self, other_dict):
        if isinstance(other_dict, DictTracker):
            self.accessed_keys.update(other_dict.accessed_keys)
            self.set_keys.update(other_dict.set_keys)
        elif isinstance(other_dict, dict):
            self.set_keys.update(other_dict.keys())
        else:
            raise TypeError("Unsupported type for update")

    def keys(self):
        return list()

    def values(self):
        return list()

    def items(self):
        return list()
    
class AttributeTracker:
    def __init__(self):
        self.accessed_attributes = set()

    def __getattr__(self, name):
        self.accessed_attributes.add(name)
        return None

    
def inspect_dependency(dependency : Callable):
    signature = inspect.signature(dependency)
    arguments = {}
    #dependent_fields= set()
    #dependent_attr = set()
    #precedent = []
    for arg in signature.parameters.values():
        if arg.name == "_field":
            print("Dependency access fields")
            _tracker = DictTracker()
            dependency(_tracker, AlwaysNoneIterable())
            dependent = list(_tracker.set_keys)
        else:
            val = arg.default
            if val == inspect._empty: val = None
            arguments.update({arg.name : val})
    return dependent, arguments

def _update_dict_no_None(main_dict, other_dict):
    for key, value in other_dict.items():
        if value is not None:
            main_dict[key] = value
        elif key not in main_dict:
            main_dict[key] = None


class TaskClass:
    def __init__(self, fields = {}) -> None:
        self.fields = fields
        self.user_dependencies = []
        self.user_variables = {}

    def add_dependency(self, dependency : Callable):
        dependent_field, variables = inspect_dependency(dependency)
        _update_dict_no_None(self.user_variables, variables)

    
    


#%%
fields = {
  'lat:1G:geometry': 'spherical',
  'lat:1G:gradients': 1,
  'lat:1G:lambda': 0.16666666666666666,
  'lat:1G:n_layers': '_',
  'mon:pao:freedom': 'free',
  'mon:pa:freedom': 'free',
  'mon:pae:freedom': 'free',
  'mon:pbo:freedom': 'free',
  'mon:pb:freedom': 'free',
  'mon:pbe:freedom': 'free',
  'mol:diblock:composition': '(pae)1(pa)98(pao)1(pbo)1(pb)98(pbe)1',
  'mol:diblock:freedom': 'restricted',
  'mol:diblock:theta': 0.1,
  'mon:S:freedom': 'free',
  'mol:solvent:freedom': 'solvent',
  'mol:solvent:composition': 'S',
  'mon:pao:chi - S': '_',
  'mon:pa:chi - S': '_',
  'mon:pae:chi - S': '_',
  'mon:pbo:chi - S': '_',
  'mon:pb:chi - S': '_',
  'mon:pbe:chi - S': '_',
  'newton:isaac:method': 'pseudohessian',
  'newton:isaac:tolerance': 1e-08,
  'output:filename.out:type': 'ana',
  'output:filename.out:write_profiles': True,
  'output:filename.out:append': False,
  'output:filename.out:write_bounds': False
}

aliases = dict(
        nlayers = "lat:1G:n_layers",
        phibulk = "mol:diblock:phibulk",
        method = "newton:isaac:method",
        tolerance = 'newton:isaac:tolerance',
        composition = 'mol:diblock:composition'
    )

def set_chi_AS(_):
    _['mon:pao:chi - S'] = _.chi_AS
    _['mon:pa:chi - S'] = _.chi_AS
    _['mon:pae:chi - S'] = _.chi_AS

def set_chi_BS(_):
    _['mon:pbo:chi - S'] = _.chi_BS
    _['mon:pb:chi - S'] = _.chi_BS
    _['mon:pbe:chi - S'] = _.chi_BS

def set_composition(_):
   _.composition =  f"(pae)1(pa){_.NA-2}(pao)1(pbo)1(pb){_.NB-2}(pbe)1"

def get_N(_):
    _.N = _.NA + _.NB

# properties = dict(
#     chi_AS = [get_chi_AS, set_chi_AS, del_chi_AS]
# )
#%%
inspect_dependency(set_chi_AS)

# %%

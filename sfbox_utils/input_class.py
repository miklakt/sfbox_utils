#%%
from typing import Any, Dict, List, Callable
import inspect

def create_task_item(
        properties = {}, 
        fields = {},
        **user_attributes
        ):
    
    class TaskItemClass(Dict):
        def __init__(self):
            self.update(fields)
            self.properties = list(properties.keys())
            self.attributes = {}
            # if user_attributes:
            #     self.attributes = user_attributes

        def __str__(self) -> str:
            s = "".join(f"{field}:{value}\n" for field, value in self.items())
            return s
        
        def __repr__(self) -> str:
            return super().__repr__() + "\nattributes: " +str(self.attributes)
        
        def __getattribute__(self, __name: str) -> Any:
            if __name in user_attributes:
                return self.attributes[__name]
            else:
                #fallback to default behavior
                return super().__getattribute__(__name)
        
        def __setattr__(self, __name: str, __value: Any) -> None:
            if __name in user_attributes:
                self.attributes[__name] = __value
            else:
                #fallback to default behavior
                return super().__setattr__(__name, __value)
            
            
        def add_property(
                self,
                name : str, 
                getter : str|Callable = None, 
                setter : str|Callable = None, 
                deleter : str|Callable = None, 
                doc : str = None
                ):
            if isinstance(getter, str):
                def fget(self_):
                    return self_[getter]
            else:
                fget = getter

            if isinstance(setter, str):
                def fset(self_, value):
                    self_[name]=value
            else:
                fset = setter
                signature = inspect.signature(setter)
                for arg in signature.parameters.values():
                    if arg.name == "_": continue
                    print(arg.name, arg.default)
                    
            if isinstance(deleter, str):
                def fdel(self_):
                    del self_[name]
            else:
                fdel = deleter
            
            if doc is None:
                doc = f"'{name}' defined with getter" + (", setter", "")[setter is None] +  (", deleter", "")[deleter is None] + "."

            prop = property(fget, fset, fdel, doc)
            setattr(self.__class__, name, prop)
            print(doc)
    
        def add_alias(self, key, field):
            doc = f"'{key}' is an alias for '{field}'"
            self.add_property(key, field, field, field, doc)

    task = TaskItemClass()
    for prop_name, handlers in properties.items():
        if isinstance(handlers, (list, tuple)):
            task.add_property(prop_name, *handlers)
        elif isinstance(handlers, dict):
            task.add_property(prop_name, **handlers)
        elif isinstance(handlers, str):
            task.add_alias(prop_name, handlers)
            

    return TaskItemClass()

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
    )

get_chi_AS = 'mon:pa:chi - S'

def set_chi_AS(field, chi_AS):
    field['mon:pao:chi - S'] = chi_AS
    field['mon:pa:chi - S'] = chi_AS
    field['mon:pae:chi - S'] = chi_AS

def del_chi_AS(field):
    del field['mon:pao:chi - S']
    del field['mon:pa:chi - S']
    del field['mon:pae:chi - S']

get_composition = 'mol:diblock:composition'
del_composition = 'mol:diblock:composition'
def set_composition(field, NA, NB=100):
    field.composition =  f"(pae)1(pa){NA-2}(pao)1(pbo)1(pb){NB-2}(pbe)1"

properties = dict(
    chi_AS = [get_chi_AS, set_chi_AS, del_chi_AS]
)
#%%
task = create_task_item(
    properties=aliases|properties,
    fields=fields,
    NA = 100, NB = 100,
    )
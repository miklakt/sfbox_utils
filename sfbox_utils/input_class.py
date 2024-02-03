from typing import Dict, List, Callable
from .read_input import parse_file
class InputItemClass(Dict):
    def __init__(self, fields ={}, properties = {}):
        self.update(fields)
        self.properties = properties

        for prop_name, handlers in self.properties.items():
            if isinstance(handlers, (list, tuple)):
                self.add_property(prop_name, *handlers)
            elif isinstance(handlers, dict):
                self.add_property(prop_name, **handlers)
            elif isinstance(handlers, str):
                self.add_alias(prop_name, handlers)

    def __str__(self) -> str:
        s = ""
        for k, v in self.items():
            if not isinstance(v, list): v = [v]
            
            for v_ in v:
                #boolean to string
                if v_ is False:
                    v_ = 'false'
                elif v_ is True:
                    v_ = 'true'
                s = s+ f'{k}:{v_}\n'
        return s
            
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
                self_[setter]=value
        else:
            fset = setter
                
        if isinstance(deleter, str):
            def fdel(self_):
                del self_[deleter]
        else:
            fdel = deleter
        
        if doc is None:
            doc = f"'{name}' defined with getter" + (", setter", "")[setter is None] +  (", deleter", "")[deleter is None] + "."

        prop = property(fget, fset, fdel, doc)
        setattr(self.__class__, name, prop)
        #print(doc)

    def add_alias(self, key, field):
        doc = f"'{key}' is an alias for '{field}'"
        self.add_property(key, field, field, field, doc)
class InputListClass(List):
    def __init__(
            self, 
            fields:dict = {}, 
            properties:dict = {}, 
            filename:str = None
            ):
        if fields and filename: raise AttributeError("Pass either fields or file")
        if not(fields): fields = InputListClass.__readfile(filename)
        self.properties = properties
        super().__init__(InputItemClass(item, self.properties) for item in fields)

    def __readfile(filename):
        return parse_file(filename)

    def __setitem__(self, index, item):
        if not isinstance(item, type(self)):
            item = InputItemClass(item, self.properties)
        #auto enlarge
        if index == len(self):
            print("Out of range, list is resized")
            self.append(item)
        else:
            super().__setitem__(index, item)

    def __getitem__(self, index):
        if index == len(self) and not(self[-1] == {}):
            print("Out of range, list is resized")
            self.append(InputItemClass({}, self.properties))
            return self.__getitem__(index)
        else:
            return super().__getitem__(index)


    def insert(self, index, item):
        if not isinstance(item, type(self)):
            item = InputItemClass(item, self.properties)
        super().insert(index, item)

    def append(self, item):
        if not isinstance(item, type(self)):
            item = InputItemClass(item, self.properties)
        super().append(item)

    def extend(self, other):
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            super().extend(InputItemClass(item, self.properties) for item in other)

    def __str__(self) -> str:
        s = "start\n".join(f"{item}" for item in self) + "start\n"
        return s
    
    def writefile(self, filename):
        with open(filename, "w") as f:
            f.writelines(str(self))
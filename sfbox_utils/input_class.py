from typing import Dict, List, Callable
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
        s = "".join(f"{field}:{value}\n" for field, value in self.items())
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
                self_[name]=value
        else:
            fset = setter
                
        if isinstance(deleter, str):
            def fdel(self_):
                del self_[name]
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
    def __init__(self, fields={}, properties={}):
        self.properties = properties
        super().__init__(InputItemClass(item, self.properties) for item in fields)

    def __setitem__(self, index, item):
        if not isinstance(item, type(self)):
            item = InputItemClass(item, self.properties)
        super().__setitem__(index, item)

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
        s = "start\n".join(f"{item}" for item in self)
        return s
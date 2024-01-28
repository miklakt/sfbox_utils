from typing import Dict, List, Callable
class TaskItemClass(Dict):
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
        print(doc)

    def add_alias(self, key, field):
        doc = f"'{key}' is an alias for '{field}'"
        self.add_property(key, field, field, field, doc)
class InputClass(List):
    def __init__(self, fields, properties):
        super().__init__(TaskItemClass(item, properties) for item in fields)

    def __setitem__(self, index, item):
        super().__setitem__(index, TaskItemClass(item))

    def insert(self, index, item):
        super().insert(index, TaskItemClass(item))

    def append(self, item):
        super().append(TaskItemClass(item))

    def extend(self, other):
        if isinstance(other, type(self)):
            super().extend(other)
        else:
            super().extend(TaskItemClass(item) for item in other)

    def __str__(self) -> str:
        s = "start\n".join(f"{item}" for item in self)
        return s
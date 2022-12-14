import logging
from functools import partial

import dill
import zerorpc


class Client:
    def __init__(self, host, port):
        self.client = zerorpc.Client()
        self.client.connect("tcp://{}:{}".format(host, port))

    def searchtext(self, field, query):
        return self.client.searchtext(field, query)

    def search(self, where):
        lamd = dill.dumps(where)
        return self.client.search(lamd)

    def proxy(self, path):
        file = self.getobject(path, False)
        method_list = [
            attribute
            for attribute in dir(type(file))
            if callable(getattr(type(file), attribute))
            and attribute.startswith("_") is False
        ]

        funcs = {}

        def getatt(self, oid, name):
            obj = self.client.getobject(oid, False)
            _obj = dill.loads(obj)
            return getattr(_obj, name)

        funcs["__getattr__"] = partial(getatt, self, path)

        def invoke(self, oid, method):
            return self.client.execute(oid, method)

        for method in method_list:
            funcs[method] = partial(invoke, self, path, method)

        proxy = type("ClassProxy", (), funcs)

        return proxy()

    def store(self, obj):
        import inspect

        _source = inspect.getsource(type(obj))
        self.client.store(obj.id, obj.path, obj.name, _source, dill.dumps(obj))

    def list(self, path, offset=0, size=0):
        return dill.loads(self.client.list(path, offset, size))

    def getobject(self, path, nodill, offset=0, size=0):
        file = self.client.getobject(path, nodill, offset=offset, size=size)
        _file = dill.loads(file)
        return _file

    def hello(self, query):

        return self.client.hello(query)

    def graphql(self, query):

        return self.client.graphql(query)

    def mkdir(self, directory):
        self.client.mkdir(directory)
        print(directory + " created.")

    def rm(self, path):
        self.client.rm(path)
        print(path + " removed.")

    def query(self, path):
        return self.client.query(path)

    def register(self, entry):
        logging.info("register entry %s", entry)
        self.client.register(entry)

    def get(self, oid, offset=0, size=0):
        file = self.client.get(oid, offset=offset, size=size)
        _files = []
        if type(file) is list:
            for f in file:
                _f = dill.loads(f)
                if "obj" in _f:
                    _f["obj"] = dill.loads(_f["obj"])
                _files += [_f]
        else:
            if "obj" in file:
                file["obj"] = dill.loads(file["obj"])
            _files = file

        return _files

    def run(self, oid, method):
        return self.client.execute(oid, method)

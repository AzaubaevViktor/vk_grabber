from typing import Any, Union

import yaml

from core import Log


def LoadConfig(file_name: str = None) -> "Config":
    log = Log("LoadConfig")

    file_name = file_name or "private.yaml"

    log.info("Load config", source=file_name)

    with open(file_name, "rt") as f:
        data = yaml.safe_load(f)

    def do_update():
        log.info("Update config file", source=file_name)
        with open(file_name, "wt") as f:
            yaml.safe_dump(data, f)

    return Config(data, do_update, "", source=file_name)


class Config:
    def __init__(self, data: dict, update_func, path, source=None):
        super(Config, self).__setattr__("log", Log("Config"))
        super(Config, self).__setattr__("path", path)
        super(Config, self).__setattr__("_data", data)
        super(Config, self).__setattr__("update", update_func)
        super(Config, self).__setattr__("source", source)

    def __getattr__(self, item: str) -> Union["Config", Any]:
        self.log.deep('Access to', path=self.path, item=item)
        if item not in self._data:
            raise KeyError(f"Key `{item}` not found, try one of: "
                           f"({', '.join(self._data.keys())})")

        new_data = self._data[item]

        if isinstance(new_data, dict):
            path = ((self.path + ".") if self.path else "") + item
            return Config(self._data[item], self.update, path=path)

        return new_data

    def __getitem__(self, item) -> Union["Config", Any]:
        return getattr(self, item)

    def __setattr__(self, key, value):
        if key not in self._data:
            raise KeyError(f"Key `{key}` not found, try one of: "
                           f"({', '.join(self._data.keys())})")

        self._data[key] = value
        return value

    def __setitem__(self, key, value):
        self[key] = value
        return value

    def __iter__(self):
        return iter(self._data.items())

    def __eq__(self, other):
        if isinstance(other, dict):
            return self._data == other

        raise NotImplementedError()

    def __repr__(self):
        return f"<Config: {self.source} {self.path}>"


__all__ = ("LoadConfig", "Config")

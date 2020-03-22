import yaml


class LoadConfig:
    FILE_NAME = "private.yml"

    def __init__(self, file_name=None):
        self.file_name = file_name or self.FILE_NAME
        with open(file_name, "rt") as f:
            self._data = yaml.safe_load(f)

    def __getattr__(self, item):
        return self._data[item]


__all__ = ("LoadConfig", )

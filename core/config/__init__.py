import yaml

from core import Log


class LoadConfig:
    FILE_NAME = "private.yaml"

    def __init__(self, file_name=None):
        self.file_name = file_name or self.FILE_NAME
        self.log = Log("LoadConfig")
        self.log.info("Load config", source=self.file_name)

        with open(self.file_name, "rt") as f:
            self._data = yaml.safe_load(f)

    def __getattr__(self, item):
        self.log.debug('Access to', item=item)
        return self._data[item]


__all__ = ("LoadConfig", )

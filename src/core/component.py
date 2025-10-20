# -*- coding: utf-8 -*-

import importlib


class Component(object):
    def __init__(self, name: str, module_path: str, class_name: str):
        self.name = name
        self.module_path = module_path
        self.class_name = class_name
        self.instance = None

    def get_instance(self):
        if not self.instance:
            assert self.module_path, "Key 'module_path' is empty."
            assert self.class_name, "Key 'class_name' is empty."
            self.instance = getattr(importlib.import_module(self.module_path), self.class_name)
        return self.instance

    def get_module_path(self):
        return self.module_path

    def get_class_name(self):
        return self.class_name

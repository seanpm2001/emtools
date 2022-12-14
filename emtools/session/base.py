#!/usr/bin/env python
import math
import sys
import os
import json
from collections import OrderedDict
from glob import glob
from pprint import pprint
import argparse

from emtools.utils import Pretty, Color, Path
from datetime import datetime

import xmltodict
from .config import *


class SessionsBase:
    def __init__(self, **kwargs):
        self.cache_folder = kwargs.get('cache_folder', SESSIONS_CACHE_FOLDER)
        self.sessions_json_file = os.path.join(self.cache_folder,
                                               self.cache_file)
        self.verbose = kwargs.get('verbose', 0)
        self.sessions = OrderedDict()
        self.load()

    def print(self, *args):
        if self.verbose:
            print(*args)

    def load(self):
        """ Load sessions. """
        self.sessions = OrderedDict()
        if os.path.exists(self.sessions_json_file):
            with open(self.sessions_json_file) as f:
                for s in json.load(f):
                    self.sessions[s['path']] = s

    def save(self):
        with open(self.sessions_json_file, 'w') as f:
            json.dump([s for s in self.sessions.values()], f)

    def update(self, new_sessions):
        for s in new_sessions:
            self.update_session(s)
            self.sessions[s['path']] = s
        self.save()
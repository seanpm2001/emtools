# **************************************************************************
# *
# * Authors:  J. M. de la Rosa Trevin (delarosatrevin@gmail.com)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# **************************************************************************


import os
import sys
import argparse
from collections import OrderedDict, namedtuple
from contextlib import AbstractContextManager
import sqlite3

from .table import ColumnList, Table


class SqliteFile(AbstractContextManager):
    """
    Class to manipulate Scipion Set Sqlite files.
    """
    def __init__(self, inputFile, mode='r'):
        """
        Args:
            inputFile: can be a str with the file path or a file object.
            mode: mode to open the file, if inputFile is already a file,
                the mode will be ignored.
        """
        self._names = []
        self._file = inputFile
        self._con = sqlite3.connect(f"file:{inputFile}?mode=ro", uri=True)
        self._con.row_factory = self._dict_factory

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def __contains__(self, item):
        """ Return if a table name is in the file. """
        return item in self.getTableNames()

    def getTableNames(self):
        """ Return all the names of the data_ blocks found in the file. """
        if not self._names:  # Scan for ALL table names
            res = self._con.execute("SELECT name FROM sqlite_master "
                                    "WHERE type='table'")
            self._names = [row['name'] for row in res.fetchall()]

        return self._names

    def getTable(self, tableName, **kwargs):
        raise Exception('getTable is not implemented for Sqlite files. '
                        'Use iterTable instead, iteration will yield a dict.')

    def getTableSize(self, tableName):
        """ Return the number of elements in the given table.
        This method is much more efficient that parsing the table
        and getting the size, if the size what is important.
        """
        return self._con.execute(f"SELECT COUNT(*) FROM {tableName}").fetchone()['COUNT(*)']

    def iterTable(self, tableName, **kwargs):
        """ Only iterate over the table's rows and do not create
        a Table in memory to store all rows.
        Args:
            tableName: the name of the table to read, it can be the empty string
            kwargs:
                limit: integer value to limit the number of elements
                start: start from a given element
                classes: read column names from a 'classes' table
        """
        #start = kwargs.get('start', 1) - 1
        #limit = kwargs.get('limit', 0)
        query = f"SELECT * FROM {tableName}"

        if 'limit' in kwargs:
            query += f" LIMIT {kwargs['limit']}"

        if 'start' in kwargs:
            query += f" OFFSET {kwargs['start'] - 1}"

        print(query)

        if 'classes' not in kwargs:
            res = self._con.execute(query)
            while row := res.fetchone():
                yield row
        else:
            columnsMap = {row['column_name']: row['label_property']
                          for row in self.iterTable(kwargs['classes'])}

            def _row_factory(cursor, row):
                fields = [column[0] for column in cursor.description]
                return {columnsMap.get(k, k): v for k, v in zip(fields, row)}

            # Modify row factory to modify column names
            self._con.row_factory = _row_factory
            res = self._con.execute(query)
            while row := res.fetchone():
                yield row
            # Restore row factory
            self._con.row_factory = self._dict_factory

    def close(self):
        if getattr(self, '_con', None):
            self._con.close()
            self._con = None

    def _dict_factory(self, cursor, row):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}


# --------- Helper functions  ------------------------
def _guessType(strValue):
    try:
        int(strValue)
        return int
    except ValueError:
        try:
            float(strValue)
            return float
        except ValueError:
            return str


def _guessTypesFromLine(line):
    return [_guessType(v) for v in line.split()]


def _formatValue(v):
    return '%0.6f' % v if isinstance(v, float) else str(v)


def _getFormatStr(v):
    return '.6f' if isinstance(v, float) else ''



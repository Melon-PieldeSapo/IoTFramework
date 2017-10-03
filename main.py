#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
import sys

from Control import Control


if __name__ == '__main__':

    file_name = False
    if( len(sys.argv) == 2):
        file_name = sys.argv[1]

    control = Control(file_name)
    control.run()

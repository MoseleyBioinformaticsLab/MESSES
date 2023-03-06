# -*- coding: utf-8 -*-

import pandas
import numpy

def tagSheet(taggingDirectives: list, worksheet: pandas.DataFrame, silent: bool) -> tuple[numpy.ndarray,list[bool]]:
    """Add tags to the worksheet using the given tagging directives.

    Args:
        taggingDirectives (list): List of dictionaries. One dictionary for each tagging group.
        worksheet (memoryview): cython memoryview to a 2d numpy array of strings (objects).
        silent (bool): if True don't print warnings.
        
    Returns:
        (tuple): tuple where the first value is the worksheet memoryview turned into a numpy array and the second value is a list of bools indicating which tagging directives in taggingDirectives were used.
    """
    pass





















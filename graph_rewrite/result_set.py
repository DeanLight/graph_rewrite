# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_condition_filter.ipynb.

# %% auto 0
__all__ = ['ConditionFunc', 'filter_matches']

# %% ../nbs/04_condition_filter.ipynb 1
from typing import *

# %% ../nbs/04_condition_filter.ipynb 3
ConditionFunc = Callable[Match, bool]

# %% ../nbs/04_condition_filter.ipynb 5
def filter_matches(unfiltered_results: ResultSet, condition: ConditionFunc) -> ResultSet:
    # initialize new_matches, empty list

    # for match in unfiltered_results.matches:
    #   if condition(match):
    #       add match to new_matches

    # return ResultSet(new_matches)
    pass

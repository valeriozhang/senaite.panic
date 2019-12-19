# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.PANIC.
#
# SENAITE.PANIC is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2019 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims.content.analysisspec import ResultsRangeDict
from bika.lims.interfaces import ISubmitted
from bika.lims import api
from bika.lims.interfaces.analysis import IRequestAnalysis


def has_analyses_in_panic(sample):
    """Returns whether the sample passed in have at least one analysis for which
    the result is in panic in accordance with the specifications. Only analyses
    in "to_be_verified" status and beyond are considered
    """
    analyses = sample.getAnalyses(full_objects=True)
    for analysis in analyses:
        if ISubmitted.providedBy(analysis) and is_in_panic(analysis):
            return True
    return False


def is_in_panic(analysis):
    """Returns whether if the result of the analysis is below the min panic or
    above the max panic
    """
    # To begin with, the result must be floatable
    result = to_float_or_none(analysis.getResult())
    if result is None:
        return False

    # Get panic min and max
    panic_min, panic_max = get_panic_tuple(analysis)

    # Below the min panic?
    if panic_min is not None:
        if result <= panic_min:
            return True

    # Above the max panic?
    if panic_max is not None:
        if result >= panic_max:
            return True

    # Not in panic
    return False


def to_float_or_none(value):
    """Returns the float if the value is floatable. Otherwise, returns None
    """
    if api.is_floatable(value):
        return api.to_float(value)
    return None


def get_panic_tuple(analysis):
    """Returns a tuple of min_panic and max_panic for the given analysis.
    Resolves each item to None if not found or not valid for the analysis
    """
    panic_range = get_panic_range(analysis)
    panic_min = panic_range.get("min_panic", None)
    panic_max = panic_range.get("max_panic", None)
    return tuple(map(to_float_or_none, [panic_min, panic_max]))


def get_panic_range(analysis):
    """Returns the panic range values for the passed in analysis
    """
    if not IRequestAnalysis.providedBy(analysis):
        return analysis.getResultsRange() or ResultsRangeDict()

    # We need to do this trick because when "Enable Sample specifications"
    # is active, Add Sample form stores the results ranges directly to each
    # analysis, but only considers min, max, warnmin and warnmax
    request = analysis.getRequest()
    specs = request.getSpecification()

    # Get the specification values for all services
    specs = specs.getResultsRange() or []

    # Filter the spec values for our analysis
    keyword = analysis.getKeyword()
    results_range = filter(lambda rr: rr.get("keyword") == keyword, specs)
    if results_range:
        return results_range[0]

    return ResultsRangeDict()

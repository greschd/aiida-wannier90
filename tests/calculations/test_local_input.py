# -*- coding: utf-8 -*-
"""Tests for the `PwCalculation` class."""
from __future__ import absolute_import, print_function

import os

import pytest

from aiida import orm
from aiida.common import datastructures
from aiida.common.exceptions import InputValidationError

ENTRY_POINT_NAME = 'wannier90.wannier90'


@pytest.fixture
def generate_common_inputs_gaas(
    shared_datadir,
    fixture_folderdata,
    fixture_code,
    generate_win_params_gaas,
):
    def _generate_common_inputs_gaas(inputfolder_seedname):
        from aiida.tools import get_kpoints_path
        from aiida_wannier90.orbitals import generate_projections

        inputs = dict(
            code=fixture_code(ENTRY_POINT_NAME),
            metadata={
                'options': {
                    'resources': {
                        'num_machines': 1
                    },
                    'max_wallclock_seconds': 3600,
                    'withmpi': False,
                }
            },
            local_input_folder=fixture_folderdata(
                shared_datadir / 'gaas', {'gaas': inputfolder_seedname}
            ),
            **generate_win_params_gaas()
        )

        return inputs

    return _generate_common_inputs_gaas


@pytest.fixture(params=(None, "aiida", "wannier"))
def seedname(request):
    return request.param


# @pytest.mark.parametrize("seedname", (None, "aiida", "wannier"))
def test_wannier90_default(
    fixture_sandbox, generate_calc_job, generate_common_inputs_gaas,
    file_regression, seedname
):
    """Test a default `Wannier90Calculation` with local input folder."""

    input_seedname = seedname or 'aiida'
    inputs = generate_common_inputs_gaas(inputfolder_seedname=input_seedname)
    if seedname is not None:
        inputs['metadata']['options']['seedname'] = seedname

    calc_info = generate_calc_job(
        folder=fixture_sandbox,
        entry_point_name=ENTRY_POINT_NAME,
        inputs=inputs
    )

    cmdline_params = [input_seedname]
    local_copy_list = [(val, val) for val in (
        'UNK00001.1', 'UNK00002.1', 'UNK00003.1', 'UNK00004.1', 'UNK00005.1',
        'UNK00006.1', 'UNK00007.1', 'UNK00008.1',
        '{}.mmn'.format(input_seedname), '{}.amn'.format(input_seedname)
    )]
    retrieve_list = [
        "{}{}".format(input_seedname, suffix)
        for suffix in ('.wout', '.werr', '_band.dat', '_band.kpt')
    ]
    retrieve_temporary_list = []

    # Check the attributes of the returned `CalcInfo`
    assert isinstance(calc_info, datastructures.CalcInfo)
    code_info = calc_info.codes_info[0]
    assert code_info.cmdline_params == cmdline_params
    # ignore UUID - keep only second and third entry
    local_copy_res = [tup[1:] for tup in calc_info.local_copy_list]
    assert sorted(local_copy_res) == sorted(local_copy_list)
    assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)
    assert sorted(calc_info.retrieve_temporary_list
                  ) == sorted(retrieve_temporary_list)
    assert sorted(calc_info.remote_symlink_list) == sorted([])

    with fixture_sandbox.open('{}.win'.format(input_seedname)) as handle:
        input_written = handle.read()

    # Checks on the files written to the sandbox folder as raw input
    assert sorted(fixture_sandbox.get_content_list()
                  ) == sorted(['{}.win'.format(input_seedname)])
    file_regression.check(input_written, encoding='utf-8', extension='.win')


def test_wannier90_wrong_seedname(
    fixture_sandbox, generate_calc_job, generate_common_inputs_gaas, seedname
):
    """Test a default `Wannier90Calculation` with local input folder."""

    inputs = generate_common_inputs_gaas(inputfolder_seedname='something_else')
    if seedname is not None:
        inputs['metadata']['options']['seedname'] = seedname

    with pytest.raises(InputValidationError):
        generate_calc_job(
            folder=fixture_sandbox,
            entry_point_name=ENTRY_POINT_NAME,
            inputs=inputs
        )
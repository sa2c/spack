# Copyright 2013-2021 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os
import sys

import pytest

from llnl.util.filesystem import FileFilter

import spack.main
import spack.paths
from spack.cmd.style import changed_files
from spack.repo import Repo
from spack.util.executable import which

style = spack.main.SpackCommand("style")


@pytest.fixture(scope="module")
def flake8_package():
    """Style only checks files that have been modified. This fixture makes a small
    change to the ``flake8`` mock package, yields the filename, then undoes the
    change on cleanup.
    """
    repo = Repo(spack.paths.mock_packages_path)
    filename = repo.filename_for_package_name("flake8")
    package = FileFilter(filename)

    # Make the change
    package.filter("state = 'unmodified'", "state = 'modified'", string=True)

    yield filename

    # Undo the change
    package.filter("state = 'modified'", "state = 'unmodified'", string=True)


def test_changed_files(flake8_package):
    # changed_files returns file paths relative to the root
    # directory of Spack. Convert to absolute file paths.
    files = [os.path.join(spack.paths.prefix, path) for path in changed_files()]

    # There will likely be other files that have changed
    # when these tests are run
    assert flake8_package in files


# As of flake8 3.0.0, Python 2.6 and 3.3 are no longer supported
# http://flake8.pycqa.org/en/latest/release-notes/3.0.0.html
@pytest.mark.skipif(
    sys.version_info[:2] <= (2, 6) or (3, 0) <= sys.version_info[:2] <= (3, 3),
    reason="flake8 no longer supports Python 2.6 or 3.3 and older",
)
@pytest.mark.skipif(not which("flake8"), reason="flake8 is not installed.")
def test_flake8(flake8_package, tmpdir):
    root_relative = os.path.relpath(flake8_package, spack.paths.prefix)

    # use a working directory to test cwd-relative paths, as tests run in
    # the spack prefix by default
    with tmpdir.as_cwd():
        relative = os.path.relpath(flake8_package)
        output = style(flake8_package)
        assert relative in output
        assert "spack style checks were clean" in output

    output = style("--output", "--root-relative", flake8_package)
    assert root_relative in output
    assert "spack style checks were clean" in output

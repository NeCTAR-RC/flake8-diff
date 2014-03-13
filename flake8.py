#!/usr/bin/env python
# Copyright (c) 2014 University of Melbourne
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import re
import sys
import subprocess


env = os.environ.copy()
line_match = re.compile(r'^([^\s]+):([\d]+):[\d]+: ')


def which(name, flags=os.X_OK):
    """taken from twisted/python/procutils.py"""
    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result

try:
    GIT = which('git')[0]
except:
    raise Exception('git executable can\'t be found')

try:
    FLAKE8 = which('flake8')[0]
except:
    raise Exception('flake8 executable can\'t be found')


def git_diff_linenumbers(filename, revision=None):
    """Return a list of lines that have been added/changed in a file."""
    diff_command = ' '.join(['diff',
                             '--new-line-format="%dn "',
                             '--unchanged-line-format=""',
                             '--changed-group-format="%>"'])
    difftool_command = "difftool -y -x '%s'" % diff_command

    def _call(*args):
        try:
            lines_output = subprocess.check_output(
                " ".join([GIT, difftool_command]
                         + list(args)
                         + ["--", filename]),
                env=env, shell=True)
        except subprocess.CalledProcessError:
            lines_output = ""
        return lines_output

    if revision:
        lines_output = _call(revision)
        return lines_output.split()
    else:
        lines_output = _call()
        # Check any files that are in the cache
        lines_output1 = _call("--cached")
        return lines_output.split() + lines_output1.split()


def flake8(filename, *args):
    """Run flake8 over a file and return the output"""
    proc = subprocess.Popen(" ".join([FLAKE8, filename] + list(args)),
                            stdout=subprocess.PIPE, env=env, shell=True)
    (output, err) = proc.communicate()
    status = proc.wait()
    if status != 0 and len(output) == 0:
        print err
        raise Exception("Something odd happened while executing flake8.")
    return output


def git_changed_files(revision=None):
    """Return a list of all the files changed in git"""
    if revision:
        files = subprocess.check_output(
            " ".join([GIT, "diff --name-only", revision]),
            env=env, shell=True)
        return [filename for filename in files.split('\n')
                if filename]
    else:
        files = subprocess.check_output(
            " ".join([GIT, "diff --name-only"]),
            env=env, shell=True)
        cached_files = subprocess.check_output(
            " ".join([GIT, "diff --name-only --cached"]),
            env=env, shell=True)
        return [filename for filename
                in set(files.split('\n')) | set(cached_files.split('\n'))
                if filename]


def git_current_rev():
    return subprocess.check_output(" ".join([GIT, "rev-parse HEAD^"]),
                                   env=env, shell=True).strip()


WHITE_LIST = [re.compile(r'.*[.]py$')]
BLACK_LIST = []

SPECIAL_CASE_ARGS = {r'migrations/[0-9]+': ['--ignore=E501']}


def main():
    exit_status = 0
    revision = None
    files = git_changed_files()
    if not files:
        revision = git_current_rev()
        files = git_changed_files(revision)
    for filename in files:
        if not all(map(lambda x: x.match(filename),
                       WHITE_LIST)):
            print >> sys.stderr, 'SKIPPING %s' % filename
            continue
        if any(map(lambda x: x.match(filename),
                   BLACK_LIST)):
            print >> sys.stderr, 'SKIPPING %s' % filename
            continue
        included_lines = git_diff_linenumbers(filename, revision)

        for regex, args in SPECIAL_CASE_ARGS.items():
            if re.search(regex, filename):
                flake8_output = flake8(filename, *args)
                break
        else:
            flake8_output = flake8(filename)

        for line in flake8_output.split('\n'):
            line_details = line_match.match(line)
            if not line_details:
                continue
            flake_filename, lineno = line_details.groups()
            if lineno in included_lines:
                print line
                exit_status = 1
    sys.exit(exit_status)

if __name__ == "__main__":
    main()

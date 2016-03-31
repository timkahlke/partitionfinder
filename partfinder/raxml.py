#Copyright (C) 2012 Robert Lanfear and Brett Calcott
#
#This program is free software: you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the
#Free Software Foundation, either version 3 of the License, or (at your
#option) any later version.
#
#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details. You should have received a copy
#of the GNU General Public License along with this program.  If not, see
#<http://www.gnu.org/licenses/>. PartitionFinder also includes the PhyML
#program, the RAxML program, the PyParsing library, and the python-cluster library
#all of which are protected by their own licenses and conditions, using
#PartitionFinder implies that you agree with those licences and conditions as well.

"""Run raxml and parse the output"""

import logging
log = logging.getLogger("raxml")

import subprocess
import shlex
import os
import shutil
import sys
import fnmatch
import util

from pyparsing import (
    Word, Literal, nums, Suppress, ParseException,
    SkipTo, OneOrMore, Regex
)

import raxml_models as models

_binary_name = 'raxml'
if sys.platform == 'win32':
    _binary_name += ".exe"

from util import PhylogenyProgramError


class RaxmlError(PhylogenyProgramError):
    pass


def find_program():
    """Locate the binary ..."""
    pth = os.path.abspath(__file__)

    # Split off the name and the directory...
    pth, notused = os.path.split(pth)
    pth, notused = os.path.split(pth)
    pth = os.path.join(pth, "programs", _binary_name)
    pth = os.path.normpath(pth)

    log.debug("Checking for program %s", _binary_name)
    if not os.path.exists(pth) or not os.path.isfile(pth):
        log.error("No such file: '%s'", pth)
        raise RaxmlError
    log.debug("Found program %s at '%s'", _binary_name, pth)
    return pth

_raxml_binary = None


def run_raxml(command):
    global _raxml_binary
    if _raxml_binary is None:
        _raxml_binary = find_program()

    # Add in the command file
    log.debug("Running 'raxml %s'", command)
    command = "\"%s\" %s" % (_raxml_binary, command)

    # Note: We use shlex.split as it does a proper job of handling command
    # lines that are complex
    p = subprocess.Popen(
        shlex.split(command),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    # Capture the output, we might put it into the errors
    stdout, stderr = p.communicate()
    # p.terminate()

    if p.returncode != 0:
        log.error("RAxML did not execute successfully")
        log.error("RAxML output follows, in case it's helpful for finding the problem")
        log.error("%s", stdout)
        log.error("%s", stderr)
        raise RaxmlError


def dupfile(src, dst):
    # Make a copy or a symlink so that we don't overwrite different model runs
    # of the same alignment

    # TODO maybe this should throw...?
    try:
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copyfile(src, dst)
    except OSError:
        log.error("Cannot link/copy file %s to %s", src, dst)
        raise RaxmlError


def make_topology(alignment_path, datatype, cmdline_extras):
    '''Make a MP tree to start the analysis'''
    log.info("Making MP tree for %s", alignment_path)

    cmdline_extras = check_defaults(cmdline_extras)

    # First get the MP topology like this (-p is a hard-coded random number seed):
    if datatype == "DNA":
        command = "-y -s '%s' -m GTRGAMMA -n MPTREE -p 123456789 %s" % (
            alignment_path, cmdline_extras)
    elif datatype == "protein":
        command = "-y -s '%s' -m PROTGAMMALG -n MPTREE -p 123456789 %s" % (
            alignment_path, cmdline_extras)
    else:
        log.error("Unrecognised datatype: '%s'" % (datatype))
        raise(RaxmlError)

    #force raxml to write to the dir with the alignment in it
    aln_dir, fname = os.path.split(alignment_path)
    command = ''.join([command, " -w '%s'" % os.path.abspath(aln_dir)])

    run_raxml(command)
    dir, aln = os.path.split(alignment_path)
    tree_path = os.path.join(dir, "RAxML_parsimonyTree.MPTREE")
    return tree_path


def make_branch_lengths(alignment_path, topology_path, datatype, cmdline_extras):
    #Now we re-estimate branchlengths using a GTR+G model on the (unpartitioned) dataset
    cmdline_extras = check_defaults(cmdline_extras)
    dir_path, fname = os.path.split(topology_path)
    tree_path = os.path.join(dir_path, 'topology_tree.phy')
    log.debug("Copying %s to %s", topology_path, tree_path)
    dupfile(topology_path, tree_path)
    os.remove(topology_path)  # saves headaches later...

    if datatype == "DNA":
        log.info("Estimating GTR+G branch lengths on tree using RAxML")
        command = "-f e -s '%s' -t '%s' -m GTRGAMMA -n BLTREE -w '%s' %s" % (
            alignment_path, tree_path, os.path.abspath(dir_path), cmdline_extras)
        run_raxml(command)
    if datatype == "protein":
        log.info("Estimating LG+G branch lengths on tree using RAxML")
        command = "-f e -s '%s' -t '%s' -m PROTGAMMALG -n BLTREE -w '%s' %s" % (
            alignment_path, tree_path, os.path.abspath(dir_path), cmdline_extras)
        run_raxml(command)

    dir, aln = os.path.split(alignment_path)
    tree_path = os.path.join(dir, "RAxML_result.BLTREE")
    log.info("Branchlength estimation finished")

    # Now return the path of the final tree with branch lengths
    return tree_path


def check_defaults(cmdline_extras):
    """We use some sensible defaults, but allow users to override them with extra cmdline options"""
    if cmdline_extras.count("-e") > 0:
        #then the user has specified a particular accuracy:
        accuracy = ""
    else:
        #we specify a default accuracy of 1 lnL unit
        accuracy = " -e 1.0 "

    #we set this in case people are using the PThreads version of RAxML
    #note that this is intentionally set to give an error if people use Pthreads, because
    #they will need to consider by hand what the optimal setting is. And, if we set it >1
    #then we risk massively slowing things down because PF's default is to use all possible
    #processors.
    if cmdline_extras.count("-T") > 0:
        num_threads = ""

    else:
        num_threads = " -T 1 "

    #and we'll specify the -O option, so that the program doesn't exit if there are undetermined seqs.
    #we'll put spaces at the start and end too, just in case...
    cmdline_extras = ''.join(
        [" ", cmdline_extras, accuracy, num_threads, "-O "])

    return cmdline_extras


def analyse(model, alignment_path, tree_path, branchlengths, cmdline_extras):
    """Do the analysis -- this will overwrite stuff!"""

    # Move it to a new name to stop raxml stomping on different model analyses
    # dupfile(alignment_path, analysis_path)
    model_params = models.get_model_commandline(model)

    if branchlengths == 'linked':
        #constrain all branchlengths to be equal
        bl = ' -f B '
    elif branchlengths == 'unlinked':
        #let branchlenghts vary among subsets
        bl = ' -f e '
    else:
        # WTF?
        log.error("Unknown option for branchlengths: %s", branchlengths)
        raise RaxmlError

    cmdline_extras = check_defaults(cmdline_extras)

    #raxml doesn't append alignment names automatically, like PhyML, let's do that here
    analysis_ID = raxml_analysis_ID(alignment_path, model)

    #force raxml to write to the dir with the alignment in it
    #-e 1.0 sets the precision to 1 lnL unit. This is all that's required here, and helps with speed.
    aln_dir, fname = os.path.split(alignment_path)
    command = " %s -s '%s' -t '%s' %s -n %s -w '%s' %s" % (
        bl, alignment_path, tree_path, model_params, analysis_ID, os.path.abspath(aln_dir), cmdline_extras)
    run_raxml(command)


def raxml_analysis_ID(alignment_path, model):
    dir, file = os.path.split(alignment_path)
    aln_name = os.path.splitext(file)[0]
    analysis_ID = '%s_%s.txt' % (aln_name, model)
    return analysis_ID


def make_tree_path(alignment_path):
    dir, aln = os.path.split(alignment_path)
    tree_path = os.path.join(dir, "RAxML_result.BLTREE")
    return tree_path


def make_output_path(alignment_path, model):
    analysis_ID = raxml_analysis_ID(alignment_path, model)
    dir, aln_file = os.path.split(alignment_path)
    stats_fname = "RAxML_info.%s" % (analysis_ID)
    stats_path = os.path.join(dir, stats_fname)
    tree_fname = "RAxML_result.%s" % (analysis_ID)
    tree_path = os.path.join(dir, tree_fname)
    return stats_path, tree_path


def remove_files(aln_path, model):
    '''remove all files from the alignment directory that are produced by raxml'''
    dir, file = os.path.split(aln_path)
    analysis_ID = raxml_analysis_ID(aln_path, model)
    dir = os.path.abspath(dir)
    fs = os.listdir(dir)
    fnames = fnmatch.filter(fs, '*%s*' % analysis_ID)
    util.delete_files(fnames)


class RaxmlResult(object):

    def __init__(self):
        self.rates = {}
        self.freqs = {}

    def __str__(self):
        return "RaxmlResult(lnl:%s, tree_size:%s, secs:%s, alphs:%s)" % (
                self.lnl, self.tree_size, self.seconds, self.alpha)


class Parser(object):
    def __init__(self, datatype):

        if datatype == "protein":
            letters = "ARNDCQEGHILKMFPSTWYV"
        elif datatype == "DNA":
            letters = "ATCG"
        else:
            log.error("Unknown datatype '%s', please check" % datatype)
            raise RaxmlError

        FLOAT = Word(nums + '.-').setParseAction(lambda x: float(x[0]))

        L = Word(letters, exact=1)
        COLON = Suppress(":")

        LNL_LABEL = Regex("Final GAMMA.+:") | Literal("Likelihood:")
        TIME_LABEL = Regex("Overall Time.+:") | Regex("Overall Time.+tion ")
        ALPHA_LABEL = Literal("alpha:")
        TREE_SIZE_LABEL = Literal("Tree-Length:")

        def labeled_float(label):
            return Suppress(SkipTo(label)) + Suppress(label) + FLOAT

        lnl = labeled_float(LNL_LABEL)
        lnl.setParseAction(self.set_lnl)

        seconds = labeled_float(TIME_LABEL)
        seconds.setParseAction(self.set_seconds)

        alpha = labeled_float(ALPHA_LABEL)
        alpha.setParseAction(self.set_alpha)

        tree_size = labeled_float(TREE_SIZE_LABEL)
        tree_size.setParseAction(self.set_tree_size)

        rate = Suppress("rate") + L + Suppress("<->") + L + COLON + FLOAT
        rate.setParseAction(self.set_rate)
        rates = OneOrMore(rate)

        freq = Suppress("freq pi(") + L + Suppress("):") + FLOAT
        freq.setParseAction(self.set_freq)
        freqs = OneOrMore(freq)

        # Just look for these things
        self.root_parser = seconds + lnl + alpha + tree_size + rates + freqs

    def set_seconds(self, tokens):
        self.result.seconds = tokens[0]

    def set_lnl(self, tokens):
        self.result.lnl = tokens[0]

    def set_tree_size(self, tokens):
        self.result.tree_size = tokens[0]

    def set_alpha(self, tokens):
        self.result.alpha = tokens[0]

    def set_rate(self, tokens):
        basefrom, baseto, rate = tokens
        self.result.rates[(basefrom, baseto)] = rate

    def set_freq(self, tokens):
        base, rate = tokens
        self.result.freqs[base] = rate

    def parse(self, text):
        log.debug("Parsing raxml output...")
        self.result = RaxmlResult()
        try:
            self.root_parser.parseString(text)
        except ParseException, p:
            log.error(str(p))
            raise RaxmlError

        log.debug("Result is %s", self.result)
        return self.result


def parse(text, datatype):
    the_parser = Parser(datatype)
    return the_parser.parse(text)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    pth = "./tests/misc/raxml_nucleotide.output"
    p = Parser('DNA')
    result = p.parse(open(pth).read())

    pth = "./tests/misc/raxml_aminoacid.output"
    p = Parser('protein')
    result = p.parse(open(pth).read())

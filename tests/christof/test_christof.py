"""Incorporate some tests from Christoph Mayer (originally in Perl)"""
# TODO This could be automated in the same way "full_analysis'

import os
import inspect
import pytest
from partfinder import main, util, analysis, config, alignment

HERE = os.path.abspath(os.path.dirname(__file__))

# Far too clever function
def path_from_function():
    funname = inspect.stack()[1][3]
    # remove test_
    funname = funname[5:]
    funname = funname.replace('_', '-')
    pth = os.path.join(HERE, funname)
    return pth

# ---------------- SUCCESS ---------------------

def test_greedy_phyml_dna():
    main.call_main("DNA", '"%s"' % path_from_function())

def test_greedy_raxml_dna():
    main.call_main("DNA", '"%s" --raxml' % path_from_function())

def test_greedy_phyml_protein():
    main.call_main("protein", '"%s"' % path_from_function())

def test_greedy_raxml_protein():
    main.call_main("protein", '"%s" --raxml' % path_from_function())

def test_clustering_raxml_dna():
    main.call_main("DNA", '"%s" --raxml' % path_from_function())


# ---------------- ERRORS ---------------------
# Check the exception, and then look in the log output for specific
# details of the exception.

def test_alignment_error(caplog):
    with pytest.raises(alignment.AlignmentError):
        main.call_main("protein", '"%s"' % path_from_function())
    assert "Site 1000 is specified in [data_blocks], but the alignment only has 949 sites." in caplog.text()

def test_overlap_error(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("protein", '"%s"' % path_from_function())
    assert "overlaps with previously defined partitions" in caplog.text()

def test_clustering_phyml_dna(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s"' % path_from_function())
    assert "Clustering methods are only available when using raxml" in caplog.text()

def test_model_greedy_phyml01(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s"' % path_from_function())
    assert "'WAG+I+G+I' is not a valid model for phylogeny program phyml." in caplog.text()

def test_model_greedy_phyml02(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s"' % path_from_function())
    assert "only works with nucleotide models" in caplog.text()

def test_model_greedy_phyml03(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s"' % path_from_function())
    assert "'WAG+LG+F+I' is not a valid model for phylogeny program phyml" in caplog.text()

def test_model_greedy_raxml01(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s" --raxml' % path_from_function())
    assert "WAG+F' is not a valid model for phylogeny program raxml" in caplog.text()

def test_model_greedy_raxml02(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s" --raxml' % path_from_function())
    assert "Expected ";" (at char 284), (line:9, col:22)" in caplog.text()

def test_model_greedy_raxml03(caplog):
    with pytest.raises(util.PartitionFinderError):
        main.call_main("DNA", '"%s" --raxml' % path_from_function())
    assert "MtArt+I+G+F' is not a valid model for phylogeny program raxml" in caplog.text()


# Experiment combinator to run the same experiment several times and
# return only the summary statistics
#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import epyc

import numpy


class RepeatedExperiment(epyc.Experiment):
    '''A experiment combinator that takes a "base" experiment, runs it several times,
    and returns summary statistics for the results. This means you can define a
    single experiment separate from its repeating logic.'''

    # Additional metadata
    REQUESTED_REPETITIONS = 'requested_repetitions'   # repetitions attempted
    REPETITIONS = 'repetitions'                       # repetitions successfully completed

    # Prefix and suffix attached to summarised result and metadata values
    MEAN_SUFFIX = '_mean'
    VARIANCE_SUFFIX = '_variance'
    UNDERLYING_PREFIX = 'underlying_'
    
    
    def __init__( self, ex, N, summarised_results = None, summarised_metadata = None ):
        '''Create a repeated version of the given experiment. The metadata and result
        fields returned can be restricted by providing the desired field names.

        ex: the underlying experiment
        N: the number of repetitions to perform
        summarised_results: list of result values to summarise (defaults to all)
        summarised_metadata: list of metadata values to summarise (defaults to all)'''
        epyc.Experiment.__init__(self)
        self._experiment = ex
        self._N = N
        self._summarised_results = summarised_results
        self._summarised_metadata = summarised_metadata

    def experiment( self ):
        '''Return the underlying experiment.

        returns: the underlying experiment'''
        return self._experiment

    def repetitions( self ):
        '''Return the number of repetitions of the underlying experiment
        we perform.

        returns: the number of repetitions'''
        return self._N
    
    def doOne( self, params ):
        '''Run the uinderlying experiment once.

        params: the parameters to the underlying experiment
        returns: the results of running the underlying experiment'''
        return self.experiment().runExperiment(params)

    def summariseMetadata( self, results ):
        '''Add summary metadata from the underlying experiments to our metadata
        record. The fields summarised can be limited when the repeated experiment
        is constructed.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error.

        results: an array of result dicts'''

        # work out the fields to summarise
        ks = self._summarised_metadata
        if ks is None:
            ks = [ epyc.Experiment.ELAPSED_TIME ]
        
        # add the summary statistics to our metadata record
        for k in ks:
            vs = [ res[epyc.Experiment.METADATA][k] for res in results ]
            self._timings[self.UNDERLYING_PREFIX + k + self.MEAN_SUFFIX]     = numpy.mean(vs)
            self._timings[self.UNDERLYING_PREFIX + k + self.VARIANCE_SUFFIX] = numpy.var(vs)

        # add repetition statistics
        self._timings[self.REQUESTED_REPETITIONS]  = self.repetitions()
        self._timings[self.REPETITIONS]            = len(results)

    def summarise( self, results ):
        '''Generate a summary result dict from an array of result dicts
        returned by do() on the repetitions of the underlying experiment.
        By default we generate order, mean and variance for each value recorded.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error.

        Override this method to create different summary statistics.

        results: an array of result dicts
        returns: a dict of summary statistics'''
        if len(results) == 0:
            return dict()
        else:
            summary = dict()

            # work out the fields to summarise
            ks = self._summarised_results
            if ks is None:
                ks = results[0][epyc.Experiment.RESULTS].keys()

            # add the summary statistics
            for k in ks:
                vs = [ res[epyc.Experiment.RESULTS][k] for res in results ]
                summary[k + self.MEAN_SUFFIX]     = numpy.mean(vs)
                summary[k + self.VARIANCE_SUFFIX] = numpy.var(vs)

            return summary   

    def do( self, params ):
        '''Perform the number of repetitions we want and average the results.
        Our results are the summary statistics extracted from the results of
        the instances of the underlying experiment that we performed.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error.

        params: the parameters to the underlying experiment
        returns: the summary statistics'''

        # perform the repetitions, collecting the individual results
        N = self.repetitions()
        results = []
        for i in xrange(N):
            res = self.doOne(params)
            results.append(res)

        # filter out unsuccessful repetitions
        successfulResults = [ res for res in results if res[epyc.Experiment.METADATA][epyc.Experiment.STATUS] ]

        # construct summary results
        summary = self.summarise(successfulResults)

        # add summary metadata to our metadata record
        self.summariseMetadata(successfulResults)
        
        return summary
    
        

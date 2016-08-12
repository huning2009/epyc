#
# Copyright (C) 2016 Simon Dobson
# 
# Licensed under the GNU General Public Licence v.2.0
#

import epyc

import numpy


class SummaryExperiment(epyc.Experiment):
    '''An experiment combinator that takes an underlying "base" experiment and 
    returns summary statistics for some of its results. This only really makes
    sense for experiments that return lists of results, such as those conducted
    using RepeatedExperiment.

    When run, a summary experiment summarises the results of the
    results, creating a new set of results that include the mean and
    variance for each result that the underyling experiments
    generated. (You can also select which results to summarise.) The
    raw results are discarded. The new results have the names of the
    raw results, suffixed by "_mean" and "_variance".

    The summary calculations only include those experimental runs that succeeded,
    that is that have their status set to True. Failed runs are ignored.'''

    # Additional metadata
    UNDERLYING_RESULTS = 'repetitions'                         # repetitions summarised
    UNDERLYING_SUCCESSFUL_RESULTS = 'successful-repetitions'   # repetitions included
                                                               # in the summary

    # Prefix and suffix tags attached to summarised result and metadata values
    MEAN_SUFFIX = '_mean'
    MEDIAN_SUFFIX = '_median'
    VARIANCE_SUFFIX = '_variance'
    
    
    def __init__( self, ex, summarised_results = None ):
        '''Create a summarised version of the given experiment. The given
        fields in the experimental results will be summarised, defaulting to all.

        ex: the underlying experiment
        summarised_results: list of result values to summarise (defaults to all)'''
        super(epyc.SummaryExperiment, self).__init__()
        self._experiment = ex
        self._summarised_results = summarised_results

    def experiment( self ):
        '''Return the underlying experiment.

        returns: the underlying experiment'''
        return self._experiment

    def _mean( self, k ):
        '''Return the tag associated with the mean of k.'''
        return k + self.MEAN_SUFFIX

    def _median( self, k ):
        '''Return the tag associated with the median of k.'''
        return k + self.MEDIAN_SUFFIX

    def _variance( self, k ):
        '''Return the tag associated with the variance of k.'''
        return k + self.VARIANCE_SUFFIX
    
    def summarise( self, results ):
        '''Generate a summary result dict from a list of result dicts
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
                summary[self._mean(k)]     = numpy.mean(vs)
                summary[self._median(k)]   = numpy.median(vs)
                summary[self._variance(k)] = numpy.var(vs)

            return summary   

    def do( self, params ):
        '''Perform the underlying experiment and summarise its results.
        Our results are the summary statistics extracted from the results of
        the instances of the underlying experiment that we performed.

        We drop from the calculations any experiments whose completion status
        was False, indicating an error.

        params: the parameters to the underlying experiment
        returns: the summary statistics of the underlying results'''

        # set the parameters of the underlying experiment
        self.experiment().set(params)

        # perform the underlying experiment
        results = self.experiment().run()

        # extract only the successful runs
        sresults = [ res for res in results if res[epyc.Experiment.METADATA][epyc.Experiment.STATUS] ]

        # add extra values to out metadata record
        self._metadata[self.UNDERLYING_RESULTS]            = len(results)
        self._metadata[self.UNDERLYING_SUCCESSFUL_RESULTS] = len(sresults)
        
        # construct summary results
        return self.summarise(sresults)


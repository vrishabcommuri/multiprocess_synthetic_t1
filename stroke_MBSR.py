"""
refer to https://github.com/christianbrodbeck/Eelbrain/blob/master/examples/mouse/mouse.py
"""

from eelbrain import *
from eelbrain.pipeline import *
import eelbrain as eel
import mne
import itertools
from os.path import join, isfile


CONTROLS = ['R2678', 'R2680', 'R2688', 'R2692', 'R2799']

# Resting data is not collected the same way for all subjects.
# List of subjects with each session of resting data
# resting data {session}{visit}
# session:
#     - EO1 : eyes open before motor
#     - EO2 : eyes open after motor
#       command z will undo
#       R2679- have removed - redo EO2 fif and retry, if still an error then redo E)1; need to put back into the control group and resting
#       R2694- had to remove EO2 6m due to no clean segments

RESTING = {
    'restingEO1': CONTROLS,
    'restingEO2': CONTROLS,
}

class StrokeExp(MneExperiment):

    sessions = ['restingEO1', 'restingEO2', 'emptyroom']
    groups = {
        'c': Group(CONTROLS),
    }

    defaults = {
        'cov': 'emptyroom'
    }

    visits = ['', '6m']

    variables = {
        'cond': GroupVar(['c'])  # control or patient
    }

    # Pre-processing pipeline: each entry in `raw` specifies one processing step. The first parameter
    # of each entry specifies the source (another processing step or 'raw' for raw input data).
    raw = {
        # # Maxwell filter as first step (taking input from raw data, 'raw')
        'tsss': RawMaxwell('raw', st_duration=10, ignore_ref=True, st_correlation=0.9, st_only=True, bad_condition='warning'),
        'tsss-13-25-causal': RawFilter('tsss', 13, 25, phase='minimum'),
        'tsss-13-25-causal-EO1-ica': RawICA('tsss-13-25-causal', 'restingEO1', n_components=0.99),
        'tsss-13-25-causal-EO1-ica-apply': RawApplyICA('tsss-13-25-causal', 'tsss-13-25-causal-EO1-ica'),
        'tsss-13-25-causal-EO2-ica': RawICA('tsss-13-25-causal', 'restingEO2', n_components=0.99),
        'tsss-13-25-causal-EO2-ica-apply': RawApplyICA('tsss-13-25-causal', 'tsss-13-25-causal-EO2-ica'),

        'tsss-4-8-causal': RawFilter('tsss', 4, 8, phase='minimum'),
        'tsss-4-8-causal-EO1-ica': RawICA('tsss-4-8-causal', 'restingEO1', n_components=0.99),
        'tsss-4-8-causal-EO1-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-causal-EO1-ica'),
        'tsss-4-8-causal-EO2-ica': RawICA('tsss-4-8-causal', 'restingEO2', n_components=0.99),
        'tsss-4-8-causal-EO2-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-causal-EO2-ica'),
        'tsss-4-8-20comp-E01-ica': RawICA('tsss-4-8-causal', 'restingEO1', n_components=20),
        'tsss-4-8-20comp-E01-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-20comp-E01-ica'),
        'tsss-4-8-20comp-E02-ica': RawICA('tsss-4-8-causal', 'restingEO2', n_components=20),
        'tsss-4-8-20comp-E02-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-20comp-E02-ica'),
        'tsss-4-8-30comp-E01-ica': RawICA('tsss-4-8-causal', 'restingEO1', n_components=30),
        'tsss-4-8-30comp-E01-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-30comp-E01-ica'),
        'tsss-4-8-30comp-E02-ica': RawICA('tsss-4-8-causal', 'restingEO2', n_components=30),
        'tsss-4-8-30comp-E02-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-30comp-E02-ica'),
        'tsss-4-8-50comp-E01-ica': RawICA('tsss-4-8-causal', 'restingEO1', n_components=50),
        'tsss-4-8-50comp-E01-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-50comp-E01-ica'),
        'tsss-4-8-50comp-E02-ica': RawICA('tsss-4-8-causal', 'restingEO2', n_components=50),
        'tsss-4-8-50comp-E02-ica-apply': RawApplyICA('tsss-4-8-causal', 'tsss-4-8-50comp-E02-ica'),


        'tsss-1-4-causal': RawFilter('tsss', 1, 4, phase='minimum'),
        'tsss-1-4-causal-EO1-ica': RawICA('tsss-1-4-causal', 'restingEO1', n_components=0.99),
        'tsss-1-4-causal-EO1-ica-apply': RawApplyICA('tsss-1-4-causal', 'tsss-1-4-causal-EO1-ica'),
        'tsss-1-4-causal-EO2-ica': RawICA('tsss-1-4-causal', 'restingEO2', n_components=0.99),
        'tsss-1-4-causal-EO2-ica-apply': RawApplyICA('tsss-1-4-causal', 'tsss-1-4-causal-EO2-ica'),
        # Band-pass filter data between 1 and 40 Hz (taking raw data as input, 'tsss)
        # '1-40': RawFilter('raw', 1, 40, phase='minimum'),

        'tsss-1-45-causal': RawFilter('tsss', 1, 45, phase='minimum'),
        'tsss-1-45-causal-EO1-ica': RawICA('tsss-1-45-causal', 'restingEO1', n_components=0.99),
        'tsss-1-45-causal-EO1-ica-apply': RawApplyICA('tsss-1-45-causal', 'tsss-1-45-causal-EO1-ica'),
        'tsss-1-45-causal-EO2-ica': RawICA('tsss-1-45-causal', 'restingEO2', n_components=0.99),
        'tsss-1-45-causal-EO2-ica-apply': RawApplyICA('tsss-1-45-causal', 'tsss-1-45-causal-EO2-ica'),
        'tsss-delta-causal-EO1': RawFilter('tsss-1-45-causal-EO1-ica-apply', 1, 4, phase='minimum'),
        'tsss-theta-causal-EO1': RawFilter('tsss-1-45-causal-EO1-ica-apply', 4, 8, phase='minimum'),
        'tsss-alpha-causal-EO1': RawFilter('tsss-1-45-causal-EO1-ica-apply', 8, 13, phase='minimum'),
        'tsss-beta-causal-EO1': RawFilter('tsss-1-45-causal-EO1-ica-apply', 13, 25, phase='minimum'),
        'tsss-delta-causal-EO2': RawFilter('tsss-1-45-causal-EO2-ica-apply', 1, 4, phase='minimum'),
        'tsss-theta-causal-EO2': RawFilter('tsss-1-45-causal-EO2-ica-apply', 4, 8, phase='minimum'),
        'tsss-alpha-causal-EO2': RawFilter('tsss-1-45-causal-EO2-ica-apply', 8, 13, phase='minimum'),
        'tsss-beta-causal-EO2': RawFilter('tsss-1-45-causal-EO2-ica-apply', 13, 25, phase='minimum'),
    }


    epochs = {
        # A PrimaryEpoch definition extracts epochs directly from continuous data. The first argument
        # specifies the recording session from which to extract the data (here: 'CAT'). The second
        # argument specifies which events to extract the data from (here: all events at which the
        # 'stimulus' variable, defined above, has a value of either 'prime' or 'target').
        'restingEO1': PrimaryEpoch('restingEO1', tmin=0, tmax=90, samplingrate=100),
        'restingEO2': PrimaryEpoch('restingEO2', tmin=0, tmax=90, samplingrate=100),
    }

    # custom stimulus labels
    def label_events(self, ds):
        if ds.info['session'] == 'restingEO1' or ds.info['session'] == 'restingEO2':
            ds = ds.sub('trigger.isin([333, 172, 2048, 2049])')


        if ds.info['subject'] == 'R2809' and ds.info['visit'] == '':
            ds_old = ds
            ds = eel.load.unpickle("events_dataset_R2678.pickle")
            ds.info['subject'] = 'R2809'
            ds.info['session'] = ds_old['session']
            ds.info['visit'] = ''
            ds['trigger'] = eel.Var([2049, 1], name='trigger')
            ds['i_start'] = eel.Var([1000*5, 1], name='i_start')

        return ds



root_dir = "/Users/marshlab/Desktop/recon_all_clinical/"

e = StrokeExp(root_dir)
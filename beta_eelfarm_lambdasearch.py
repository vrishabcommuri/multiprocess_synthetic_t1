import mne

import nlgc

import numpy as np
import os
import pathlib

os.sys.path.append(str(pathlib.Path().cwd().resolve().parent / "Code"))
import stroke_MBSR
import eelfarm
import itertools

import warnings

# warnings.filterwarnings('ignore')

import pickle
import eelbrain
import pathlib
import synthesize_t1 as st

kwargsE01 = {'raw': 'tsss-beta-causal-EO1', 'parc': 'aparc'}
kwargsE02 = {'raw': 'tsss-beta-causal-EO2', 'parc': 'aparc'}

recoregsubs = ['R2678', 'R2680', 'R2688', 'R2692', 'R2799']

def find_lambda(sub, v, sess):
    subject_vec = [sub]
    visit_vec = [v]
    session = sess

    time_start = 5
    time_end = 85

    # Now we will run the algorithm

    for subject in subject_vec:
        for visit in visit_vec:
            print(subject, visit, session)
            print("start")
            stroke_MBSR.e.set(subject=subject, visit=visit, session=session)
            print("loading sources")
            src_target = stroke_MBSR.e.load_src(src='ico-1')
            src_origin = stroke_MBSR.e.load_src(src='ico-4')

            print("loading forward")

            try:
                forward = stroke_MBSR.e.load_fwd(src='ico-4', ndvar=False)
            except RuntimeError as ex:
                factor = 1.1
                print(f"{subject} {visit} got runtime error {ex} inner skull is likely too small. scaling bem surface by {factor}x")
                scaled_bemsol = st.scale_bem(subject, "./mri", factor)
                if '6m' in v:
                    visit = " 6m"
                else:
                    visit = ""
                rawfile = f"./meg/{subject}/{subject}_{sess}{visit}-raw.fif"
                transfile = f"./meg/{subject}/{subject}{visit}-trans.fif"
                forward = mne.make_forward_solution(rawfile, transfile, src_origin, bem=scaled_bemsol, ignore_ref=True)

            print("converting forward")
            forward = mne.convert_forward_solution(forward, force_fixed=True)
            print("forward loaded")

            # original sampling frequency = 1000 but with 10 decim now 100 (has to be greater than 2x40(highest frequency) but want it lower than 1000 as that is really short and unlikely to see links over that time given only 60 seconds (60/1000)
            ds = stroke_MBSR.e.load_epochs(subject, decim=10, ndvar=False, reject=False)

            epochs = ds['epochs']
            evoked = epochs[0].average()

            # evoked = evoked.filter(1, 4, phase='minimum')
            # evoked = evoked.decimate(2, offset=1)  # 50 Hz
            evoked = evoked.resample(sfreq=25, npad=0)
            evoked.crop(tmin=5, tmax=85)

            cov = stroke_MBSR.e.load_cov(raw='tsss-beta-causal-EO1')

            print("epochs and cov loaded")

            # lam = [1, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01]
            lam = [0.05, 0.063, 0.079, 0.1, 0.125, 0.158, 0.2]

            print("start NLGC")
            dst = f"./results/4eig2ord/[{subject}]-[visit={visit}]-[session={session}]-[beta]-[fullmodel].p"

            if pathlib.Path(dst).is_file():
                print(f"{dst} exists; continuing")
                continue

            server.put(dst, nlgc.nlgc_map, subject, evoked, forward, cov, src_target, use_es=False,
                       order=2, n_eigenmodes=4, patch_idx=list(range(84)),
                       lambda_range=lam, max_iter=500, max_cyclic_iter=3,
                       tol=1e-5, sparsity_factor=0.0, var_thr=1.0, cv=5)


if __name__ == "__main__":
    # this may change so if it doesn't work go to system settings -> network -> WiFi -> details -> TCP/IP -> IP Address
    # and paste the IP into the address field
    server = eelfarm.start_server(address="10.194.193.118")
    # server = eelfarm.start_server('localhost')

    eelbrain.gui.run(block=False)

    for session in stroke_MBSR.RESTING:
        if "EO1" in session:
            stroke_MBSR.e.set(**kwargsE01)
        else:
            stroke_MBSR.e.set(**kwargsE02)

        if '6m' in session:
            visit = '6m'
            s = session[:-2]
        else:
            visit = ''
            s = session

        for sub in stroke_MBSR.RESTING[session]:
            if sub not in recoregsubs:
                continue
            try:
                find_lambda(sub, visit, s)
            except Exception as e:
                print(sub, visit, session, " encountered an error ", e)
                continue
            # except IndexError:
            #     print(sub, visit, session, " encountered a missing session.")
            #     continue

    print("finished")

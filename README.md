# Instructions for running “clinical recon all” (synthetic T1 from clinical MRI)

# Setup

Lines beginning with “%” denote code that should be typed into the terminal.

The lines below set up the environment and path variables for running freesurfer.

% conda activate eelbrain

% export FREESURFER_HOME=/Applications/freesurfer/8.0.0/

% source $FREESURFER_HOME/SetUpFreeSurfer.sh

If you ever get “RuntimeError: The FREESURFER_HOME environment variable is not set.” The above are the lines to run

# Clinical MRI Conversion

The goal of this first step is to convert clinical MR images which are in DICOM format into Nifti (.nii).

The DICOM format can be finnicky and care must be taken when downloading the data to ensure that all slices are present. Let the data completely load before downloading. Diffusion AX files seem to work best for this as they contain the full cortex without missing slices.

DICOM files are saved to a folder, in this case ~/Desktop/MRIs_for_conversion. This is the root folder. Navigate the terminal window, set up as above, to this directory:

% cd ~/Desktop/MRIs_for_conversion/

Run the preprocessing script. “% >” indicates commands executed within the eelbrain interactive session.

% eelbrain

% > import synthesize_t1 as st

% > st.preprocess_mris(mridir=“/Users/marshlab/Desktop/MRIs_for_conversion”)

This command will attempt to automatically process all of the DICOM files within the root folder (mridir) and will create a subfolder called “outputs” to which the processed .nii files will be saved.

Files that are not able to be processed will be printed in the terminal with the message: “FAILED with exit code:” followed by the exit code. This may be useful for debugging. The most common source of these errors is improperly downloaded MRI files, which have missing or repeated slices. The way that the DICOM processing code operates relies on slice ordering being sequential with no missing or repeated slices. If that assumption is violated, things may break. The fix is generally to try redownloading the file, or to use a different image, perhaps the Flair. If this fails, then it may be possible to process the file by writing some bespoke code to manually reorder slices in the DICOM file before conversion to .nii.

# Synthesize T1s using Eelfarm and the Cluster Machines

First we will outline the general procedure by which .nii files are processed by freesurfer; that is, how they are converted from “raw” .nii files to “processed” MRI folders that contain brain extracted surfaces, parcellations, transforms, and the like.

1.  The process begins with the .nii files that live in the output directory defined above. These files are managed by a “server” computer – typically the main lab computer – that sends each .nii file to a “worker” computer that will convert this raw .nii file into a processed MRI folder.
2.  On the worker machine, the conversion happens by placing the nii files within a folder called “work” and then running the “runall.csh” script. This is all handled automatically, but if the script encounters any kind of error, then:
    1.  ERRORS WILL BE WRITTEN TO A LOG ON THE WORKER MACHINE and a
    2.  4 BYTE FILE SAVED TO THE SERVER (python value of None).
    3.  If errors are encountered, the log should be inspected and possibly the .nii file plotted using mrview or fsleyes.
    4.  Generally, such errors can be circumvented by using a different scan (e.g., Flair instead of Diffusion AX) from the same subject. The code just picks the first nii file it sees from ~/Desktop/MRIs_for_conversion/output/subject_id, which may be corrupted or incomplete. An easy way to check is to open fsleyes and try to load each nii volume. The corrupted one won’t load and can be deleted along with all ancillary files. See also the grey text in the above clinical MRI conversion section for a bit more discussion.

1.  The transfer back of this MRI folder from the worker to the server is done by compressing the folder using the “tar” utility and then sending the tarred file to the server. Tarred files are serialized as pickle files for sending, so the server will receive .pickle files, not .tar files.

Recap:

…/MRIs_for_conversion/output contains the .nii files from which we want to synthesize T1s

…/recon_all_clinical/work/ contains the log files and synthesized T1s on the worker machine

…/recon_all_clinical/processed/ contains the synthesized T1s in pickle format

Different commands are required to configure the server and workers to run.

SERVER:

% cd ~/Desktop/recon_all_clinical/

% eelbrain

% > run eelfarm_run_synth.py

If the script complains that it cannot assign the requested IP address, then it has changed. Find the new one by going into wifi settings: System Settings 🡪 Wi-Fi 🡪 hopkins 🡪 details 🡪 IP Address

If the script says “OSError: \[Errno 48\] Address already in use” you will need to exit the server in whatever terminal it is running (may have to Ctrl-C a few times) and restart it.

If the script says there are pending jobs, but you believe there shouldn’t be any, you can clear the job queue by running in the same session % > server.remove_broken_job(list(range(2000))) which will clear all job IDs up to 2000 (which should be all of them). You may have to Ctrl-C a few times after running this to get the server to quit.

If the script says that the pickle file for this subject exists, but it is only 4 bytes, delete the file and requeue the job.

WORKER:

% conda activate eelbrain

% export FREESURFER_HOME=/Applications/freesurfer/8.0.0/

% source $FREESURFER_HOME/SetUpFreeSurfer.sh

% cd ~/Desktop/recon_all_clinical/work

% eelfarm start --foreground server_ip_address

When finished the ~/Desktop/recon_all_clinical/processed/ directory on the server should be filled with pickle files, one per subject, of substantial size (~500 MB each). Anything on the order of ~1KB or less should be inspected, particularly the logs on the worker machine) and then all files deleted (e.g., in …/recon_all_clinical/processed and …/recon_all_clinical/work) and then the subject re-run. See 2 (a-d) above for fixes for undersized files.

# Postprocessing and BEM Surface Creation

In order to run MEG and EEG source analysis, a model of the various intervening tissue layers between the brain and sensors must be created. This is done by creating what is called a “boundary element model” (BEM) which defines the various boundaries between tissue layers.

These boundaries are identified using an image processing technique called a watershed algorithm, which treats the image intensity values as analogous to surface heights in a mountain range. The algorithm floods the image and then looks at the various basins that form and the watershed lines connecting basins together to identify consistent topological features.

The topological analogy is useful in understanding failure modes when postprocessing synthetic MRIs which, because they are synthesized using a deep net trained on reconstructing only neural tissue, can often manifest artifactual image intensities outside of the skull boundary. These spurious intensity values are often small, but can interfere with the watershed algorithm, particularly in its ability to define the outer skin boundary, which can result in a cube-shaped outer skin that is wrapped around the entire image extent. An example is shown below

To create the BEM surfaces we run the following script:

IMPORTANT: ensure that the subject numbers are specified in postprocess_all.py before running.

% eelbrain

% > run postprocess_all.py

## Fixing Cuboid Outer Skin Surfaces

During coregistration, you may find that that the outer skin BEM solution looks cuboid like above. This is caused by nonzero voxel values that persist outside the head boundary that arise during synthesization (discussed above).

 

Left: artifactual translucent regions outside skull. Right: translucent regions masked out

In cases where this happens, the following steps can be applied to correct matters:

1.  Delete the incorrect bem surfaces in …/recon_all_clinical/mri/subject_id/bem/ (everything in this folder can be deleted as it will all be regenerated in the next step).
2.  Run the following commands:

% eelbrain

% > import synthesize_t1 as st

% > import mne

% > st.t1_mask_remove_background(subject_id, mridir, percentile)

THIS SAVES A FILE T1_masked.mgz TO ~/Desktop/recon_all_clinical/mri/subject_id/mri/ RENAME THIS TO T1.mgz when you are satisfied.

Then the BEM surfaces can be recalculated:

% > mne.bem.make_watershed_bem(subject_id, mridir, overwrite=True, show=False, atlas=True, preflood=0)

An example of parameter values are subject_id=“R3001”, mridir=“~/Desktop/recon_all_clinical/mri”, percentile=80.

When called, the function will plot the planar views of the original image as well as the mask applied by the chosen percentile threshold. The goal is to filter out the low-valued background “ped estal” behind the brain image. Tweak the percentile (roughly between 75 and 90 should be correct, corresponding to dropping the lowest 25-10% of voxel values in the image – note that only ones outside the head boundary are dropped)  

Top: unmasked T1. Middle: Mask at percentile=85. Bottom: masked T1.

You can run “% st.t1_mask_remove_background(subject_id, mridir, percentile)” many times in succession. It will overwrite T1_masked.mgz. The images may not close until you are done with the session and exit.

Then coregistration can then proceed:

% mne coreg -d ~/Desktop/recon_all_clinical/mri

Left: bem outer skin before masking. Right: bem outer skin after masking

#!/bin/tcsh

# Check if an argument was provided
if ( $#argv == 0 ) then
    echo "Usage: ./run_recon.sh <subject_prefix>"
    echo "Example: ./run_recon.sh 12345"
    exit 1
endif

set indir = "/Users/marshlab/Desktop/recon_all_clinical/work/"

set sdir = "/Users/marshlab/Desktop/recon_all_clinical/work/"

set recon = "/Applications/freesurfer/8.0.0/bin/recon-all-clinical-corrected.sh"

set target_id = $1

foreach f ($indir/${target_id}*.nii*)

    if ( ! -e $f ) then
        echo "Error: No file found matching ${target_id} in $indir"
        continue
    endif

    set fname = `basename $f`

    # Create a timestamped log file
    set log = "${target_id}.log"

    echo "Processing $fname with subject ID ${target_id}"
    echo "Logging to $log"

    # Run recon-all and capture stdout + stderr
    tcsh $recon \
        -i $f \
        -subjid $target_id \
        -sdir $sdir \
        -threads 30 \
        >& $log

end

#!/bin/tcsh

# Check if an argument was provided
if ( $#argv == 0 ) then
    echo "Usage: ./run_recon.sh <subject_prefix>"
    echo "Example: ./run_recon.sh 12345"
    exit 1
endif

set indir = "/export/vrishab/multiprocess_synthetic_t1/work/"

set sdir = "/export/vrishab/multiprocess_synthetic_t1/work/"

set recon = "/export/vrishab/freesurfer/bin/recon-all"

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
        -sd $sdir \
	-all \
        >& $log

end

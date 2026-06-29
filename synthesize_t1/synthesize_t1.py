import os
import pathlib
import os
import pydicom
import numpy as np
import pickle
import nibabel as nib
import eelbrain as eel
import mne
import matplotlib.pyplot as plt
from scipy.ndimage import label

def synthesize(subject, img, affine):
    serialized_mri_log = None

    if not pathlib.Path(f"{subject}.tar").exists():
        try:
            img = nib.Nifti1Image(img, affine)
        except np.linalg.LinAlgError as e:
            errmsg = f"job for subject {subject} failed to save nii file, likely because the data are corrupted. redownload required. error: {e}"
            with open(f"./{subject}.log", 'w') as f:
                f.write(errmsg)
            return

        subject = subject[:5]
        print("start", subject)
        # data is a serialized nii file
        # pathlib.Path(f"./{subject}").mkdir(parents=True, exist_ok=True)
        nib.save(img, f"./{subject}.nii")

        # creates subject.log and subject/ a directory with processed subject data
        os.system(f"./runall.csh {subject}")

        os.system(f"tar -cvf {subject}.tar {subject}")

        with open(f"{subject}.log", 'rb') as f:
            serialized_mri_log = f.read()

    with open(f"{subject}.tar", 'rb') as f:
        serialized_mri = f.read()

    return serialized_mri, serialized_mri_log


def preprocess_mris(mridir="/Users/marshlab/Desktop/MRIs_for_conversion/"):
    root = pathlib.Path(mridir)
    mrpaths = []

    for fp in root.glob("*/DICOMDIR"):
        print(fp)
        ds = pydicom.dcmread(fp)

        for record in ds.DirectoryRecordSequence:
            if record.DirectoryRecordType == "IMAGE":
                mrpaths.append([fp.parent / record.ReferencedFileID[0] / record.ReferencedFileID[1]])

    mrpaths = list(np.unique(mrpaths))

    for pth in np.unique(mrpaths):
        print(f"converting {pth}")
        sub = pth.parent.parent.name  # dir structure is like RXXXX/AAAABBBB/CCCCDDDD
        (root / "stage" / f"{sub}").mkdir(parents=True, exist_ok=True)

        # stage outputs
        exitcode = os.system(f"dcm2niix -o {str(root / 'stage' / sub)} {str(pth)}")

        if exitcode:
            # failed; delete staged files
            print(f"\n\n{sub} {pth.parent.name} {pth.name} FAILED with exit code: {exitcode}\n\n")
            os.system("rm -rf /Users/marshlab/Desktop/MRIs_for_conversion/stage/")
        else:
            print(f"{sub} {pth.parent.name} {pth.name} SUCCESS")
            (root / "outputs" / f"{sub}").mkdir(parents=True, exist_ok=True)
            os.system(
                f"mv {str(root / 'stage' / sub / '*')} {str(root / 'outputs' / sub)}")

        os.system(f"rm -rf {str(root / 'stage')}")


def postprocess_mris(subject, mridir, frompickle=True):
    mridir = pathlib.Path(mridir)
    # transfer from processed dir to here
    if frompickle:
        tarfile, log = eel.load.unpickle(f"/Users/marshlab/Desktop/recon_all_clinical/processed/{subject}.pickle")
        # (mridir / subject).mkdir(parents=True, exist_ok=True)
        with open(f"{str(mridir / f'{subject}.tar')}", 'wb') as f:
            f.write(tarfile)

    os.system(f"tar -xvf {str(mridir / f'{subject}.tar')} -C {str(mridir)}")
    os.system(f"rm {str(mridir / f'{subject}.tar')}")

    # synthSR wm intensities are not normalized (~110). watershed may break unless we renormalize
    os.system(
        f"mri_convert --conform --out_data_type float {str(mridir / subject / 'mri' / 'synthSR.raw.mgz')} {str(mridir / subject / 'mri' / 'T1_conf.mgz')}")
    os.system(
        f"mri_normalize {str(mridir / subject / 'mri' / 'T1_conf.mgz')} {str(mridir / subject / 'mri' / 'T1.mgz')}")

    print("creating bem surfaces")
    mne.bem.make_watershed_bem(subject, mridir, overwrite=True, show=False, atlas=True, preflood=0)


def t1_mask_remove_background(subject, mridir, percentile=80):
    mridir = pathlib.Path(mridir)
    img = nib.load(f"{str(mridir / subject / 'mri' / 'T1.mgz')}")
    data = img.get_fdata()

    data0 = data - np.percentile(data, percentile)  # identify 'pedestal' behind brain image
    mask = data0 < 0  # isolate pedestal

    # segment image; naive thresholding above will leave voids of low signal
    # value inside the head. use the largest contiguous segment (the pedestal)
    # as the mask and leave everything else
    lab, _ = label(mask)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    mask = ~(lab == sizes.argmax())  # invert to get head mask

    x = mask.shape[0] // 2
    y = mask.shape[1] // 2
    z = mask.shape[2] // 2

    fig, axes = plt.subplots(3, 3, figsize=(10, 10))

    axes[0, 0].imshow(data[x, :, :].T, cmap="Reds", origin="lower")
    axes[0, 0].set_title("unmasked T1: Sagittal")

    axes[0, 1].imshow(data[:, y, :].T, cmap="Reds", origin="lower")
    axes[0, 1].set_title("Coronal")

    axes[0, 2].imshow(data[:, :, z].T, cmap="Reds", origin="lower")
    axes[0, 2].set_title("Axial")


    axes[1, 0].imshow(mask[x, :, :].T, cmap="Reds", origin="lower")
    axes[1, 0].set_title("mask: Sagittal")

    axes[1, 1].imshow(mask[:, y, :].T, cmap="Reds", origin="lower")
    axes[1, 1].set_title("Coronal")

    axes[1, 2].imshow(mask[:, :, z].T, cmap="Reds", origin="lower")
    axes[1, 2].set_title("Axial")



    axes[2, 0].imshow(data[x, :, :].T * mask[x, :, :].T, cmap="Reds", origin="lower")
    axes[2, 0].set_title("masked T1: Sagittal")

    axes[2, 1].imshow(data[:, y, :].T * mask[:, y, :].T, cmap="Reds", origin="lower")
    axes[2, 1].set_title("Coronal")

    axes[2, 2].imshow(data[:, :, z].T * mask[:, :, z].T, cmap="Reds", origin="lower")
    axes[2, 2].set_title("Axial")

    plt.tight_layout()
    plt.show(block=False)
    plt.pause(2)

    out = nib.MGHImage(
        data * mask,
        affine=img.affine,
        header=img.header
    )

    nib.save(out, f"{str(mridir / subject / 'mri' / 'T1_masked.mgz')}")
    return


def scale_bem(subject, mridir, factor):
    surfs = mne.make_bem_model(subject, ico=4, conductivity=[0.3], subjects_dir=mridir)
    for surf in surfs:
        surf['rr'] *= factor

    bemsol = mne.make_bem_solution(surfs)
    return bemsol




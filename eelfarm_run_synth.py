import synthesize_t1 as st
import eelfarm
import eelbrain
import pathlib
import pickle
import nibabel as nib

if __name__ == '__main__':
    ip = "10.229.43.52"
    indir = "/Volumes/Expansion/strokedata/alzheimers/mri/"
    outdir = "/Volumes/Expansion/strokedata/alzheimers/processed"
    is_synthetic = False # these are real T1s
    
    server = eelfarm.start_server(address=ip)
    eelbrain.gui.run(block=False)

    farmed_subs = []
    for fp in pathlib.Path(indir).glob("**/*.nii*"):
        sub = fp.parent.name
        # an nii file for this subject was already sent
        if sub in farmed_subs:
            continue
        farmed_subs.append(sub)

        img = nib.load(fp)

        print(f"start synthesize {sub}")
        dst = f"{str(pathlib.Path(outdir) / f'{sub}.pickle')}"

        if pathlib.Path(dst).is_file():
            print(f"{dst} exists; continuing")
            continue

        server.put(dst, st.synthesize, sub, img.get_fdata(), img.affine, synthetic=is_synthetic)

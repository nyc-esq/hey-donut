import os, sys
from mmap_ninja.ragged import RaggedMmap
from microwakeword.audio.augmentation import Augmentation
from microwakeword.audio.clips import Clips
from microwakeword.audio.spectrograms import SpectrogramGeneration

AUG_PROBS = {
    "SevenBandParametricEQ": 0.1, "TanhDistortion": 0.1, "PitchShift": 0.1,
    "BandStopFilter": 0.1, "AddColorNoise": 0.1, "AddBackgroundNoise": 0.75,
    "Gain": 1.0, "RIR": 0.5,
}
BG = [p for p in ['/w/augment/background'] if os.path.isdir(p) and os.listdir(p)]
IR = [p for p in ['/w/augment/mit_rirs'] if os.path.isdir(p) and os.listdir(p)]
print(f"  impulse dirs: {IR}\n  background dirs: {BG}", flush=True)

def build(input_dir, out_root):
    print(f"\n=== features for {input_dir} -> {out_root}", flush=True)
    clips = Clips(input_directory=input_dir, file_pattern='*.wav',
                  max_clip_duration_s=None, remove_silence=False,
                  random_split_seed=10, split_count=0.1)
    aug = Augmentation(augmentation_duration_s=3.2,
                       augmentation_probabilities=AUG_PROBS,
                       impulse_paths=IR, background_paths=BG,
                       background_min_snr_db=-5, background_max_snr_db=10,
                       min_jitter_s=0.195, max_jitter_s=0.205)
    for split, split_name, rep, slide in (("training","train",2,10),
                                          ("validation","validation",1,10),
                                          ("testing","test",1,1)):
        od = os.path.join(out_root, split)
        os.makedirs(od, exist_ok=True)
        spec = SpectrogramGeneration(clips=clips, augmenter=aug,
                                     slide_frames=slide, step_ms=10)
        print(f"  -> {split}", flush=True)
        RaggedMmap.from_generator(
            out_dir=os.path.join(od, 'wakeword_mmap'),
            sample_generator=spec.spectrogram_generator(split=split_name, repeat=rep),
            batch_size=100, verbose=True)

build('/w/samples/positive',          '/w/features/positive')
build('/w/samples/adversarial_flat',  '/w/features/adversarial')
print("\nFEATURES-DONE", flush=True)

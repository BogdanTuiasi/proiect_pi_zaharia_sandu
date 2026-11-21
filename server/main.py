from communication.server import run_server
from image_processing.filters import accentuate_contrast
from image_processing.region_detection import proc, reset_regions
from image_processing.translator import translator

if __name__ == "__main__":
    # process_frame = accentuate_contrast(75, 180, 20, 235, 256)
    process_frame = proc
    target_language = "ro"
    translator.set_target_language(target_language)
    run_server(
        process_frame,
        fps=60,
        target_language=target_language,
        reset_process_state=reset_regions,
    )

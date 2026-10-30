from communication.server import run_server
from image_processing.filters import accentuate_contrast, proc

if __name__ == "__main__":
    # process_frame = accentuate_contrast(75, 180, 20, 235, 256)
    process_frame = proc
    run_server(process_frame)

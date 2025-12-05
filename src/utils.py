import subprocess

def merge_overlay(input_video, overlay_video, output_video):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", overlay_video,
        "-filter_complex", "[0:v][1:v] overlay=0:0",
        "-c:a", "copy",
        output_video
    ]
    subprocess.run(cmd, check=True)

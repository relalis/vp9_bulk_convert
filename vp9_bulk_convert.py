#!/usr/bin/env python

import os
import subprocess
import json
import time
import difflib
import argparse
import math
import re
from tqdm import tqdm

## vspipe --arg in_filename=S04E06.webm --arg display_fps=60 -c y4m motioninterpolation.vpy -|ffmpeg -i - -i S04E06.webm -map 0 -map 1:a -crf 30 test.webm
## https://askubuntu.com/questions/1107782/how-to-use-gpu-acceleration-in-ffmpeg-with-amd-radeon
## https://trac.ffmpeg.org/wiki/Hardware/VAAPI

class file_conversion:
    def __init__(self,
    dry_run = False,
    two_pass_conv = False,
    cleanup_conv_files = False,
    ignore_prev_conv = False,
    strict_conv_verification = False,
    path = ".",
    crf = 30):
        self.tpconv = two_pass_conv
        self.cleanup_after = cleanup_conv_files
        self.nocheck = ignore_prev_conv
        self.strict_check = strict_conv_verification
        self.path = path
        self.dry_run = dry_run
        self.filelist = []

        ## ffmpeg fun stuff
        self.crf = crf
        self.test_params = ""
        #self.test_params = "-quality realtime -speed 5 -threads 8 -row-mt 1 -tile-columns 2 -frame-parallel 1 -qmin 4 -qmax 48"

    def probe_file(self, fname):
        cmd = f'ffprobe -v quiet -print_format json -show_format -show_streams "{self.path}/{fname}"'
        try:
            out = json.loads(subprocess.getoutput(cmd))
            return out
        except ValueError:
            print(f"A ValueError exception was raised while trying to probe for file {fname}.")
            return None


    def __verify_previous_conv(self, original, attempt):
        unconverted_files = []
        for og_file in original:
            try:
                matched_file = difflib.get_close_matches(og_file, attempt)
                if (len(matched_file) == 0) or (os.path.splitext(matched_file[0])[0] != os.path.splitext(og_file)[0]):
                    ## difflib should match the files as closely as possible- assuming the filename
                    ## is identical with only a difference in extension, a negative result means
                    ## that the temp conversion doesn't exist. There may be a more efficient way
                    ## to do this, but this just gets the job done for now.
                    unconverted_files.append(og_file)
                else:
                    if self.strict_check:
                        try:
                            og = self.probe_file(og_file)['format']
                            if og is None:
                                print(f"probing {og_file} failed")
                        except Exception as e:
                            print(f"There was an error while probing {og_file}: {e}")
                            continue
                        try:
                            pc = self.probe_file(matched_file[0])['format']
                            if ('duration' not in pc) or (not math.isclose(float(og['duration']), float(pc['duration']), rel_tol=1e-5)):
                                print(f"Probing indicated that {og_file} needs to be reconverted.")
#                                print(pc)
#                                print(float(pc['duration']))
#                                print(og)
#                                print(float(og['duration']))
#                                print("=============================\n\n")
                                unconverted_files.append(og_file)
                        except KeyError:
                            print(f"Probing {matched_file[0]} failed, reconverting the original")
                            unconverted_files.append(og_file)
                    else:
                        unconverted_files.append(og_file)
            except Exception as e:
                print(f"Caught exception on {og_file} {type(e)}: {e}")
        return unconverted_files

    def get_media_files(self):
        contents = os.listdir(self.path)
        first_pass = [x for x in contents if ((x[:1] != '.') and ('srt' not in x) and (os.path.basename(__file__) != x) and ('log' not in x))]
        prev_conv = [x for x in first_pass if 'webm' in x]
        original_file = [x for x in first_pass if 'webm' not in x]

        if (len(prev_conv) > 0) and (self.nocheck is False):
            self.filelist = self.__verify_previous_conv(original_file, prev_conv)
        else:
            self.filelist = first_pass
        return self.filelist

    def convert(self, fname):
        base_name = os.path.splitext(fname)[0]
        if not self.dry_run:
            if self.tpconv:
                print(f"Performing two-pass conversion on {fname}")
                subprocess.run(f'ffmpeg -hide_banner -i "{self.path}/{fname}" -c:v libvpx-vp9 -b:v 0 -crf {self.crf} -pass 1 -an -f null /dev/null', shell=True)
                subprocess.run(f'ffmpeg -loglevel warning -hide_banner -i "{self.path}/{fname}" -c:v libvpx-vp9 -b:v 0 -crf {self.crf} -pass 2 -c:a libopus -ac 6 "{self.path}/{base_name}.webm"', shell=True)
            else:
                ffprobe_info = self.probe_file(fname)
                if ffprobe_info and 'format' in ffprobe_info:
                    total_duration = float(ffprobe_info['format']['duration'])
                    pbar = tqdm(total=total_duration, unit='s', unit_scale=True, bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:10}{r_bar}', position=0)
                    ffmpeg_process = subprocess.Popen(f'ffmpeg -y -hide_banner -loglevel error -stats -i "{self.path}/{fname}" -map 0:a -map 0:v -c:v libvpx-vp9 -b:v 3M -crf {self.crf} {self.test_params} -c:a libopus -ac 6 "{self.path}/{base_name}.webm"', 
shell=True, stderr=subprocess.PIPE, bufsize=10**8, universal_newlines=True)
                    for line in ffmpeg_process.stderr:
                        time_info = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                        if time_info:
                            current_time = time_info.group(1)
                            current_time_seconds = sum(float(x) * 60**i for i, x in enumerate(reversed(current_time.split(':'))))
                            pbar.update(current_time_seconds - pbar.n)
                    pbar.close()
                    ffmpeg_process.wait()
                else:
                    subprocess.run(f'ffmpeg -y -hide_banner -loglevel error -stats -i "{self.path}/{fname}" -map 0:a -map 0:v -c:v libvpx-vp9 -b:v 3M -crf {self.crf} {self.test_params} -c:a libopus -ac 6 "{self.path}/{base_name}.webm"', shell=True)

        else:
            print(f"Dry run specified, not converting {fname}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--two-pass', help='Two-pass conversion', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--ignore_prev_conv', help='Ignore failed previous conversions', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--strict_mode', help='Strict conversion verification', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--cleanup', help='Cleanup originals after conversion (not recommended)', action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--crf', help='CRF value', default=30, type=int)
    parser.add_argument('--path', help='Path of folder containing media files. Defaults to current directory.', default='.')
    parser.add_argument('--dry_run', help='Dry run (no conversion takes place)', action=argparse.BooleanOptionalAction, default=False)

    args = parser.parse_args()

    test = file_conversion(crf=args.crf, dry_run = args.dry_run, two_pass_conv = args.two_pass, cleanup_conv_files = args.cleanup, ignore_prev_conv = args.ignore_prev_conv, strict_conv_verification = args.strict_mode, path = args.path)
    mf = test.get_media_files()

    print(mf)
    iter = 1
    for x in mf:
        print(f"[{iter}/{len(mf)}] Converting {x}")
        iter = iter + 1
        test.convert(x)


# vp9_bulk_convert

vp9_bulk_convert is a Python script that utilizes ffmpeg to convert all media/movie files in a specified path to VP9. By default, this script converts all files in the current directory; it does not recursively search for media files. By specifying `--path {PATH_TO_SCAN}`, it can convert all files in a specific path.

Currently this script converts media files in one pass, which is faster at the cost of compression. Two-pass conversion may compress resulting media files more efficiently, but requires much more time; it can be invoked with the `--two-pass` option, but has been mostly untested. Hardware encoding support (such as 8-bit VP9 in Intel Kaby Lake and higher) may be added in the future.

## Usage

Usage information is printed with `-h` or `--help`. By default, all options except for `--strict_mode` are disabled and crf is 30.

```

usage: vp9_bulk_convert.py [-h] [--two-pass] [--ignore_prev_conv] [--strict_mode] [--cleanup] [--crf CRF] [--path PATH] [--dry_run]

options:
  -h, --help            show this help message and exit
  --two-pass, --no-two-pass
                        Two-pass conversion
  --ignore_prev_conv, --no-ignore_prev_conv
                        Ignore failed previous conversions
  --strict_mode, --no-strict_mode
                        Strict conversion verification
  --cleanup, --no-cleanup
                        Cleanup originals after conversion (not recommended)
  --crf CRF             CRF value
  --path PATH           Path of folder containing media files. Defaults to current directory.
  --dry_run, --no-dry_run
                        Dry run (no conversion takes place)

```

## Example

```
$ python vp9_bulk_convert.py
Probing indicated that S03E01.mkv needs to be reconverted.
['S03E01.mkv', 'S03E04.mkv', 'S03E05.mkv', 'S03E08.mkv', 'S03E12.mkv', 'S03E11.mkv', 'S03E02.mkv']
[1/7] Converting S03E01.mkv
       7%|▋         | 187/2.61k [14:52<4:10:40, 6.21s/s] 
```
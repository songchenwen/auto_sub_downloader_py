import sys
import os

input_dir = None
output_dir = None
if len(sys.argv) > 1:
    input_dir = str(sys.argv[1])
if len(sys.argv) > 2:
    output_dir = str(sys.argv[2])
if input_dir is None:
    input_dir = str(os.environ.get('INPUT', '/input'))
if output_dir is None:
    output_dir = str(os.environ.get('OUTPUT', '/output'))
interval = float(os.environ.get('INTERVAL', 0))
need_srt = (str(os.environ.get('NEED_SRT', 'true')).lower() == 'true')
need_aac = (str(os.environ.get('NEED_AAC', 'true')).lower() == 'true')
old_days = (int(os.environ.get('OLD_DAYS', 0)))
sub_available_delay = int(os.environ.get('SUB_AVAILABLE_DELAY', 2))

debug = False


print('from %s to %s interval %f\nneed srt %s, need aac %s' % (input_dir, output_dir, interval,
    need_srt, need_aac))

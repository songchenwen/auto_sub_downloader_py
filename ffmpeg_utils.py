import os
from collections import OrderedDict
from ffmpy import FFmpeg

def combine_file(filename, subs, output):
    inputs_dict = [(filename, None)]
    out_params = ['-map 0:v', '-map 0:a']

    for i in range(0, len(subs)):
        sub = subs[i]        
        inputs_dict.append((sub, None))
        ext = os.path.splitext(sub)[1]
        out_params.append("-map %d" % (i + 1))
        out_params.append("-metadata:s:s:%d language=chi" % i)
        out_params.append("-metadata:s:s:%d title=chi.%d%s" % (i, i + 1, ext))
    out_params.extend(['-map 0:s?', '-c copy'])
    out_params = " ".join(out_params)

    inputs_dict = OrderedDict(inputs_dict)

    ff = FFmpeg(
        inputs=inputs_dict,
        outputs={output: out_params}
        )
    print(ff.cmd)
    try:
        devnull = open(os.devnull, 'w')
        ff.run(stderr=devnull)
        devnull.close()
        return output
    except Exception as e:
        print(e)
        return None

import subprocess
import re

def octescape_decode(s):
    def rep(m):
        vs = [int(v, 8) for v in m.group(0).split('\\')[1:]]
        return bytes(vs).decode('utf-8')
    return re.sub('(\\\\[0-9]{3})+', rep, s)

def execute(args, cwd, split = True, octescape=True, binary=False):
    output = subprocess.check_output(args, cwd=cwd)
    if binary:
        return output
    try:
        output_text = output.decode('utf-8')
    except UnicodeDecodeError as e:
        return output
    if octescape:
        output_text = octescape_decode(output_text)
    if not split:
        return output_text
    lines = output_text.split('\n')
    return lines

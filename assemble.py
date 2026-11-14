"""Join rendered rounds without re-encoding the picture and add MP4 chapters."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

output = Path(sys.argv[1]).resolve()
rounds = [Path(arg).resolve() for arg in sys.argv[2:]]
with tempfile.TemporaryDirectory() as directory:
    work = Path(directory)
    chapters = [';FFMETADATA1', 'title=Unitree G1 Sparring', 'artist=MuJoCo']
    listing = []
    cursor = 0
    for i, file in enumerate(rounds, 1):
        probe = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                         'format=duration', '-of', 'json', str(file)])
        duration = float(json.loads(probe)['format']['duration'])
        link = work / f'round-{i}.mp4'
        link.symlink_to(file)
        listing.append(f"file '{link}'")
        chapters += ['[CHAPTER]', 'TIMEBASE=1/1000', f'START={cursor}',
                     f'END={cursor+round(duration*1000)}', f'title=Round {i}']
        cursor += round(duration*1000)
    (work/'list.txt').write_text('\n'.join(listing)+'\n')
    (work/'chapters.txt').write_text('\n'.join(chapters)+'\n')
    temp = output.with_suffix('.partial.mp4')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                    '-f','concat','-safe','0','-i',str(work/'list.txt'),
                    '-f','ffmetadata','-i',str(work/'chapters.txt'),
                    '-map','0:v','-map','0:a','-map_metadata','1','-map_chapters','1',
                    '-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',
                    str(temp)], check=True)
    temp.replace(output)
    print(f'{output} {cursor/1000:.3f} seconds')

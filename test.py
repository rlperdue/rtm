# create dataset on remote server

import os
from pathlib import Path
import subprocess
import zipfile

testfolder = 'bpillar'
k = [5,50]

# make zip of mesh folder and send to server
zippath = Path('to_server.zip').resolve()
with zipfile.ZipFile(zippath, 'w') as zipf:
    zipf.write(f'tests/{testfolder}/mesh')
    for file in os.listdir(f'tests/{testfolder}/mesh'):
        zipf.write(f'tests/{testfolder}/mesh/{file}')

subprocess.call(f'scp {zippath} server:/Users/rperd/Desktop/rtm')

cmds = ' && '.join([
    'cd Desktop/rtm', 
    'powershell -Command Expand-Archive to_server.zip -DestinationPath .', 
    'del to_server.zip', 
    'git pull'
])
subprocess.run(f'ssh -o BatchMode=yes server {cmds}')

os.remove(zippath)

import subprocess

cmds = [
    'cd Desktop', 
    'echo pluh > pluh.txt'
]

proc = subprocess.Popen(
    ['ssh', '-o', 'BatchMode=yes', 'server', ' && '.join(cmds)], 
    text=True
)

proc.communicate()

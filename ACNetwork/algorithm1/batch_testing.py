import subprocess

NODES = 5

for i in range(1,8):
    for j in range(1,3):
        # Default topology
        # cmd = ['python3', 'main.py', f"run-{str(i)}-{str(j)}-n{50}.csv", '--config', f"../config/config1-n{NODES}.json"]

        # Default topology w/ error
        cmd = ['python3', 'main.py', f"run-{str(i)}-{str(j)}-n{50}.csv", '--config', f"../config/config1-n{NODES}.json", '-e', '-en', '1', '-ei', '0']

        # Star topology
        # cmd = ['python3', 'main.py', f"run-{str(i)}-{str(j)}-n{50}.csv", '--config', f"../config/config2-n{NODES}.json"]
        
        # Ring topology
        # cmd = ['python3', 'main.py', f"run-{str(i)}-{str(j)}-n{50}.csv", '--config', f"../config/config3-n{NODES}.json"]

        subprocess.Popen(cmd).wait()

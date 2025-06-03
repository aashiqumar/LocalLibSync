import subprocess

def build_library(config):
    print(f"[BUILD] Building {config['name']} in {config['src']}...")
    try:
        result = subprocess.run(
            config['build_command'],
            shell=True,
            check=True,
            cwd=config['src'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(result.stdout)
        print("[BUILD] Build successful.")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        print(e.output if hasattr(e, 'output') else "")
        return False, e.output if hasattr(e, 'output') else str(e)
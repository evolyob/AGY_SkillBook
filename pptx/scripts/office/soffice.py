import os, sys, subprocess

def get_soffice_env():
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "gen"
    return env

def run_soffice(args, **kwargs):
    return subprocess.run(["soffice"] + args, env=get_soffice_env(), **kwargs)

if __name__ == "__main__":
    result = run_soffice(sys.argv[1:])
    sys.exit(result.returncode)

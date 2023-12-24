import sys
import os
import subprocess
import pathlib

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO, stream = sys.stdout)

conf = {
    'exe_path' : 'sfbox',
    'cpu_count' : 8
        }

def set_executable_path(path):
    """Set the path to the sfbox execution file globally for the module

    Args:
        path (path-like object): path to the sfbox execution file
    """
    conf['exe_path'] = path

def set_cpu_count(cpu_count : int):
    """Set maximum cpu cores for multiprocessing

    Args:
        cpu_count (int): maximum cpu cores
    """
    conf['cpu_count'] = cpu_count

def sfbox_call(filename : pathlib.Path, wait = True):
    """Start a child process of sfbox

    Args:
        filename (str): path to an input file
        wait (bool, optional): If set to False
            python interpreter will not be locked,
            but log file has to be closed by the user manually.
            Defaults to True.

    Returns:
        [(Popen, log) or None]: if wait is set to true function returns nothing,
            otherwise a subprocess.Popen object
            and opened log file is returned
    """

    if isinstance(filename, str):
        filename = pathlib.Path(filename)

    executable_path = conf['exe_path']
    logger.info(f'subprocess call {executable_path} {filename.name}')
    log = open(filename.with_suffix('.log'), 'w')
    proc = subprocess.Popen(
        [executable_path+" "+str(filename.name)],
        stdout=log,
        shell=True,
        cwd = filename.parent,
        )
    while True:
        if not wait:
            return proc, log
        if proc.poll() is not None:
            logger.info(f'process is done, {filename} is calculated')
            log.close()
            break

def sfbox_calls_subprocess(dir = None):
    """Create a pool of task to process all sfbox input files in a directory.
    Number of of max sfbox instances that can work in parallel is defined in 
    conf['cpu_count'].
    The pool is created with Python subprocess package.

    Args:
        dir (str): path to a directory with input files. 
            Defaults to the working directory.
    """    
    if dir is None:
        dir = os.getcwd()
    cpu_count = conf['cpu_count']
    remained_files = list(pathlib.Path(dir).glob("*.in"))
    proc_work = []
    log_work = []
    event_show_msg = True
    logger.info(f'n of process to do: {len(remained_files)}')
    while len(remained_files) or len(proc_work):

        if event_show_msg:
            logger.info(
                f'{len(remained_files)} processes waiting, '+\
                f'{len(proc_work)} processes in work'
                )
            event_show_msg = False

        if (len(proc_work)<cpu_count) and len(remained_files):
            new_proc, new_log = sfbox_call(remained_files.pop(), wait=False)
            proc_work.append(new_proc)
            log_work.append(new_log)
            event_show_msg = True

        for i, (proc, log) in enumerate(zip(proc_work, log_work)):
            if proc.poll() is not None:
                logger.info(f'{proc} is done')
                log.close()
                del proc_work[i]
                del log_work[i]
                event_show_msg = True
    logger.info(f'Success.')
    return

def sfbox_calls_sh(dir = None , wait = True):
    """Create a pool of task to process all sfbox input files in a directory.
    Number of of max sfbox instances that can work in parallel is defined in 
    conf['cpu_count'].
    The pool is created with bash xargs command.

    Args:
        dir (str): path to a directory with input files. 
            Defaults to the working directory.
        wait (bool, optional): If set to True
            python interpreter will be locked until all jobs are done.
            Defaults to True.

    Returns:
        [(Popen, log) or None]: if wait is set to True function returns nothing,
            otherwise a subprocess.Popen object is returned
    """

    if dir is None:
        dir = os.getcwd()
    cpu_count = conf['cpu_count']
    exe_path = conf['exe_path']
    script_dir = pathlib.Path(__file__).parent
    bash_script = str(script_dir / "scripts" / "call_sfbox_multifile.sh")

    proc = subprocess.Popen(
        [bash_script+f" {cpu_count}" + f" {exe_path}"],
        shell =True,
        stdout=subprocess.PIPE,
        cwd = dir
        )
    while True:
        if not wait:
            return proc
        if proc.poll() is not None:
                logger.info(f'processes is done')
                break

def sfbox_calls(parallel_execution = 'sh', **kwargs):
    """Wrapper function to call multiple sfbox instances. 
    Parallel execution framework is python subprocesses or bash xargs.

    Args:
        dir (str): parallel execution framework 'sh' or 'subprocess'. 
            Defaults to 'sh'.
    """
    if parallel_execution == "sh":
        sfbox_calls_sh(**kwargs)
    elif parallel_execution == "subprocess":
        sfbox_calls_subprocess(**kwargs)
    else:
        raise ValueError("invalid argument")

if __name__ == '__main__':
    pass
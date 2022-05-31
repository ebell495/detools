#!/usr/local/bin/python3
import atheris
import os
import sys
import io

# with atheris.instrument_imports():
from detools import _main

# From: https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions
# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in 
    Python, i.e. will suppress all print, even if the print originates in a 
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).      

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]
        self.saved_exit = sys.exit

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)
        # sys.exit = dummy

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # sys.exit = self.saved_exit
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)

@atheris.instrument_func
def TestOneInput(data):
    if len(data) < 2:
        return

    from_size = (data[0] * len(data)) // 255
    from_p = data[2:2+from_size]
    to_p = data[2 + from_size:]
    
    with open("a", 'wb') as f:
        f.write(from_p)
    with open("b", 'wb') as f:
        f.write(to_p)

    
    if data[1] % 2 == 0:
        sys.argv = "detools create_patch -c none a.out b.out c.patch".split(' ')
    else:
        sys.argv = "detools create_patch -c lzma a.out b.out c.patch".split(' ')
    
    with suppress_stdout_stderr():
        _main()


atheris.instrument_all()
atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
# TestOneInput(b"abcd")
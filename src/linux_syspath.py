import sys
import os.path as op

# If interpreter working directory is the "src" inside the virtual environment directory then this should add site packages
# directory to the sys.path

sys.path.append(op.join(op.dirname(sys.path[0]), 'lib', 'site-packages'))
print(sys.path)

# GitSlice constants
import re

# The name of the project
PROJECT_NAME = "GitSlice"

# Brief description of the project
PROJECT_DESCRIPTION = "Slicing the repository that feeds us"

# Commands run inside a singularity container before user-specified commands
RSYNC_PRE_RUN = "mkdir -p %%WORKING_DIR%%; rsync --inplace --exclude \".git-descendants\" --exclude \".git-names\" " \
          "--exclude \".git-parents\" --exclude \".author\" --exclude \".author-email\" --chmod=Du=rwx,Dg=rx,Do=rx," \
          "Fu=rw,Fg=r,Fo=r -r /src/ %%WORKING_DIR%% 2>&1 ; cd %%WORKING_DIR%%"

# Commands run inside a singularity container after user-specified commands
RSYNC_POST_RUN = "rm -rf %%WORKING_DIR%%"

# The regular expression to be used for converting a string to a datetime delta, it should be in this format: XdXmXs.
TIMEDELTA_REGEX = (r'((?P<days>-?\d+)d)?'
                   r'((?P<hours>-?\d+)h)?'
                   r'((?P<minutes>-?\d+)m)?')

# Pattern object compiled from TIMEDELTA_REGEX which is used to get the values from the delta string.
TIMEDELTA_PATTERN = re.compile(TIMEDELTA_REGEX, re.IGNORECASE)

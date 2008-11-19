# -*- python -*-
#
# Setup our environment
#
import glob
import os, sys

sys.path = ["python"] + sys.path # ensure that we use our copy of sconsLSST
import lsst.SConsUtils as scons

env = scons.MakeEnv("sconsUtils",
                    r"$HeadURL$")

#
# Install things
#
env['IgnoreFiles'] = r"(~$|\.pyc$|^\.svn$)"

env.Declare()
Alias("install", [
    env.Install(env['prefix'], glob.glob("*.build")),
    env.Install(env['prefix'], glob.glob("*.table")),
    env.InstallEups(os.path.join(env['prefix'], "ups")),
    ])

env.Help("""
Build files for products that aren't in our svn tree
""")

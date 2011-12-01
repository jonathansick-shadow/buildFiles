### This file is a "startup.py" used in eups.
###
### It defines some useful operations for distribution
###

def cmdHook(Eups, cmd, opts, args):
    if cmd.split()[0] == "distrib":
        subcmd = cmd.split()[1]
        if subcmd == "create":
            opts.distribTypeName = "builder"
            opts.allowIncomplete = True
            opts.useFlavor = "generic"
            
eups.commandCallbacks.add(cmdHook)

global lsstThirdParty
lsstThirdParty = ('activemqcpp', 'apr', 'astrometry_net', 'boost', 'boostmpi',
                  'cfitsio', 'doxygen', 'eigen', 'fftw', 'freetype', 'gcc', 'gmp',
                  'gsl', 'libpng', 'matplotlib', 'minuit2', 'mpfr', 'mpich2',
                  'mysqlclient', 'mysqlpython', 'numpy', 'pyfits', 'pysqlite',
                  'python', 'scisql', 'scons', 'sconsDistrib', 'sqlite',
                  'swig', 'tcltk', 'wcslib', 'xpa')

global defaultRepoVersioner, defaultVersionIncrementer
defaultRepoVersioner = hooks.config.Eups.repoVersioner
defaultVersionIncrementer = hooks.config.Eups.versionIncrementer

# Build version hackers for LSST: "plus versions", e.g., +3
global lsstRepoVersioner, lsstVersionIncrementer
def lsstRepoVersioner(product, version):
    # We don't rebuild third-party packages in the same way as for LSST packages
    if product in lsstThirdParty:
        return version
    return defaultRepoVersioner(product, version)

def lsstVersionIncrementer(product, version):
    if product in lsstThirdParty:
        raise RuntimeError("We don't rebuild third-party packages this way")
    return defaultVersionIncrementer(product, version)

# Build version hackers for HSC: "letter versions", e.g., a_hsc
global hscSuffix
hscSuffix = '_hsc'
def hscRepoVersioner(product, version):
    if version[-len(hscSuffix):] == hscSuffix:
        import re
        return re.sub(r"^([\w.+-]*[0-9.])[a-z]+" + hscSuffix + "$", r"\1", version)
    return lsstRepoVersioner(product, version)

def hscVersionIncrementer(product, version):
    import re
    match = re.search(r"^([\w.+-]*[0-9.])([a-z]+)" + hscSuffix + "$", version)
    if not match:
        return version + "a" + hscSuffix

    repoVersion = match.group(1)
    letters = match.group(2)

    letterVersionNumber = 0
    for l in letters:
        if not l >= 'a' and l <= 'z':
            raise RuntimeError("Version %s contains an illegal character %s" % (iversion, l))
        letterVersionNumber = 26*letterVersionNumber + (ord(l) - ord('a'))

    letterVersionNumber += 1

    letters = ""
    while letterVersionNumber:
        letters += chr(letterVersionNumber%26 + ord('a'))
        letterVersionNumber //= 26

    letters = ''.join(reversed(letters))

    return repoVersion + letters + hscSuffix


# Select which build version hacker to use
hooks.config.Eups.repoVersioner = lsstRepoVersioner
hooks.config.Eups.versionIncrementer = lsstVersionIncrementer


# How to build LSST products (pull from git)
#
# LSST products' build files should contain:
# @LSST BUILD@
# build_lsst @PRODUCT@ @VERSION@ @PRODUCT.replace("_", "/")@ @REPOVERSION@
hooks.config.distrib["builder"]["variables"]["LSST BUILD"] = """
build_lsst() {
    if [ -z "$1" -o -z "$2" -o -z "$3" -o -z "$4" ]; then
        echo "build_lsst requires four arguments"
        exit 1
    fi
    productname=$1
    versionname=$2
    reponame=$3
    repoversion=$4
    builddir=${productname}-${versionname}
    if [ -d $builddir ]; then
        rm -rf $builddir
    fi
    mkdir $builddir &&
    git archive --format=tar --remote=git@git.lsstcorp.org:LSST/DMS/${reponame}.git ${repoversion} | tar -x -C $builddir &&
    cd $builddir &&
    setup -r . &&
    scons opt=3 install version=$versionname
}
"""

# How to install "ups" files for LSST third-party products (grab from git)
#
# Third-party products' build files should contain at the top:
# @LSST UPS@
# and then later:
# lsst_ups @PRODUCT@ @VERSION@ <INSTALL-DIR> [GIT-HASH]
hooks.config.distrib["builder"]["variables"]["LSST UPS"] = """
lsst_ups() {
    if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
        echo "lsst_cfg requires at least three arguments"
        exit 1
    fi
    productname=$1
    versionname=$2
    installdir=$3
    githash=$4
    gitrepo="git@git.lsstcorp.org:LSST/DMS/devenv/buildFiles.git"
    if [ -z "$githash" ]; then
        githash="HEAD"
    fi
    currentdir=$(pwd)
    git archive --verbose --format=tar --remote=$gitrepo --prefix=ups/ ${githash} ${productname}.build | tar --extract --verbose --directory $installdir &&
    eups expandbuild -i ${installdir}/ups/${productname}.build -V $versionname
    git archive --verbose --format=tar --remote=$gitrepo --prefix=ups/ ${githash}:${productname} ${productname}.cfg | tar --extract --verbose --directory $installdir
}
"""

# How to build HSC products (pull from hg)
#
# HSC products' build files should contain:
# @HSC BUILD@
# build_hsc @PRODUCT@ @VERSION@ @REPOVERSION@
hooks.config.distrib["builder"]["variables"]["HSC BUILD"] = """
build_hsc() {
    if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
        echo "build_hsc requires three arguments: build_hsc PRODUCT VERSION REPOVERSION"
        exit 1
    fi
    productname=$1
    versionname=$2
    repoversionname=$3
    builddir=${productname}-${versionname}
    if [ -d $builddir ]; then
        rm -rf $builddir
    fi
    hg clone ssh://hsc-gw2.mtk.nao.ac.jp//ana/hgrepo/${productname} $builddir &&
    cd $builddir &&
    hg up $repoversionname &&
    setup -r . &&
    scons opt=3 install version=$versionname
}
"""

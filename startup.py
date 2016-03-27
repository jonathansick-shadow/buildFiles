# This file is a "startup.py" used in eups.
###
# It defines some useful operations for distribution
###

hooks.config.Eups.globalTags += ["HSC", "unstable", ]


def cmdHook(Eups, cmd, opts, args):
    if cmd.split()[0] == "distrib":
        subcmd = cmd.split()[1]
        if subcmd == "create":
            opts.distribTypeName = "builder"
            opts.allowIncomplete = True
            opts.useFlavor = "generic"
            opts.serverDir = "/home/price/public_html/packages"

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
hooks.config.Eups.repoVersioner = hscRepoVersioner
hooks.config.Eups.versionIncrementer = hscVersionIncrementer


# How to build LSST products (pull from git)
#
# LSST products' build files should contain:
# @LSST BUILD@
# build_lsst @PRODUCT@ @VERSION@ @REPOVERSION@ [repository name]
hooks.config.distrib["builder"]["variables"]["LSST BUILD"] = """
build_lsst() {
    if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
        echo "build_lsst requires at least three arguments"
        exit 1
    fi
    productname=$1
    versionname=$2
    repoversion=$3
    reponame=$4
    if [ -z "$reponame" ]; then
        reponame=$productname
    fi
    builddir=${productname}-${versionname}
    if [ -d $builddir ]; then
        rm -rf $builddir
    fi
    mkdir $builddir &&
    git archive --format=tar --remote=git://hsca.ipmu.jp/repos/${reponame}.git ${repoversion} | tar -x -C $builddir &&
    cd $builddir &&
    setup -r . &&
    scons opt=3 install version=$versionname
}
"""

# How to build HSC products: same as LSST
import re
hooks.config.distrib["builder"]["variables"]["HSC BUILD"] = re.sub(
    "build_lsst", "build_hsc", hooks.config.distrib["builder"]["variables"]["LSST BUILD"])

# How to install "ups" files for LSST third-party products (grab from git)
#
# Third-party products' build files should contain at the top:
# @LSST UPS@
# and then later:
# lsst_ups @PRODUCT@ @VERSION@ <INSTALL-DIR> [GIT-HASH]
hooks.config.distrib["builder"]["variables"]["LSST UPS"] = """
lsst_ups() {
    if [ -z "$1" -o -z "$2" -o -z "$3" ]; then
        echo "lsst_ups requires at least three arguments"
        exit 1
    fi
    productname=$1
    versionname=$2
    installdir=$3
    githash=$4
    gitrepo="git://hsca.ipmu.jp/repos/devenv/buildFiles.git"
    if [ -z "$githash" ]; then
        githash="HEAD"
    fi
    currentdir=$(pwd)
    git archive --verbose --format=tar --remote=$gitrepo --prefix=ups/ ${githash} ${productname}.build | tar --extract --verbose --directory $installdir &&
    eups expandbuild -i ${installdir}/ups/${productname}.build -V $versionname
    git archive --verbose --format=tar --remote=$gitrepo --prefix=ups/ ${githash}:${productname} | tar --extract --verbose --directory $installdir || echo "No additional files required: ignore error"
}
"""


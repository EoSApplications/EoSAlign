# This file exists solely so that, when this directory is installed as the
# "eosapplications" package, importing it (which happens automatically and
# unavoidably before any submodule like eosapplications.EoSApplications is
# imported) puts this directory on sys.path -- letting all sibling modules'
# existing bare imports (from Version import ..., etc.) keep resolving
# exactly as they do today, unmodified.
import os
import sys
_This_Directory = os.path.dirname(os.path.abspath(__file__))
if _This_Directory not in sys.path:
    sys.path.insert(0, _This_Directory)

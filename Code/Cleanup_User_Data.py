# Load libraries
    # Load standard libraries
import shutil
import sys
    # Load local libraries
from Session_Paths import get_user_data_root



# Delete the shared EoS user data folder (cached/user-edited/downloaded calibration files,
# the installed-applications registry, session data) after explicit confirmation.
#
# This is a pre-uninstall step, not a post-uninstall one -- it must be run BEFORE
# `pip uninstall eosapplications`, not after. All three apps' code lives in the single
# eosapplications package, so this command's own entry point is removed the moment that
# package is uninstalled: there is no way for any command to run afterward and notice the
# uninstall happened. Running this command at all already means eosapplications (and
# therefore EoSApplications, EoSAlign, and EoSHolo) is still installed and about to be
# removed, so it is safe to treat that as "all three are going away."
def main():

    Data_Root = get_user_data_root()

    if not Data_Root.exists():
        print(f"No user data folder found at {Data_Root} -- nothing to clean up.")
        return 0

    print(f"This will permanently delete: {Data_Root}")
    print("This includes cached calibration files, any calibration files you've edited")
    print("or entered yourself, downloaded calibration updates, and session data.")
    print("")
    print("Run this only when you are about to remove EoSApplications, EoSAlign, and")
    print("EoSHolo completely and no longer need this data.")
    print("")

    Confirmation = input("Type 'yes' to delete, anything else to cancel: ").strip().lower()
    if Confirmation != "yes":
        print("Cancelled. Nothing was deleted.")
        return 0

    shutil.rmtree(Data_Root)

    print(f"Deleted {Data_Root}.")
    print("Now run:  pip uninstall eosapplications")
    print("(and, if you installed them separately, pip uninstall eosalign eosholo eosfitting)")

    # Return success
    return 0



# Run when invoked directly
if __name__ == "__main__":
    sys.exit(main())

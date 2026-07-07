## Release vX.Y.Z


## Author checklist

- [ ] Version number updated in `README.md`
- [ ] Version number updated in `Code/Version.py`
- [ ] Version number updated in all installers
- [ ] Version number updated in `Installer_Files/Pip/pyproject.toml`
- [ ] Release notes drafted and accurate
- [ ] Windows/Mac/Linux installers built successfully
- [ ] PyPI wheel built successfully
- [ ] Release asset filenames match `Version.py`'s `Platform_Assets` exactly
- [ ] I understand publishing this GitHub Release will create a new Zenodo version
- [ ] Zenodo's GitHub webhook has been switched **on** for this repo (only if this release is meant to be archived — see "Zenodo Connect/Disconnect Toggle Workflow" in `Public_Release_Repo_And_Calibration_Data_Plan.md`)


## Reviewer checklist

- [ ] Confirmed the version number is correct and consistent across all files
- [ ] Confirmed release notes are accurate
- [ ] Confirmed installer/PyPI build artifacts match expected filenames
- [ ] Confirmed intaller/PyPI build artifacts work
- [ ] Confirmed this release is intentional and ready to trigger a new Zenodo version
- [ ] After the release is published and archived, confirmed Zenodo's GitHub webhook has been switched back **off**





# securecrt-scripts
Various SecureCRT scripts to automate things.

# BulkLoadINEConfigs.py
Clear existing configs on several routers at once and load in new configs from text files (as given by INE to go with their workbooks, for example).

This script expects you to have tabs open for each IOS/IOS-XE router named R# and each IOS-XR router named XR#, which is how INE does their naming (at least in the CCIE SP scenarios).

When run, the script will find all the tabs with appropriately named routers that are connected, then ask you to point to a directory full of files with names like R#.txt and XR#.txt. It will then blank out the existing configs on all of the routers (reloading where required), then load in the new configs from the text files. The specific file selected in the selection dialog doesn't matter, only the directory component is used.

All usernames and passwords are expected to be 'cisco', if this isn't the case then the script can still be used without an issue, just ensure all devices are already in enable mode before starting the script.

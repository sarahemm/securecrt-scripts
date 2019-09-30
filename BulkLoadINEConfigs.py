# $language = "python"
# $interface = "1.0"

# Wipe configs from multiple routers at a time then apply new ones from a directory
# of configuration text files (like INE gives you).

# Open tabs for all the routers you want to reconfigure (tabs should be named R#
# for IOS/IOS-XE and XR# for IOS-XR), then run this script in SecureCRT. Select
# any file in the directory full of config files (the specific file selected
# doesn't matter, just the directory is used), then say OK and wait a few minutes
# while all your routers are reconfigured.

# Passwords are assumed to be cisco/cisco for everything, if they're not then
# just enable before running the script and it won't matter.

import os
import re

initialTab = crt.GetScriptTab()

# return a list of tabs that match a specific regex
def FindTabs(tabRegex):
	tabList = []

	for i in range(1, crt.GetTabCount()+1):
		tab = crt.GetTab(i)
		if tab.Session.Connected == True and re.search(tabRegex, tab.Caption):
			tabList.append(tab)
	
	return tabList

# erase the startup config on an IOS/IOS-XE router, then reload it
def EraseIOSConfig(tab):
	scr = tab.Screen
	StatusMessage("Erasing IOS configuration on %s..." % tab.Caption)
	tab.Activate()
	scr.Send("\n")
	scr.WaitForString("#")
	scr.Send("wr erase\n")
	scr.WaitForString("Continue? [confirm]")
	scr.Send("\n")
	scr.WaitForString("#")
	scr.Send("reload\n")
	rv = scr.WaitForStrings(["Proceed with reload?", "configuration has been modified"])
	if(rv == 2):
		# if it asks if we want to save config, say no before confirming the reload
		scr.Send("no\n")
		crt.Sleep(2000)
	scr.Send("\n")
	scr.WaitForString("SYS-5-RELOAD")

# erase the config on an IOS-XR router (doesn't require a reload)
def EraseXRConfig(tab):
	scr = tab.Screen
	StatusMessage("Erasing IOS-XR configuration on %s..." % tab.Caption)
	tab.Activate()
	scr.Send("\n")
	scr.WaitForString("#")
	scr.Send("conf t\n")
	scr.WaitForString("(config)#")
	scr.Send("commit replace\n")
	scr.WaitForString("Do you wish to proceed?")
	scr.Send("yes\n")

# wait until an IOS/IOS-XE router reloads
def WaitForReload(tab):
	scr = tab.Screen
	StatusMessage("Waiting for %s to boot..." % tab.Caption)
	tab.Activate()
	scr.WaitForString("initial configuration dialog?")

# decline the offer of autoconfiguration and terminate the autoinstall
def DeclineAutoconfig(tab):
	scr = tab.Screen
	StatusMessage("Declining offer of autoconfiguration on %s..." % tab.Caption)
	tab.Activate()
	scr.Send("no\n")
	scr.WaitForString("terminate autoinstall")
	scr.Send("yes\n")

# wait for initialization of an IOS/IOS-XE router to complete and then enable
def WaitForReadyAndEnable(tab):
	scr = tab.Screen
	waitCycles = 0
	StatusMessage("Waiting for %s to complete initialization..." % tab.Caption)
	tab.Activate()
	
	# router might still be booting so try until we get a prompt back
	scr.Send("\n")
	rv = scr.WaitForString(">", 5)
	while(not rv):
		waitCycles += 1
		StatusMessage("Waiting for %s to complete initialization...%s" % (tab.Caption, "."*waitCycles))
		
		scr.Send("\r\n\r\n\r\n")
		rv = scr.WaitForString(">", 5)
	scr.Send("enable\n")

# get us logged in and enabled from any state we may be in
def GetToEnable(tab):
	scr = tab.Screen
	StatusMessage("Getting %s to a known state..." % tab.Caption)
	tab.Activate()

	while True:
		scr.Send("\r\n")
		rv = scr.WaitForStrings([")#", ">", "Username:", "#"])
		if rv == 1:
			# currently in config mode
			scr.Send("abort\nend\n")
		elif rv == 2:
			# currently in exec mode
			scr.Send("en\n")
			rv = scr.WaitForStrings(["#", "Password:"])
			if rv == 2:
				scr.Send("cisco\n")
				rv = scr.WaitForStrings(["#", "Password:"])
				if rv == 2:
					# we can't enable, password must be wrong
					break
		elif rv == 3:
			# not yet logged in
			scr.Send("cisco\n")
			scr.WaitForString("Password:")
			scr.Send("cisco\n")
		elif rv == 4:
			break
		crt.Sleep(1000)

# load configuration from a file into an IOS/IOS-XE/IOS-XR router
def LoadConfig(tab, configFile):
	scr = tab.Screen
	waitCycles = 0
	StatusMessage("Loading configuration onto %s..." % tab.Caption)
	tab.Activate()
	fp = file(configFile, "r")
	configText = fp.read()
	fp.close()
	scr.Send("conf t\n")
	scr.WaitForString("(config)#")
	scr.Send(configText)

# display a status message in our status window
# (which is what we use the command window as)
def StatusMessage(text):
	crt.CommandWindow.Text = text

def Main():
	iosTabs = FindTabs("^R\d+$")
	iosXrTabs = FindTabs("^XR\d+$")
	if iosTabs == [] and iosXrTabs == []:
		crt.Dialog.MessageBox("No router tabs found! Please ensure you have tabs in a connected state that are named R# for IOS/IOS-XE devices and XR# for IOS-XR devices, then try again.")
		return

	selectedFile = crt.Dialog.FileOpenDialog("Select Config Directory", "This Folder")
	configDir = os.path.dirname(selectedFile)
	
	iosRouterList = "\n".join(map(lambda x: x.Caption, iosTabs))
	iosXrRouterList = "\n".join(map(lambda x: x.Caption, iosXrTabs))
	
	if iosRouterList == "":
		iosRouterList = "none"
	if iosXrRouterList == "":
		iosXrRouterList = "none"
	
	warnMsg = "About to reconfigure the following routers, configuration will be ERASED on all listed devices!\n\nIOS/IOS-XE:\n%s\n\nIOS-XR:\n%s\n\nOK to continue?" % (iosRouterList, iosXrRouterList)
	response = crt.Dialog.MessageBox(warnMsg, "Erase Configuration?", BUTTON_YESNO)
	if response != IDYES:
		return
	
	# show the command window (used to show the current status to the user)
	crt.CommandWindow.Visible = True

	for iosTab in iosTabs:
		GetToEnable(iosTab)

	for iosTab in iosTabs:
		EraseIOSConfig(iosTab)
	
	for iosTab in iosTabs:
		WaitForReload(iosTab)
	
	for iosTab in iosTabs:
		DeclineAutoconfig(iosTab)
		
	for iosTab in iosTabs:
		WaitForReadyAndEnable(iosTab)
	
	for iosTab in iosTabs:
		configFile = "%s\%s.txt" % (configDir, iosTab.Caption)
		LoadConfig(iosTab, configFile)
	
	for iosXrTab in iosXrTabs:
		GetToEnable(iosXrTab)
	
	for iosXrTab in iosXrTabs:
		EraseXRConfig(iosXrTab)
		
	for iosXrTab in iosXrTabs:
		configFile = "%s\%s.txt" % (configDir, iosXrTab.Caption)
		LoadConfig(iosXrTab, configFile)
		
	# go back to the tab that was active before we started
	initialTab.Activate()
	
	# clear and close our log window (the command window)
	crt.CommandWindow.Text = ""
	crt.CommandWindow.Visible = False

Main()

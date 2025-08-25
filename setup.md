# Step 1

## Download and install Python

For Windows: https://www.python.org/downloads/windows/  
For Mac: https://www.python.org/downloads/mac-osx/  
For Linux: Use your package manager.

Windows and Mac:  
**Use custom installation.**  
Make sure to check the "Add Python to PATH" option.   
Make sure to check pip in optional features.  

Linux:  
Install python and pip from your package manager. 

## Update pip and install py3amf

Run the following commands in your terminal or command prompt.

### Linux/Mac
`python3 -m pip install --upgrade pip`  
`python3 -m pip install py3amf`

Note: On Linux you may need to run:

`python3 -m pip install py3amf --break-system-packages`  

### Windows (CMD/PowerShell)
`py -m pip install --upgrade pip`  
`py -m pip install py3amf`  

# Step 2

## Setting up the standalone flash player

Ruffle doesn't work yet.    

https://archive.org/details/Adobe_Flash_Player_Complete_Collection    

Look for the version that corresponds to your OS.   
Get the latest version (32).  
It should be the one with "sa" in the name.   

## Trusting the directory with Touchy games

Create the following directory structure if it doesn't exist:

#### Windows:

`%APPDATA%\Macromedia\Flash Player\#Security\FlashPlayerTrust\`

#### Linux:

`~/.macromedia/Flash_Player/#Security/FlashPlayerTrust/`

#### macOS:

`~/Library/Preferences/Macromedia/Flash Player/#Security/FlashPlayerTrust/`

Create a new .cfg file with any name i.e., touchy.cfg.   
Add the absolute path to the directory with Touchy games.   

**Warning: Only put trusted games in this directory.    
Do not put any other games.** 

Example:

#### Windows:    
`C:\Users\User\Desktop\Touchy`

#### Linux:    
`/home/user/Desktop/Touchy`

#### macOS:    
`/Users/User/Desktop/Touchy`

# Step 3

## Setting up Touchy on your android device

### Download prerequisites

**Note: If you are installing Touchy on an older phone (Android 12 or lower), you do not need to download the platform tools.    
Simply install the APK file on your phone.**  

**Note: If your phone is rooted, you do not need to download the platform tools.    
Simply running `pm install --bypass-low-target-sdk-block Touchy.1.7.apk` in a root shell should work.** 

Download Touchy to your computer from here:    
https://archive.org/details/nitrome-touchy

Download the latest platform tools to your computer from here:   
https://developer.android.com/tools/releases/platform-tools   

Extract the zip file to a directory of your choice.   
Copy the Touchy APK file to the same directory as the platform tools.  

### Enable USB debugging on your android device

**Note: If you are installing Touchy on an older phone (Android 12 or lower), you do not need to do this step.    
Simply install the APK file.**   

Go to Settings → About phone → Build number → Tap 7 times → Developer options → Enable USB debugging.   
**Note: On Xiaomi devices you also need to enable "USB debugging (Security settings)" in Developer options.**   

Connect your android device to your computer via USB.   
Open a terminal or command prompt in the directory where you extracted the platform tools.

Run the following command:    
`adb install --bypass-low-target-sdk-block Touchy.1.7.apk `   
Note: You may need to allow the installation in the Play Protect dialog if it comes up.   

**Note: On Linux you might need udev rules to allow adb to access your device.**

# Step 4

## Redirecting the flash games and Touchy to use the self-hosted server

Firstly, find out your computer's private IP address.   

#### Windows:

Run `ipconfig` in a terminal or command prompt.   
Look for the IPv4 address.   

#### Linux:

Run `ifconfig` in a terminal or command prompt.   
Look for the IPv4 address.   

#### macOS:

Run `ifconfig` in a terminal or command prompt.   
Look for the IPv4 address.   
 
It should be something like 192.168.1.100.  
Make sure the private IP address is from your main network adapter.

You need to redirect the following domains to your computer's private IP address:  
`registry.monkeysecurity.com`   
`playbrassmonkey.com`

The best way to do this would be to redirect the domains router-wide.   
The details depend on your router. 
If your router cannot redirect domains, running a custom DNS server and doing a rewrite *might* work.

At least on PC, it can be done by editing the hosts file.

**Alternatively, try the modified version of the app on the archive which connects to 192.168.1.115 instead.**  
**Change your computer's IP address to 192.168.1.115, restart and run the server.**  

**Note: If you can redirect the domains from your router, you do not need to do the following steps.**

### On your computer, edit the hosts file as administrator:

#### Windows:

`C:\Windows\System32\drivers\etc\hosts`

#### Linux:

`/etc/hosts`

#### macOS:

`/private/etc/hosts`

Add the following lines to the end of the file:

`your_private_ip registry.monkeysecurity.com`  
`your_private_ip playbrassmonkey.com`

**If you are using the modified app, then you should put 192.168.1.115 as the private IP since your PC needs to be configured for that IP.**  

If your phone is rooted, you can also use a module like bindhosts to redirect the domains on your phone.

# Step 5

## Playing games

Download the latest release.  
Run the server on your computer:

Run `python3 start_servers.py` in a terminal or command prompt. 

If you see something like:  
For games:  
`[INFO] REGISTRY: Device registered: Bad Ice-Cream 2 (52ca7f38cdbb88ddcf266fbd311d1bef87dcef7616c9247eb86b7c552cb2d37d14698), Slot: 1`  
For Touchy:   
`[INFO] REGISTRY: Device registered: M2007J3SG (9be34a2fe5c3fb90), Slot: 0` 

And you see the games in the list, you are good to go. Enjoy playing your games!

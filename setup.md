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
`C:\Users\User\Desktop\TouchyGames`

#### Linux:    
`/home/user/Desktop/TouchyGames`

#### macOS:    
`/Users/User/Desktop/TouchyGames`

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

### Easy Way
Try the modified version of the app `Touchy.1.7-modified.apk` and install it according to Step 3.  
(delete the original before installing the modified one)  
(modify the commands to accomodate the different name)  
Change your computer's private IP address to `192.168.1.115` (depends on your OS, there are many tutorials online).

Then modify the hosts file on your computer:

#### Windows:

`C:\Windows\System32\drivers\etc\hosts`

#### Linux:

`/etc/hosts`

#### macOS:

`/private/etc/hosts`

Add the following lines to the end of the file:

`127.0.0.1 registry.monkeysecurity.com`  
`127.0.0.1 playbrassmonkey.com`

Setting it to 127.0.0.1 will make the flash games connect to localhost, aka the self-hosted server running on your computer.   
The modified app will connect to `192.168.1.115` which will also connect to your computer after setting it to that.  

Then go to Step 5.

### Hard Way

The hard way involves redirecting the default domains on your router.  
If you have a router capable to do this, you don't need to use the modified app.  

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

Then go to Step 5.

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

google-drive-cleaner
====================

Google Drive is an excellent way to share files with colleagues and friends.  However, it makes some unconventional assumptions about the organization of files and folders.  As a result of these assumptions (and sequences of events like the ones documented [here](https://support.google.com/a/answer/6008339?hl=en), some users will find that they have "orphaned" files.  These files are included in "All Files" but not visible in any other folder on My Drive.  They continue to consume quota and the "all files" technique is impractical for large numbers of files.  

This Python package addresses the orphaned files problem by scanning through Google Drive and find orphaned files.   Once identified, they can be moved into a folder for manual review (recommended) or directly into the trash. 

Google API Code
===============

The following were the steps I took to get the Google API configured:

 - Go to the APIs console at [https://code.google.com/apis/console](https://code.google.com/apis/console)
 - Create a project, I named it GDriveOrphans
 - It will take a minute or so for the project to finish then you should be redirected to the project hompage
 - Under "APIs & Auth" click on APIs
   - Turn on Drive API and Drive SDK (I turned off the rest)
 - Click on Create Credentials
 - Select "Other UI (e.g. Windows, CLI tool)" and "User Data"
 - Click "What Credentials Do I need?"
 - Enter a Client ID, I entered GDriveOrphans and Create it
 - Also enter a Product Name, I again used GDriveOrphans
 - Click Download to download your json credentials file. Rename it to client_secret.json and put it in the same directory as cleaner.py

Use (to assist non-programmers)
===============================

WARNING: This procedure is provided is provided "as is" without express or implied warranty.  The Google API includes commands that could result in the loss of data.  While the author believes the guide to be accurate, any number of things (including the Google API) could have changed since it was written.  If you elect to follow this guide, you take full responsibility for the consequences.  If you live in a country where the author cannot disclaim such a warranty, you are not licensed to use the following procedure.

 - Install Python
 - Install pip (http://pip.readthedocs.org/en/latest/installing.html)
 - Install the Google API by running "pip install --upgrade google-api-python-client"
 - Install another required library by runnign "pip install httplib2"
 - Using a command prompt, change directory into the folder that contains cleaner.py 
 - Start python.  In the python console (once you see >>>), run:
```
from cleaner import *
dc = build_connection()
```
The first time you run this will open a browser window for you to login to your google account. Your credential files will then be saved into a .credentials dir and you will not need to authenticate again.

While the original author designed this to delete orphaned files, I strongly recommend that you create a folder (named something like "_delete") and move all your orphaned files/folders to this directory.  This will give you a chance to visually review all the files before deleting (and you can always delete the whole folder if that's what you really want to do).

To move files, navigate to the target Google Drive folder in your web browser.  The URL will end in something like "folders/0B1Bdl-YbgK8ZUWx0cVEtTklWdUU".  Everything after the '/' is the ID of the folder.  Using that ID, run the following substituting the ID for <folder>.  In the final command, the ID should be enclosed in quotes:
```
dc.moveItems("<folder id>")
```

Another option is to move the files to the trash with:
```
dc.trashItems("<folder id>")
```
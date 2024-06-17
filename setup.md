## Set-Up Guide (Work In Progress)
#### (This was made with self-hosting in mind)
This guide assumes you've already created a bot user at the [Discord developer portal](https://discord.com/developers/applications).

### Find an IDE
#### This is just what I use lol
I personally use PyCharm Community Edition which you can find [here](https://www.jetbrains.com/pycharm/download), but any IDE *should* work.  
I'll be using PyCharm for this guide.

### Install The Libraries and FFMPEG
#### You can't run it without these
Press ALT+F12 to open up the console.  
Paste in this and click enter:
``pip install discord.py os yt-dlp itertools asyncio matplotlib``

### Configure and Provide Token
#### Configuration
At the [Discord developer portal](https://discord.com/developers/applications):  
1. Click your application (bot)  
2. Click the **Installation** tab on the left part of the page.  
3. Under **Authorization Methods**, check the **Guild Install** box.  
4. Under **Install Link**, select **Discord Provided Link**  
5. Under **Default Install Settings**, give it the **application.commands** and **bot** scopes.  
6. Give the bot the **Administrator** permission as well.  
7. Click the **Bot** tab on the left side of the page.  
8. Under **Authorization Flow**, enable **Public Bot**.  
9. Under **Presence Intent**, enable all presence intents.
  
#### ENV Values
Go generate and/or find your bot token at the [Discord developer portal](https://discord.com/developers/applications).  
  Find the token in the **Bot** section, accesible from the left side of the page.  
  Copy that token and paste it in the .env file after the ``DISCORD_TOKEN=`` (Make sure to surround it with apostrophes)  
Locate the root folder of your project  
  This folder should be the first folder in the top left corner and should be named the same as your project name  
    Right-click this folder  
    Click **Copy Path/Reference**  
    Click **Copy Absolute Path**  
  Then, replace every backslash (\) with a forward slash (/)  
  Paste it in the .env file after the ``DIRECTORY=`` (Make sure to surround it with apostrophes)  

### Press Start!  
#### You're all set!  
Press ``Shift+F10`` or the green start button in the window bar.

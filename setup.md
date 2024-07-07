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

You need **ffmpeg.exe** which you can download [here](https://www.gyan.dev/ffmpeg/builds/).  
1. Download the **ffmpeg-git-full.7z**.  
2. Unzip the file and find **ffmpeg.exe** in the **bin** folder.  
3. Drag **ffmpeg.exe** into the same directory as **bot.py**.  

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
9. Under **Privelaged Gateway Intents**, enable **Presence Intent** and **Server Members Intent**.
  
#### Environment Variables
* Go generate and/or find your bot token at the [Discord developer portal](https://discord.com/developers/applications).  
  1. Find the token in the **Bot** section, accesible from the left side of the page.  
  2. Copy that token and paste it in the .env file after the ``DISCORD_TOKEN=`` (Make sure to surround it with apostrophes)  

### Press Start!  
#### You're all set!  
Press ``Shift+F10`` or the green start button in the window bar.

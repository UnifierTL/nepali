"""
Unifier - A sophisticated Discord bot uniting servers and platforms
Copyright (C) 2024  Green, ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import nextcord
from nextcord.ext import commands
import aiohttp
import asyncio
import json
import tomli
import tomli_w
import os
import sys
import logging
import requests
import traceback
import threading
import shutil
from utils import log
from dotenv import load_dotenv
from pathlib import Path

# import ujson if installed
try:
    import ujson as json
except:
    pass

try:
    with open('.install.json') as file:
        install_info = json.load(file)

    if not install_info['product'] == 'unifier':
        print('This installation is not compatible with Unifier.')
        sys.exit(1)
except:
    # copy bootloader if needed
    if not os.path.isdir('boot'):
        os.mkdir('boot')
        for file in os.listdir('update/boot'):
            shutil.copy2(f'update/boot/{file}', f'boot/{file}')
    if not 'run.sh' in os.listdir():
        shutil.copy2('update/run.sh', 'run.sh')
    if not 'run.bat' in os.listdir():
        shutil.copy2('update/run.bat', 'run.bat')

    # we probably need to copy this too
    shutil.copy2('update/plugins/system.json', 'plugins/system.json')

    if sys.platform == 'win32':
        print('To start the bot, please run "run.bat" instead.')
    else:
        print('To start the bot, please run "./run.sh" instead.')
        print('If you get a "Permission denied" error, run "chmod +x run.sh" and try again.')
    sys.exit(1)

try:
    # as only winloop or uvloop will be installed depending on the system,
    # we will ask pylint to ignore importerrors for both
    if os.name == "win32":
        import winloop as uvloop  # pylint: disable=import-error
    else:
        import uvloop  # pylint: disable=import-error
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    pass

config_file = 'config.toml'
if 'devmode' in sys.argv:
    config_file = 'devconfig.toml'

valid_toml = False
try:
    with open(config_file, 'rb') as file:
        data = tomli.load(file)
    valid_toml = True
except:
    try:
        with open('config.json') as file:
            data = json.load(file)
    except:
        traceback.print_exc()
        print('\nFailed to load config.toml file.\nIf the error is a JSONDecodeError, it\'s most likely a syntax error.')
        sys.exit(1)

    # toml is likely in update files, pull from there
    with open('update/config.toml', 'rb') as file:
        newdata = tomli.load(file)

    def update_toml(old, new):
        for key in new:
            for newkey in new[key]:
                if newkey in old.keys():
                    new[key].update({newkey: old[newkey]})
        return new

    data = update_toml(data, newdata)

    with open(config_file, 'wb+') as file:
        tomli_w.dump(data, file)

try:
    with open('boot_config.json', 'r') as file:
        boot_data = json.load(file)
except:
    boot_data = {}

newdata = {}

for key in data:
    for newkey in data[key]:
        newdata.update({newkey: data[key][newkey]})

data = newdata

env_loaded = load_dotenv()

level = logging.DEBUG if data['debug'] else logging.INFO
package = data['package']

logger = log.buildlogger(package,'core',level)

owner_valid = True

try:
    if int(data['owner']) < 0 or type(data['owner']) is str:
        raise Exception()
except:
    owner_valid = False

if not valid_toml:
    logger.warning('From v3.0.0, Unifier will use config.toml rather than config.json.')
    logger.warning('To change your Unifier configuration, please use the new file.')

if not env_loaded or not os.path.isfile('.env'):
    logger.critical(
        'Could not load .env file! More info: https://unifier-wiki.pixels.onl/setup-selfhosted/getting-started/unifier#set-bot-token'
    )
    if not os.path.isfile('.env'):
        dotenv = open('.env', 'w+')
        dotenv.write('TOKEN=token_goes_here')
        dotenv.close()
        logger.critical('A template .env file was created. Please add your token to that file to start Unifier.')
    sys.exit(1)

if not owner_valid:
    logger.critical('Invalid owner user ID in configuration!')
    if type(data['owner']) is str:
        logger.critical('Please note that IDs should be integers and not strings.')
    sys.exit(1)

if os.name == "win32":
    logger.warning('You are using Windows, which is untested. Some features may not work.')

if not '.welcome.txt' in os.listdir():
    x = open('.welcome.txt','w+')
    x.close()
    logger.info('Thank you for installing Unifier!')
    logger.info('Unifier is licensed under the AGPLv3, so if you would like to add your own twist to Unifier, you must follow AGPLv3 conditions.')
    logger.info('You can learn more about modifying Unifier at https://unifier-wiki.pixels.onl/setup-selfhosted/modding-unifier')

if not 'repo' in list(data.keys()):
    logger.critical('WARNING: THIS INSTANCE IS NOT AGPLv3 COMPLAINT!')
    logger.critical('Unifier is licensed under the AGPLv3, meaning you need to make your source code available to users. Please add a repository to the config file under the repo key.')
    sys.exit(1)

if 'allow_prs' in list(data.keys()) and not 'allow_posts' in list(data.keys()):
    logger.warning('From v1.2.4, allow_prs is deprecated. Use allow_posts instead.')

if 'token' in list(data.keys()):
    logger.warning('From v1.1.8, Unifier uses .env (dotenv) files to store tokens. We recommend you remove the old token keys from your config.json file.')

cgroup = Path('/proc/self/cgroup')
if Path('/.dockerenv').is_file() or cgroup.is_file() and 'docker' in cgroup.read_text():
    logger.warning('Unifier is running in a Docker container. Some features may need plugins to work properly.')

try:
    with open('plugins/system.json', 'r') as file:
        vinfo = json.load(file)
except:
    with open('update.json', 'r') as file:
        vinfo = json.load(file)

if not data['skip_status_check']:
    try:
        incidents = requests.get('https://discordstatus.com/api/v2/summary.json',timeout=10).json()['incidents']
        for incident in incidents:
            logger.warning('Discord incident: ' + incident['name'])
            logger.warning(incident['status']+': '+incident['incident_updates'][0]['body'])
    except:
        logger.debug('Failed to get Discord status')


class AutoSaveDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = 'data.json'
        self.__save_lock = False

        # Ensure necessary keys exist
        self.update({'rooms': {}, 'emojis': [], 'nicknames': {}, 'blocked': {}, 'banned': {},
                     'moderators': [], 'avatars': {}, 'experiments': {}, 'experiments_info': {}, 'colors': {},
                     'external_bridge': [], 'modlogs': {}, 'trusted': [], 'report_threads': {}, 'fullbanned': [],
                     'exp': {}, 'squads': {}, 'squads_joined': {}, 'squads_optout': {}, 'appealban': [],
                     'languages': {}, 'settings': {}, 'invites': {}, 'underattack': [], 'rooms_count': {}})
        self.threads = []

        # Load data
        self.load_data()

    @property
    def save_lock(self):
        return self.__save_lock

    @save_lock.setter
    def save_lock(self, save_lock):
        if self.__save_lock:
            raise RuntimeError('already locked')
        self.__save_lock = save_lock

    def load_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            self.update(data)
        except FileNotFoundError:
            pass  # If the file is not found, initialize an empty dictionary

    def save(self):
        if self.__save_lock:
            return
        with open(self.file_path, 'w') as file:
            json.dump(self, file, indent=4)
        return

    def cleanup(self):
        for thread in self.threads:
            thread.join()
        count = len(self.threads)
        self.threads.clear()
        return count

    def save_data(self):
        if self.__save_lock:
            return
        thread = threading.Thread(target=self.save)
        thread.start()
        self.threads.append(thread)

class DiscordBot(commands.Bot):
    """Extension of discord.ext.commands.Bot for bot configuration"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__ready = False
        self.__update = False
        self.__config = None
        self.__boot_config = None
        self.__safemode = None
        self.__coreboot = None
        self.__devmode = None
        self.__setup_lock = False
        self.bridge = None
        self.pyversion = sys.version_info
        self.db = AutoSaveDict({})

    @property
    def owner(self):
        return self.__config['owner'] if self.__config else None

    @property
    def config(self):
        return self.__config

    @property
    def boot_config(self):
        return self.__boot_config

    @config.setter
    def config(self, config):
        if self.__config:
            raise RuntimeError('Config already set')
        self.__config = config

    @boot_config.setter
    def boot_config(self, config):
        if self.__boot_config:
            raise RuntimeError('Boot config already set')
        self.__boot_config = config

    @property
    def ready(self):
        return self.__ready

    @ready.setter
    def ready(self, ready):
        if self.__ready:
            raise RuntimeError('Bot is already ready')
        self.__ready = ready

    @property
    def setup_lock(self):
        return self.__setup_lock

    @setup_lock.setter
    def setup_lock(self, lock):
        if self.__setup_lock:
            raise RuntimeError('Bot is already locked')
        self.__setup_lock = lock

    @property
    def update(self):
        return self.__update

    @update.setter
    def update(self, update):
        if self.__update:
            raise RuntimeError('Update lock is set')
        self.__update = update

    @property
    def safemode(self):
        return self.__safemode

    @safemode.setter
    def safemode(self, status: bool):
        if not self.__safemode is None:
            raise RuntimeError('Safemode is set')
        self.__safemode = status

    @property
    def coreboot(self):
        return self.__coreboot

    @coreboot.setter
    def coreboot(self, status: bool):
        if not self.__coreboot is None:
            raise RuntimeError('Coreboot is set')
        self.__coreboot = status

    @property
    def devmode(self):
        return self.__devmode

    @devmode.setter
    def devmode(self, status: bool):
        if not self.__devmode is None:
            raise RuntimeError('Coreboot is set')
        self.__devmode = status


bot = DiscordBot(command_prefix=data['prefix'],intents=nextcord.Intents.all())
bot.config = data
bot.boot_config = boot_data
bot.coreboot = 'core' in sys.argv
bot.safemode = 'safemode' in sys.argv and not bot.coreboot
bot.devmode = 'devmode' in sys.argv
mentions = nextcord.AllowedMentions(everyone=False,roles=False,users=False)

if bot.coreboot:
    logger.warning('Core-only boot is enabled. Only core and System Manager will be loaded.')

if bot.safemode:
    logger.warning('Safemode is enabled. Only system extensions will be loaded.')

asciiart = """  _    _       _  __ _           
 | |  | |     (_)/ _(_)          
 | |  | |_ __  _| |_ _  ___ _ __ 
 | |  | | '_ \\| |  _| |/ _ \\ '__|
 | |__| | | | | | | | |  __/ |   
  \\____/|_| |_|_|_| |_|\\___|_| """

print(asciiart)
print('Version: '+vinfo['version'])
print('Release '+str(vinfo['release']))
print()

@bot.event
async def on_ready():
    if len(bot.extensions) > 0:
        # Prevent duplicate extension load
        return

    bot.session = aiohttp.ClientSession(loop=bot.loop)
    logger.info('Loading Unifier extensions...')
    bot.remove_command('help')
    if hasattr(bot, 'locked'):
        locked = bot.locked
    else:
        locked = False
    if not locked:
        should_abort = False
        try:
            bot.load_extension("cogs.sysmgr")
            bot.pid = os.getpid()
            bot.load_extension("cogs.lockdown")
        except:
            logger.exception('An error occurred!')
            logger.critical('System modules failed to load, aborting boot...')
            should_abort = True
        if should_abort:
            sys.exit(1)
        logger.debug('System extensions loaded')
        if hasattr(bot, 'bridge') and not bot.coreboot:
            try:
                logger.debug('Restructuring room data...')
                await bot.bridge.convert_1()
                logger.debug('Optimizing room data, this may take a while...')
                await bot.bridge.optimize()
                if len(bot.bridge.bridged) == 0:
                    await bot.bridge.restore()
                    logger.info(f'Restored {len(bot.bridge.bridged)} messages')
            except FileNotFoundError:
                logger.warning('Cache backup file could not be found, skipping restore.')
            except:
                logger.exception('An error occurred!')
                logger.warning('Message restore failed')
        elif data['periodic_backup'] <= 0:
            logger.debug(f'Periodic backups disabled')
        if data['enable_ctx_commands'] and not bot.coreboot:
            logger.debug("Registering context commands...")
            await bot.sync_application_commands()
    logger.info('Unifier is ready!')
    if not bot.ready:
        bot.ready = True

@bot.event
async def on_command_error(_ctx, _command):
    # ignore all errors raised outside cog
    # as core has no commands, all command errors from core can be ignored
    pass

@bot.event
async def on_message(message):
    if not bot.ready or bot.setup_lock:
        return

    if not message.webhook_id==None:
        # webhook msg
        return

    if message.author.id in bot.db['fullbanned']:
        if message.author.id==bot.owner:
            bot.db['fullbanned'].remove(message.author.id)
            bot.db.save_data()
        else:
            return

    if message.content.lower().startswith(bot.command_prefix) and not message.author.bot:
        message.content = bot.command_prefix + message.content[len(bot.command_prefix):]
        return await bot.process_commands(message)

try:
    bot.run(os.environ.get('TOKEN'))
except SystemExit as e:
    try:
        code = int(f'{e}')
    except:
        code = 'unknown'
    if code==0 or code==130:
        logger.info(f'Exiting with code {code}')
    else:
        logger.critical(f'Exiting with code {code}')

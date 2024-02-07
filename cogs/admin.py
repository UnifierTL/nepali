"""
Unifier - A "simple" bot to unite Discord servers with webhooks
Copyright (C) 2024  Green and ItsAsheer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
import aiofiles
import inspect
import textwrap
from contextlib import redirect_stdout
import cpuinfo
import time
import os
import json
import requests

def log(type='???',status='ok',content='None'):
    from time import gmtime, strftime
    time1 = strftime("%Y.%m.%d %H:%M:%S", gmtime())
    if status=='ok':
        status = ' OK  '
    elif status=='error':
        status = 'ERROR'
    elif status=='warn':
        status = 'WARN '
    elif status=='info':
        status = 'INFO '
    else:
        raise ValueError('Invalid status type provided')
    print(f'[{type} | {time1} | {status}] {content}')

with open('config.json', 'r') as file:
    data = json.load(file)
owner = data['owner']
branch = data['branch']
check_endpoint = data['check_endpoint']
files_endpoint = data['files_endpoint']

noeval = '''```-------------No eval?-------------
⠀⣞⢽⢪⢣⢣⢣⢫⡺⡵⣝⡮⣗⢷⢽⢽⢽⣮⡷⡽⣜⣜⢮⢺⣜⢷⢽⢝⡽⣝
⠸⡸⠜⠕⠕⠁⢁⢇⢏⢽⢺⣪⡳⡝⣎⣏⢯⢞⡿⣟⣷⣳⢯⡷⣽⢽⢯⣳⣫⠇
⠀⠀⢀⢀⢄⢬⢪⡪⡎⣆⡈⠚⠜⠕⠇⠗⠝⢕⢯⢫⣞⣯⣿⣻⡽⣏⢗⣗⠏⠀
⠀⠪⡪⡪⣪⢪⢺⢸⢢⢓⢆⢤⢀⠀⠀⠀⠀⠈⢊⢞⡾⣿⡯⣏⢮⠷⠁⠀⠀
⠀⠀⠀⠈⠊⠆⡃⠕⢕⢇⢇⢇⢇⢇⢏⢎⢎⢆⢄⠀⢑⣽⣿⢝⠲⠉⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡿⠂⠠⠀⡇⢇⠕⢈⣀⠀⠁⠡⠣⡣⡫⣂⣿⠯⢪⠰⠂⠀⠀⠀⠀
⠀⠀⠀⠀⡦⡙⡂⢀⢤⢣⠣⡈⣾⡃⠠⠄⠀⡄⢱⣌⣶⢏⢊⠂⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢝⡲⣜⡮⡏⢎⢌⢂⠙⠢⠐⢀⢘⢵⣽⣿⡿⠁⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠨⣺⡺⡕⡕⡱⡑⡆⡕⡅⡕⡜⡼⢽⡻⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣳⣫⣾⣵⣗⡵⡱⡡⢣⢑⢕⢜⢕⡝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣴⣿⣾⣿⣿⣿⡿⡽⡑⢌⠪⡢⡣⣣⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡟⡾⣿⢿⢿⢵⣽⣾⣼⣘⢸⢸⣞⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠁⠇⠡⠩⡫⢿⣝⡻⡮⣒⢽⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀```'''

def cleanup_code(content):
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    return content.strip('` \n')

def set_author(embed,**kwargs):
    try:
        embed.set_author(name=kwargs['name'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_author(name=kwargs['name'])

def set_footer(embed,**kwargs):
    try:
        embed.set_footer(text=kwargs['text'],icon_url=kwargs['icon_url'].url)
    except:
        embed.set_footer(text=kwargs['text'])

class Admin(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(hidden=True)
    async def dashboard(self,ctx):
        if ctx.author.id==owner:
            async with aiofiles.open('uptime.txt','r',encoding='utf-8') as x:
                startup = await x.read()
                startup = int(startup)
                await x.close()
            embed = discord.Embed(title='Unifier dashboard',description='Just a moment...',color=0xb5eeff)
            before = time.monotonic()
            msg = await ctx.send(embed=embed)
            ping = (time.monotonic() - before) * 1000
            pingspeed = round(ping, 1)
            current = round(time.time())
            uptime = current - startup
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            seconds = (uptime % 3600) % 60
            import platform
            import psutil
            arch = platform.machine()
            osinfo = platform.platform()
            cpu = await self.bot.loop.run_in_executor(None, lambda: cpuinfo.get_cpu_info()['brand_raw'])
            ghz = await self.bot.loop.run_in_executor(None, lambda: round(cpuinfo.get_cpu_info()['hz_actual'][0]/1000000000,2))
            ram = round(psutil.virtual_memory().total / (1024.0 **3))
            cpuusage = psutil.cpu_percent()
            ramusage = psutil.virtual_memory()[2]
            membercount = 0
            for guild in self.bot.guilds:
                try:
                    membercount = membercount + guild.member_count
                except:
                    pass
            embed = discord.Embed(title='Unifier Dashboard',color=0xb5eeff)
            embed.add_field(name='Latency',value='%s ms' % round(ping, 1),inline=True)
            embed.add_field(name='CPU',value='{0} ({1} GHz, currently using {2}%)'.format(cpu,ghz,cpuusage),inline=True)
            embed.add_field(name='RAM',value='{0} GB (currently using {1}%)'.format(ram,ramusage),inline=True)
            embed.add_field(name='Architecture',value=arch,inline=True)
            embed.add_field(name='OS',value=osinfo,inline=True)
            guildcount = len(self.bot.guilds)
            if guildcount == 69:
                guildcount = '69 :smirk:'
            embed.add_field(name='Server count',value='%s' % guildcount,inline=True)
            embed.add_field(name='User count',value='{0} ({1} cached)'.format(membercount,len(set(self.bot.get_all_members())),inline=True))
            embed.add_field(name='Up since',value=f'<t:{startup}:f>',inline=False)
            embed.add_field(name='Uptime',value=f'`{hours}` hours, `{minutes}` minutes, `{seconds}` seconds',inline=False)
            await msg.edit(embed=embed)

    @commands.command(hidden=True)
    async def eval(self,ctx,*,body):
        if ctx.author.id==owner:
            import io
            import traceback
            env = {
                'ctx': ctx,
                'channel': ctx.channel,
                'author': ctx.author,
                'guild': ctx.guild,
                'message': ctx.message,
                'source': inspect.getsource,
                'session':self.bot.session,
                'bot':self.bot
            }

            env.update(globals())

            body = cleanup_code(body)
            stdout = io.StringIO()
            err = out = None

            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

            try:
                if 'bot.token' in body:
                    raise ValueError('Blocked phrase')
                exec(to_compile, env)
            except Exception as e:
                pass

            try:
                func = env['func']
            except Exception as e:
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` the code didn\'t work\n`2.` no meme?')
                await ctx.author.send(f'```py\n{e.__class__.__name__}: {e}\n```')
                return
            try:
                with redirect_stdout(stdout):
                    ret = await func()
            except Exception as e:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                try:
                    await ctx.send(file=discord.File(fp='nosuccess.png'))
                except:
                    await ctx.send('Two (or more) errors occured:\n`1.` the code didn\'t work\n`2.` no meme?')
                await ctx.author.send(f'```py\n{value}{traceback.format_exc()}\n```')
            else:
                value = await self.bot.loop.run_in_executor(None, lambda: stdout.getvalue())
                if value=='':
                    pass
                else:
                    await ctx.send('```%s```' % value)
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @eval.error
    async def eval_error(self,ctx,error):
        if ctx.author.id==owner:
            if isinstance(error, commands.MissingRequiredArgument):
                try:
                    await ctx.send('where code :thinking:',file=discord.File(fp='nocode.png'))
                except:
                    try:
                        await ctx.send('where code :thinking:')
                    except:
                        await ctx.author.send('where code and permission to send messages :thinking:')
            else:
                try:
                    await ctx.send('Something went horribly wrong, sadge')
                except:
                    await ctx.author.send('i cant send stuff in that channel :/')
        else:
            try:
                await ctx.send(file=discord.File(fp='noeval.png'))
            except:
                await ctx.send(noeval)

    @commands.command(hidden=True)
    async def reload(self,ctx,*,extensions):
        if ctx.author.id==owner:
            extensions = extensions.split(' ')
            msg = await ctx.send('Reloading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    self.bot.reload_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Reload completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run reload! :x:')

    @commands.command(hidden=True)
    async def load(self,ctx,*,extensions):
        if ctx.author.id==owner:
            extensions = extensions.split(' ')
            msg = await ctx.send('Loading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    self.bot.load_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Load completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run load! :x:')

    @commands.command(hidden=True)
    async def unload(self,ctx,*,extensions):
        if ctx.author.id==owner:
            extensions = extensions.split(' ')
            msg = await ctx.send('Unloading extensions...')
            failed = []
            errors = []
            text = ''
            for extension in extensions:
                try:
                    if extension=='admin':
                        raise ValueError('Cannot unload the admin extension, let\'s not break the bot here!')
                    self.bot.unload_extension(f'cogs.{extension}')
                    if len(text)==0:
                        text = f'```diff\n+ [DONE] {extension}'
                    else:
                        text += f'\n+ [DONE] {extension}'
                except Exception as e:
                    failed.append(extension)
                    errors.append(e)
                    if len(text)==0:
                        text = f'```diff\n- [FAIL] {extension}'
                    else:
                        text += f'\n- [FAIL] {extension}'
            await msg.edit(content=f'Unload completed (`{len(extensions)-len(failed)}/{len(extensions)}` successful)\n\n{text}```')
            text = ''
            index = 0
            for fail in failed:
                if len(text)==0:
                    text = f'Extension `{fail}`\n```{errors[index]}```'
                else:
                    text = f'\n\nExtension `{fail}`\n```{errors[index]}```'
                index += 1
            if not len(failed)==0:
                await ctx.author.send(f'**Fail logs**\n{text}')
        else:
            await ctx.send('**OOPS**: Only the owner can run unload! :x:')

    @commands.command(hidden=True, aliases=['update'])
    async def upgrade(self, ctx):
        if not ctx.author.id == 356456393491873795:
            return
        embed = discord.Embed(title='Checking for upgrades...', description='Getting latest version from remote')
        msg = await ctx.send(embed=embed)
        try:
            r = requests.get(check_endpoint+"/update.json",headers={'Cache-Control': 'no-cache'})
            open('update_new.json','wb').write(r.content)
            with open('update.json', 'r') as file:
                current = json.load(file)
            with open('update_new.json', 'r') as file:
                new = json.load(file)
            release = new['release']
            version = new['version']
            update_available = new['release'] > current['release']
            should_reboot = new['reboot'] > current['release']
            try:
                desc = new['description']
            except:
                desc = 'No description is available for this upgrade.'
        except:
            embed.title = 'Failed to check for updates'
            embed.description = 'Could not find a valid update.json file on remote'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        if not update_available:
            embed.title = 'No updates available'
            embed.description = 'Unifier is up-to-date.'
            embed.colour = 0x00ff00
            return await msg.edit(embed=embed)
        print('Upgrade available: '+current['release']+' ==> '+new['release'])
        print('Confirm upgrade through Discord.')
        embed.title = 'Update available'
        embed.description = f'An update is available for Unifier!\n\nCurrent version: {current["version"]} (`{current["release"]}`)\nNew version: {version} (`{release}`)\n\n{desc}'
        embed.colour = 0xffcc00
        if should_reboot:
            embed.set_footer(text='The bot will need to reboot to apply the new update.')
        row = [
            discord.ui.Button(style=discord.ButtonStyle.green, label='Upgrade', custom_id=f'accept', disabled=False),
            discord.ui.Button(style=discord.ButtonStyle.gray, label='Nevermind', custom_id=f'reject', disabled=False)
        ]
        btns = discord.ui.ActionRow(row[0], row[1])
        components = discord.ui.MessageComponents(btns)
        await msg.edit(embed=embed, components=components)

        def check(interaction):
            return interaction.user.id == ctx.author.id and interaction.message.id == msg.id

        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await msg.edit(components=components)
        if interaction.custom_id == 'reject':
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await interaction.response.edit_message(components=components)
        print('Upgrade confirmed, preparing...')
        embed.title = 'Backing up...'
        embed.description = 'Your data is being backed up.'
        await interaction.response.edit_message(embed=embed, components=None)
        try:
            folder = os.getcwd() + '/old'
            try:
                os.mkdir(folder)
            except:
                pass
            folder = os.getcwd() + '/old/cogs'
            try:
                os.mkdir(folder)
            except:
                pass
            for file in os.listdir(os.getcwd() + '/cogs'):
                print('Backing up: '+os.getcwd() + '/cogs/' + file)
                os.system('cp ' + os.getcwd() + '/cogs/' + file + ' ' + os.getcwd() + '/old/cogs/' + file)
            print('Backing up: ' + os.getcwd() + '/unifier.py')
            os.system('cp ' + os.getcwd() + '/unifier.py ' + os.getcwd() + '/old/unifier.py')
            print('Backing up: ' + os.getcwd() + '/data.json')
            os.system('cp ' + os.getcwd() + '/data.json ' + os.getcwd() + '/old/data.json')
            print('Backing up: ' + os.getcwd() + '/config.json')
            os.system('cp ' + os.getcwd() + '/config.json ' + os.getcwd() + '/old/config.json')
        except:
            print('Backup failed, abort upgrade.')
            embed.title = 'Backup failed'
            embed.description = 'Unifier could not create a backup. The upgrade has been aborted.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        print('Backup complete, requesting final confirmation.')
        embed.title = 'Start the upgrade?'
        embed.description = '- :inbox_tray: Your files have been backed up in `[Unifier root directory]/backup.`\n- :wrench: Any modifications you made to Unifier will be wiped, unless they are a part of the new upgrade.\n- :warning: Once started, you cannot abort the upgrade.'
        await msg.edit(embed=embed, components=components)
        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60.0)
        except:
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await msg.edit(components=components)
        if interaction.custom_id == 'reject':
            row[0].disabled = True
            row[1].disabled = True
            btns = discord.ui.ActionRow(row[0], row[1])
            components = discord.ui.MessageComponents(btns)
            return await interaction.response.edit_message(components=components)
        print('Upgrade confirmed, upgrading Unifier...')
        print()
        embed.title = 'Upgrading Unifier'
        embed.description = ':hourglass_flowing_sand: Downloading updates\n:x: Installing updates\n:x: Reloading modules'
        await msg.edit(embed=embed, components=None)
        log(type='UPG', status='info', content='Starting upgrade')
        try:
            print('')
            log(type='GIT',status='info',content='Purging old update files')
            os.system('rm -rf '+os.getcwd()+'/update')
            log(type='GIT', status='info', content='Downloading from remote repository...')
            os.system('git clone --branch '+branch+' '+files_endpoint+' '+os.getcwd()+'/update')
            log(type='GIT', status='info', content='Confirming download...')
            x = open(os.getcwd() + '/update/update.json', 'r')
            x.close()
            log(type='GIT', status='ok', content='Download confirmed, proceeding with upgrade')
        except:
            log(type='UPG', status='error', content='Download failed, no rollback required')
            embed.title = 'Upgrade failed'
            embed.description = 'Could not download updates. No rollback is required.'
            embed.colour = 0xff0000
            await msg.edit(embed=embed)
            raise
        try:
            log(type='INS', status='info', content='Installing upgrades')
            embed.title = 'Upgrading Unifier'
            embed.description = ':white_check_mark: Downloading updates\n:hourglass_flowing_sand: Installing updates\n:x: Reloading modules'
            await msg.edit(embed=embed)
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update/unifier.py')
            os.system('cp ' + os.getcwd() + '/update/unifier.py ' + os.getcwd() + '/unifier.py')
            log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update/update.json')
            os.system('cp ' + os.getcwd() + '/update/update.json ' + os.getcwd() + '/update.json')
            for file in os.listdir(os.getcwd() + '/update/cogs'):
                log(type='INS', status='info', content='Installing: ' + os.getcwd() + '/update/cogs/'+file)
                os.system('cp ' + os.getcwd() + '/update/cogs/' + file + ' ' + os.getcwd() + '/cogs/' + file)
            if should_reboot:
                log(type='UPG', status='ok', content='Upgrade complete, reboot required')
                embed.title = 'Restart to apply upgrade'
                embed.description = 'The upgrade was successful. Please reboot Unifier to apply the upgrades.'
                embed.colour = 0x00ff00
                await msg.edit(embed=embed)
            else:
                embed.title = 'Upgrading Unifier'
                embed.description = ':white_check_mark: Downloading updates\n:white_check_mark: Installing updates\n:hourglass_flowing_sand: Reloading modules'
                await msg.edit(embed=embed)
                for cog in list(self.bot.extensions):
                    log(type='UPG', status='ok', content='Restarting extension: '+ cog)
                    self.bot.reload_extension(cog)
                log(type='UPG', status='ok', content='Upgrade complete')
                embed.title = 'Upgrade successful'
                embed.description = 'The upgrade was successful! :partying_face:'
                embed.colour = 0x00ff00
                await msg.edit(embed=embed)
        except:
            log(type='UPG', status='error', content='Upgrade failed, attempting rollback')
            embed.title = 'Upgrade failed'
            try:
                log(type='RBK', status='info', content='Reverting: ' + os.getcwd() + '/unifier.py')
                os.system('cp ' + os.getcwd() + '/old/unifier.py ' + os.getcwd() + '/unifier.py')
                log(type='RBK', status='info', content='Reverting: ' + os.getcwd() + '/data.json')
                os.system('cp ' + os.getcwd() + '/old/data.json ' + os.getcwd() + '/data.json')
                log(type='RBK', status='info', content='Reverting: ' + os.getcwd() + '/update.json')
                os.system('cp ' + os.getcwd() + '/old/update.json ' + os.getcwd() + '/update.json')
                log(type='RBK', status='info', content='Reverting: ' + os.getcwd() + '/config.json')
                os.system('cp ' + os.getcwd() + '/old/config.json ' + os.getcwd() + '/config.json')
                for file in os.listdir(os.getcwd() + '/old/cogs'):
                    log(type='RBK', status='info', content='Reverting: ' + os.getcwd() + '/cogs/'+file)
                    os.system('cp ' + os.getcwd() + '/old/cogs/' + file + ' ' + os.getcwd() + '/cogs/' + file)
                log(type='RBK', status='ok', content='Rollback success')
                embed.description = 'The upgrade failed, and all files have been rolled back.'
            except:
                log(type='RBK', status='error', content='Rollback failed')
                embed.description = 'The upgrade failed, and the bot may now be in a crippled state.'
            await msg.edit(embed=embed)
            raise

def setup(bot):
    bot.add_cog(Admin(bot))

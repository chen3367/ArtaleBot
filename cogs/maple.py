import discord
import typing
import aiohttp, aiofiles
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from table2ascii import table2ascii as t2a
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
import json
from collections import defaultdict

with open('src/maple/mob.json',encoding="utf-8") as f:
  mob = json.load(f)

with open('src/maple/drop_data.json',encoding="utf-8") as f:
  drop_data = json.load(f)

with open('src/maple/boss_time.json',encoding="utf-8") as f:
  boss_time = json.load(f)

with open('src/maple/map.json',encoding="utf-8") as f:
  maple_map = json.load(f)

with open('src/maple/boss_time.json',encoding="utf-8") as f:
  boss_time = json.load(f)

with open('src/maple/item.json',encoding="utf-8") as f:
  item = json.load(f)

item_list = {v:k for k, v in item.items()}

def reverse_dict(input_dict: dict[str, list[str]]) -> dict[str, list[str]]:
    reversed_dict = defaultdict(list)
    for key, values in input_dict.items():
        for val in values:
            reversed_dict[val].append(key)
    return dict(reversed_dict)

drop_mob = reverse_dict(drop_data)

class Mob(discord.ui.View):
    def __init__(self, mob, bot, index = 0) -> None:
        super().__init__(timeout=None)
        self.mob = mob
        self.bot = bot
        self.index = index

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.index -= 1
        await self.callback(interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.index += 1
        await self.callback(interaction)

    async def callback(self, interaction: discord.Interaction):
        mob_id = self.mob[self.index][0]
        maps = await self.bot.database.select("b.*", "maple_mob_map a inner join maple_map b on a.map_id = b.id", mob_id = mob_id)
        embed = discord.Embed(
            title=f"{self.mob[self.index][1]} {self.index+1}/{len(self.mob)}", description=f"[更多詳細資訊](https://maplestory.wiki/TWMS/256/mob/{mob_id})", color=0xBEBEFE
        )
        embed.add_field(name="", value=formatted_mob_info(self.mob[self.index], maps), inline=False)
        embed.set_thumbnail(url=f"https://maplestory.io/api/TWMS/256/mob/{mob_id}/icon")

        for item in self.children:
            if item.label == "<":
                item.disabled = not self.index
            else:
                item.disabled = self.index == (len(self.mob) - 1)

        await interaction.response.edit_message(embed=embed, view=self, content=None)

def autocompletion_dict(items: dict):
    async def getChoice(
            interaction: discord.Interaction,
            current: str
    ) -> typing.List[app_commands.Choice[str]]:
        data = []
        for name, value in items.items():
            if current in name:
                data.append(app_commands.Choice(name=name, value=value))
            if len(data) >= 25:
                break
        return data
    return getChoice

def autocompletion_list(items: list[str]):
    async def getChoice(
            interaction: discord.Interaction,
            current: str
    ) -> typing.List[app_commands.Choice[str]]:
        data = []
        for item in items:
            if current in item:
                data.append(app_commands.Choice(name=item, value=item))
            if len(data) >= 25:
                break
        return data
    return getChoice

def formatted_mob_info(mob):
    result = []
    result.append(f"等級: {mob['level'].values[0]}")
    result.append(f"經驗值: {mob['exp'].values[0]}")
    result.append(f"HP: {mob['maxHP'].values[0]}")
    result.append(f"MP: {mob['maxMP'].values[0]}")
    result.append(f"移動速度: {int(mob['speed'].values[0])}")
    result.append(f"物攻: {mob['physicalDamage'].values[0]}")
    result.append(f"物防: {mob['physicalDefense'].values[0]}")
    result.append(f"魔攻: {mob['magicDamage'].values[0]}")
    result.append(f"魔防: {mob['magicDefense'].values[0]}")
    result.append(f"命中率: {mob['accuracy'].values[0]}")
    result.append(f"迴避率: {mob['evasion'].values[0]}")
    result.append(f"KB值: {int(mob['minimumPushDamage'].values[0])}")
    result.append(f"Boss: {'是' if bool(mob['isBoss'].values[0]) else '否'}")
    return "\n".join(result)

class Maple(commands.Cog, name="maple"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="maple",
        description="楓之谷相關指令",
        hidden=True
    )
    async def maple(self, context: Context) -> None:
        """
        Maplestory functions.

        :param context: The hybrid command context.
        """
        if context.invoked_subcommand is None:
            embed = discord.Embed(
                title="Error",
                description="Please specify a subcommand.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
    
    @maple.command(name="mob", description="取得怪物資訊")
    @app_commands.autocomplete(name=autocompletion_list(drop_data.keys()))
    @app_commands.describe(
        name="怪物名稱"
    )
    async def mob(self, context: Context, name: str) -> None:
        mob_info = mob[name]
        map_info = maple_map[name].keys()
        boss_respawn_time = boss_time.get(name, "")
        drop_list = sorted(drop_data[name], key = lambda x: int(item_list.get(x, "9999999")))
        embed = discord.Embed(
            title=f"**{name}** { '(BOSS)' if boss_respawn_time else ''}", 
            description=f"資料來源: [Artale怪物掉落物一覽](https://a2983456456.github.io/artale-drop/)", 
            color=0xBEBEFE
        )

        embed.add_field(
            name="",
            value=(
                "```ini\n"
                "[怪物資訊]\n"
                f"等級: {mob_info[0]}\n"
                f"HP: {mob_info[1]}\n"
                f"MP: {mob_info[2]}\n"
                f"經驗值: {mob_info[3]}\n"
                f"迴避: {mob_info[4]}\n"
                f"物防: {mob_info[5]}\n"
                f"魔防: {mob_info[6]}\n"
                f"命中需求: {mob_info[7]}\n"
                "```"
                "```ini\n"
                "[出沒地圖]\n"
            )  + "\n".join(map_info) + "```"
        )

        embed.add_field(
            name="",
            value= "```xml\n"
            + "<裝備>\n"
            + "\n".join(x for x in drop_list if 1000000 <= int(item_list[x]) < 2000000)
            + "```"
            + "```xml\n"
            + "<消耗>\n"
            + "\n".join(x for x in drop_list if 2000000 <= int(item_list[x]) < 3000000)
            + "```" 
            + "```xml\n"
            + "<其他>\n"
            + "\n".join(x for x in drop_list if int(item_list[x]) < 1000000 or int(item_list[x]) >= 3000000)
            + "```" 
        )

        ID = mob_info[8].split('.')[0]
        embed.set_thumbnail(url=f"https://maplestory.io/api/TWMS/256/mob/{ID}/render/stand")
        await context.send(embed=embed)
    
    @maple.command(name="item", description="物品掉落資訊")
    @app_commands.autocomplete(name=autocompletion_list(drop_mob.keys()))
    @app_commands.describe(
        name="物品名稱"
    )
    async def item(self, context: Context, name: str) -> None:
        drop_list = drop_mob[name]
        embed = discord.Embed(
            title=f"**{name}**", 
            description=f"資料來源: [Artale怪物掉落物一覽](https://a2983456456.github.io/artale-drop/)", 
            color=0xBEBEFE
        )

        embed.add_field(
            name="",
            value="\n".join(drop_list)
        )

        try:
            embed.set_thumbnail(url=f"https://maplestory.io/api/TWMS/256/item/{item_list[name]}/icon")
            await context.send(embed=embed)
        except:
            image = discord.File(f"image/thumbnail.png", filename=f"thumbnail.png")
            embed.set_thumbnail(url=f"attachment://thumbnail.png")
            await context.send(file=image, embed=embed)
    
    @maple.command(name="opq_cd", description="當日CD顏色查詢")
    async def mob(self, context: Context) -> None:

        # Get current UTC time as a timezone-aware datetime
        now_utc = datetime.now(timezone.utc)

        weekday = {0: "日", 1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", }

        # Convert to UTC+8
        time_utc8 = now_utc.astimezone(ZoneInfo("Asia/Singapore"))
        weekday_num_utc8 = (time_utc8.weekday() + 1) % 7

        # Convert to UTC-5
        time_utc_minus_5 = now_utc.astimezone(ZoneInfo("America/Jamaica"))
        weekday_num_minus_5 = (time_utc_minus_5.weekday() + 1) % 7

        # Get disk name
        item_id = 4001056 + weekday_num_minus_5
        url = f"https://maplestory.io/api/TWMS/256/item/{item_id}/name"
        item = requests.get(url).json()

        embed = discord.Embed(
            title=item["name"], 
            description="", 
            color=0xBEBEFE
        )

        embed.add_field(name="台灣時間(UTC+8)", value=f"{time_utc8.strftime('%Y-%m-%d %H:%M:%S')} 星期{weekday[weekday_num_utc8]}", inline=False)
        embed.add_field(name="系統時間(UTC-5):", value=f"{time_utc_minus_5.strftime('%Y-%m-%d %H:%M:%S')} 星期{weekday[weekday_num_minus_5]}", inline=False)

        embed.set_thumbnail(url=f"https://maplestory.io/api/GMS/62/item/{item_id}/icon")
        await context.send(embed=embed)

    @maple.command(name="change_thumbnail_by_attachment", hidden=True)
    @commands.is_owner()
    async def change_thumbnail_by_attachment(self, context: Context, image: discord.Attachment) -> None:
        try:
            await image.save("image/thumbnail.png")
            embed = discord.Embed(
                title="成功", description="", color=0xBEBEFE
            )
        except Exception as e:
            embed = discord.Embed(
                title="錯誤", description=e, color=0xE02B2B
            )            
        await context.send(embed=embed, ephemeral=True)

    @maple.command(name="change_thumbnail_by_url", hidden=True)
    @commands.is_owner()
    async def change_thumbnail_by_url(self, context: Context, url: str) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    async with aiofiles.open("image/thumbnail.png", 'wb') as f:
                        await f.write(await resp.read())
            embed = discord.Embed(
                title="成功", description="", color=0xBEBEFE
            )
        except Exception as e:
            embed = discord.Embed(
                title="錯誤", description=e, color=0xE02B2B
            )            
        await context.send(embed=embed, ephemeral=True)

async def setup(bot) -> None:
    await bot.add_cog(Maple(bot))
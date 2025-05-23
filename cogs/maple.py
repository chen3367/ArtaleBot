import discord
import typing
import aiohttp, aiofiles
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from src.maple import var
import pandas as pd
from table2ascii import table2ascii as t2a
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests

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
    @app_commands.autocomplete(name=autocompletion_list(var.mob_list))
    @app_commands.describe(
        name="怪物名稱"
    )
    async def mob(self, context: Context, name: str) -> None:
        mob_info = var.mob[var.mob['name_tw'] == name]
        embed = discord.Embed(
            title=f"**{name}**", description="", color=0xBEBEFE
        )
        embed.add_field(name="", value=formatted_mob_info(mob_info), inline=True)
        if not pd.isna(mob_info['drop'].values[0]):
            embed.add_field(name="掉落物", value=mob_info['drop'].values[0], inline=True)
        if not pd.isna(mob_info['foundAt'].values[0]):
            embed.add_field(name="出沒地點", value=mob_info['foundAt'].values[0], inline=True)

        ID = int(mob_info['ID'].values[0])
        embed.set_thumbnail(url=f"https://maplestory.io/api/TWMS/256/mob/{ID}/render/stand")
        await context.send(embed=embed)
    
    @maple.command(name="chance_to_hit", description="物攻職業命中率計算")
    @app_commands.autocomplete(name=autocompletion_list(var.mob_list))
    @app_commands.describe(
        name="怪物名稱",
        level="角色等級",
        accuracy="命中率"
    )
    # Chance to Hit = Accuracy/((1.84 + 0.07 * D) * Avoid) - 1
    # (D = monster level - your level. If negative, make it 0.)
    async def mob(self, context: Context, name: str, level: int, accuracy: int) -> None:
        mob_info = var.mob[var.mob['name_tw'] == name]
        embed = discord.Embed(
            title=f"**{name}**", description=f"", color=0xBEBEFE
        )
        mob_level, evasion = mob_info["level"].values[0], mob_info["evasion"].values[0]
        
        header = ['accuracy\\level'] + [l for l in range(level, level+3)]
        acc_table = [[acc] + [min(100, float(round((acc/((1.84 + 0.07 * max(0, mob_level - l)) * evasion) - 1) * 100, 1))) for l in range(level, level+3)] for acc in range(accuracy, accuracy+10)]

        output = t2a(
            header = header,
            body = acc_table,
            first_col_heading=True
        )

        embed.add_field(name="命中率", value=f"```\n{output}\n```", inline=True)

        ID = int(mob_info['ID'].values[0])
        embed.set_thumbnail(url=f"https://maplestory.io/api/TWMS/256/mob/{ID}/render/stand")
        await context.send(embed=embed)
    
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
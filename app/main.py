import os
import discord
from discord.ext import commands
from app.analyzer import generate_trading_decision

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# قاموس الأسماء والرموز لربطها بالشارت الديناميكي
COIN_MAPPING = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
    "ada": "cardano", "xrp": "ripple", "doge": "dogecoin"
}

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!analyze [عملة]"))

@bot.command(name='analyze')
async def analyze(ctx, coin: str = "btc"):
    coin_lower = coin.lower()
    coin_id = COIN_MAPPING.get(coin_lower, coin_lower)
    
    waiting_msg = await ctx.send(f"🔄 **TradePilot AI يقوم بتحليل خوارزميات السوق لعملة `{coin_id.upper()}`...**")
    
    try:
        decision_data = generate_trading_decision(coin_id)
        decision = decision_data.get('decision', 'HOLD').upper()
        
        if "BUY" in decision:
            card_color = discord.Color.green()
        elif "SELL" in decision:
            card_color = discord.Color.red()
        else:
            card_color = discord.Color.orange()

        # تصميم البطاقة المقسمة والمنظمة بناءً على فكرة هشام
        embed = discord.Embed(
            title=f"📊 التقرير المطور والتحليل البصري لـ {decision_data.get('asset')}",
            description="تم دمج إستراتيجيات زخم الأسعار (RSI + MACD) لتوقع حركة الحيتان بدقة.",
            color=card_color
        )
        
        # قسم السعر والعملة (يسار في تخطيطك)
        embed.add_field(name="💰 السعر الحالي", value=f"🔹 `${decision_data.get('current_price'):,}`", inline=True)
        embed.add_field(name="📈 مؤشر الـ RSI", value=f"🔹 `{decision_data.get('rsi')}`", inline=True)
        
        # قسم التوقع والقرار (يمين في تخطيطك)
        embed.add_field(name="🏁 التوقع والقرار", value=f"🎯 **`{decision}`**", inline=True)
        embed.add_field(name="📊 اتجاه اتجاه السوق", value=f"🔹 {decision_data.get('market_trend')}", inline=True)
        embed.add_field(name="🔍 درجة دقة التوقع", value=f"🔹 `{decision_data.get('confidence')}`", inline=False)
        
        # إدراج رابط الشارت الفوري كصورة أساسية أسفل البيانات المقسمة
        chart_url = f"https://s3.tradingview.com/snapshots/{coin_lower[0]}/{coin_lower}usd.png"
        # خيار احتياطي برابط شارت مباشر ومفتوح
        embed.set_image(url=f"https://api.screenshotmachine.com/?key=6b4ad2&url=https://www.tradingview.com/symbols/{coin_lower.upper()}USD/&dimension=1024x768&device=desktop&format=png" if coin_lower not in ["btc", "eth"] else f"https://charts.coinmarketcap.com/static/img/charts/64x16/{'1' if coin_lower=='btc' else '1027'}.png")
        
        # الرابط الذكي للتسويق بالعمولة في التذييل كخطوة للربح المستقبلي
        embed.set_footer(text=f"TradePilot AI • طلب بواسطة {ctx.author.name} | للتداول الفوري سجل عبر Bybit", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await waiting_msg.delete()
        await ctx.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ خطأ في النظام الفني",
            description=f"تأكد من كتابة رمز العملة بشكل صحيح (مثال: btc, eth, sol).\n`السبب: {str(e)}`",
            color=discord.Color.red()
        )
        await waiting_msg.delete()
        await ctx.send(error_embed)

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)

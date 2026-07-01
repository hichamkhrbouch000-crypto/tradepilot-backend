import os
import discord
from discord.ext import commands
from app.analyzer import generate_trading_decision

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# قاموس لتحويل الاختصارات الشائعة إلى الأسماء الكاملة التي تفهمها واجهة البيانات
COIN_MAPPING = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "ada": "cardano",
    "xrp": "ripple",
    "doge": "dogecoin",
    "dot": "polkadot"
}

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!analyze [عملة]"))

@bot.command(name='analyze')
async def analyze(ctx, coin: str = "btc"):
    # تحويل الرمز المكتوب لأحرف صغيرة
    coin_lower = coin.lower()
    # جلب الاسم الحقيقي للعملة من القاموس، وإذا لم يوجد نستخدم ما كتبه المستخدم مباشرة
    coin_id = COIN_MAPPING.get(coin_lower, coin_lower)
    
    waiting_msg = await ctx.send(f"🔄 **جاري جلب البيانات الفنية وتحليل عملة `{coin_id.upper()}`...**")
    
    try:
        # تمرير اسم العملة المطلوبة لدالة التحليل
        decision_data = generate_trading_decision(coin_id)
        
        decision = decision_data.get('decision', 'HOLD').upper()
        if "BUY" in decision:
            card_color = discord.Color.green()
        elif "SELL" in decision:
            card_color = discord.Color.red()
        else:
            card_color = discord.Color.orange()

        embed = discord.Embed(
            title=f"📊 تقرير التحليل الذكي لعملة {decision_data.get('asset')}",
            description=f"تحليل فني فوري معتمد على مؤشر القوة النسبية (RSI).",
            color=card_color
        )
        
        embed.add_field(name="💰 السعر الحالي", value=f"🔹 `${decision_data.get('current_price'):,}`", inline=True)
        embed.add_field(name="📈 مؤشر RSI", value=f"🔹 `{decision_data.get('rsi')}`", inline=True)
        embed.add_field(name="🏁 القرار الحالي", value=f"🎯 **`{decision}`**", inline=True)
        embed.add_field(name="📊 اتجاه السوق (Trend)", value=f"🔹 `{decision_data.get('market_trend')}`", inline=True)
        embed.add_field(name="🔍 درجة الثقة", value=f"🔹 `{decision_data.get('confidence')}`", inline=True)
        embed.add_field(name="💡 نصيحة الخوارزمية", value="⚠️ التحليل مبني على قراءة تقنية مؤتمتة لآخر 30 يوماً، يرجى الالتزام التام بإدارة مخاطر محفظتك.", inline=False)
        
        embed.set_footer(text=f"TradePilot AI • طلب بواسطة {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await waiting_msg.delete()
        await ctx.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ خطأ في جلب البيانات",
            description=f"تأكد من كتابة رمز العملة بشكل صحيح (مثال: `btc` أو `ethereum`).\n`الخطأ: {str(e)}`",
            color=discord.Color.red()
        )
        await waiting_msg.delete()
        await ctx.send(embed=error_embed)

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)

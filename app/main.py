import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from app.analyzer import generate_trading_decision

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

COIN_MAPPING = {
    "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
    "ada": "cardano", "xrp": "ripple", "doge": "dogecoin"
}

# 1. فئة الأزرار الدائمة (Persistent View) - لا تموت أبداً عند إعادة تشغيل البوت
class PersistentTradingView(View):
    def __init__(self):
        super().__init__(timeout=None) # تفعيل العمل اللانهائي للأزرار

    async def handle_button_logic(self, interaction: discord.Interaction, custom_id: str):
        # تفكيك المعرف الحصري للزر لمعرفة العملة والفريم المطلوب
        # الصيغة: "tradepilot:[coin]:[timeframe]"
        try:
            parts = custom_id.split(":")
            if len(parts) < 3:
                return
            
            _, coin_lower, timeframe = parts
            await interaction.response.defer() # تأكيد الاستلام لمنع ظهور خطأ التباطؤ بالهاتف
            
            coin_id = COIN_MAPPING.get(coin_lower, coin_lower)
            decision_data = generate_trading_decision(coin_id, timeframe)
            decision = decision_data.get('decision', 'HOLD').upper()
            
            if "BUY" in decision:
                card_color = discord.Color.green()
            elif "SELL" in decision:
                card_color = discord.Color.red()
            else:
                card_color = discord.Color.orange()

            embed = discord.Embed(
                title=f"📊 تقرير شمعة ({timeframe.upper()}) لـ {decision_data.get('asset')}",
                description=f"لوحة تفاعلية محدثة بالكامل لإطار حركة السوق الحالية.",
                color=card_color
            )
            
            embed.add_field(name="💰 السعر الحالي", value=f"🔹 `${decision_data.get('current_price'):,}`", inline=True)
            embed.add_field(name="📈 مؤشر الـ RSI", value=f"🔹 `{decision_data.get('rsi')}`", inline=True)
            embed.add_field(name="🏁 التوقع والقرار", value=f"🎯 **`{decision}`**", inline=True)
            embed.add_field(name="📊 اتجاه الحركة الحالي", value=f"🔹 {decision_data.get('market_trend')}", inline=True)
            embed.add_field(name="🔍 درجة الدقة والنطاق", value=f"🔹 `{decision_data.get('confidence')}`", inline=False)
            
            embed.set_image(url=f"https://images.cryptocompare.com/sparkchart/{coin_lower.upper()}/USD/latest.png?ts={interaction.created_at.timestamp()}")
            embed.set_footer(text="TradePilot AI • لوحة تحكم فورية دائمية | للتداول سجل عبر Bybit")
            
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

# بناء هيكلية البوت مع ربط الأزرار الدائمة عند الإقلاع
class TradePilotBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # تسجيل الـ View في ذاكرة الديسكورد العميقة لكي تعمل الأزرار القديمة دائماً
        self.add_view(PersistentTradingView())

bot = TradePilotBot()

# دالة مساعدة لإنشاء الأزرار بشكل ديناميكي بروابط معرفة ثابتة ومستقرة
def create_view_for_coin(coin_lower):
    view = PersistentTradingView()
    timeframes = ["5m", "1h", "4h", "1d"]
    
    for tf in timeframes:
        btn = Button(
            label=tf.upper(), 
            style=discord.ButtonStyle.primary if tf != "5m" else discord.ButtonStyle.secondary,
            custom_id=f"tradepilot:{coin_lower}:{tf}" # معرف فريد ثابت مبرمج مسبقاً للديسكورد
        )
        # ربط الضغط بالدالة الموحدة
        btn.callback = lambda i, cid=btn.custom_id: view.handle_button_logic(i, cid)
        view.add_item(btn)
    return view

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!analyze و !risk"))

@bot.command(name='analyze')
async def analyze(ctx, coin: str = "btc"):
    coin_lower = coin.lower()
    coin_id = COIN_MAPPING.get(coin_lower, coin_lower)
    
    waiting_msg = await ctx.send(f"🔄 **TradePilot AI يقوم بتحضير لوحة التحكم التفاعلية لعملة `{coin_id.upper()}`...**")
    
    try:
        decision_data = generate_trading_decision(coin_id, "1d")
        decision = decision_data.get('decision', 'HOLD').upper()
        
        card_color = discord.Color.green() if "BUY" in decision else (discord.Color.red() if "SELL" in decision else discord.Color.orange())

        embed = discord.Embed(
            title=f"📊 تقرير شمعة (1D) لـ {decision_data.get('asset')}",
            description=f"لوحة تفاعلية دائمة ومقاومة للانقطاع. اضغط على الفريمات في الأسفل للتنقل الفوري.",
            color=card_color
        )
        
        embed.add_field(name="💰 السعر الحالي", value=f"🔹 `${decision_data.get('current_price'):,}`", inline=True)
        embed.add_field(name="📈 مؤشر الـ RSI", value=f"🔹 `{decision_data.get('rsi')}`", inline=True)
        embed.add_field(name="🏁 التوقع والقرار", value=f"🎯 **`{decision}`**", inline=True)
        embed.add_field(name="📊 اتجاه الحركة الحالي", value=f"🔹 {decision_data.get('market_trend')}", inline=True)
        embed.add_field(name="🔍 درجة الدقة والنطاق", value=f"🔹 `{decision_data.get('confidence')}`", inline=False)
        
        embed.set_image(url=f"https://images.cryptocompare.com/sparkchart/{coin_lower.upper()}/USD/latest.png?ts={ctx.message.created_at.timestamp()}")
        embed.set_footer(text=f"TradePilot AI • طلب بواسطة {ctx.author.name} | للتداول سجل عبر Bybit", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        view = create_view_for_coin(coin_lower)
        
        await waiting_msg.delete()
        await ctx.send(embed=embed, view=view)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ خطأ في النظام الفني",
            description=f"تأكد من كتابة الرموز بشكل صحيح.\n`السبب: {str(e)}`",
            color=discord.Color.red()
        )
        await waiting_msg.delete()
        await ctx.send(embed=error_embed)

# 2. أمر حاسبة إدارة المخاطر الجديد والمستقل (!risk)
@bot.command(name='risk')
async def risk(ctx, balance: float = None, risk_percent: float = 2.0):
    if balance is None:
        await ctx.send("❌ **طريقة الاستخدام الخاطئة!**\nيرجى كتابة الأمر بالشكل التالي لقراءة حسابك الحقيقي:\n`!risk [رأس المال] [نسبة المخاطرة]`\n*مثال:* `!risk 1000 2` (لحساب مخاطرة 2% على حساب بقيمة 1000 دولار)")
        return

    # حساب الحسبة المالية الدقيقة ميكانيكياً لحماية المحفظة
    allowed_loss = (balance * risk_percent) / 100
    position_size_zone1 = balance * 0.20 # الدخول الأول بـ 20% من الحساب كأمان
    position_size_zone2 = balance * 0.30 # تعزيز بـ 30% عند الارتداد
    
    embed = discord.Embed(
        title="🛡️ نظام إدارة المخاطر وتأمين الحسابات (Risk Management)",
        description=f"تحليل مالي مخصص لحساب بقيمة **`${balance:,}`** بناءً على نسبة مخاطرة **`{risk_percent}%`**.",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🚨 أقصى مبلغ مسموح بخسارته", value=f"🛑 **`${allowed_loss:,}`** إجمالاً في الصفقة.", inline=False)
    embed.add_field(name="📉 خطة الدخول المقسمة (Zone Entries)", value=f"🔹 **المنطقة 1 (دخول فوري):** `${position_size_zone1:,}` (20%)\n🔹 **المنطقة 2 (تعزيز عند الارتداد):** `${position_size_zone2:,}` (30%)", inline=False)
    embed.add_field(name="⚠️ توصية الرافعة المالية (Leverage)", value="💡 إذا كنت تتداول العقود الآجلة (Futures)، ينصح البوت بعدم تجاوز رافعة **`3X` إلى `5X`** كأقصى حد لتجنب المرجنة السريعة أثناء تذبذب السوق الحاد.", inline=False)
    
    embed.set_footer(text=f"TradePilot AI • المستشار المالي الرقمي الخاص بك | صمم بواسطة {ctx.author.name}")
    
    await ctx.send(embed=embed)

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)

import os
import discord
from discord.ext import commands
from app.analyzer import generate_trading_decision, analyze_technical_indicators

# إعداد الصلاحيات للبوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')
    # تعيين حالة البوت ليظهر للمستخدمين أنه يتابع الأوامر
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!analyze"))

@bot.command(name='analyze')
async def analyze(ctx):
    # إرسال رسالة انتظار مؤقتة مع إيموجي متحرك
    waiting_msg = await ctx.send("🔄 **جاري سحب البيانات الفنية وتحليل مؤشرات السوق... انتظر لحظة.**")
    
    try:
        # استدعاء دالات التحليل الفني من مشروعك
        decision_data = generate_trading_decision()
        metrics_data = analyze_technical_indicators()
        
        # تحديد لون البطاقة بناءً على القرار (أخضر للشراء، أحمر للبيع، برتقالي للانتظار)
        decision = decision_data.get('decision', 'HOLD').upper()
        if "BUY" in decision:
            card_color = discord.Color.green()
        elif "SELL" in decision:
            card_color = discord.Color.red()
        else:
            card_color = discord.Color.orange()

        # إنشاء بطاقة احترافية (Embed)
        embed = discord.Embed(
            title="📊 تقرير التحليل الفني لـ TradePilot AI",
            description="تم تحديث وتحليل المؤشرات الفنية للأسواق بناءً على الخوارزمية الذكية الحالية.",
            color=card_color
        )
        
        # إضافة الحقول وتنسيقها بشكل منظم ومتقابل
        embed.add_field(name="🏁 القرار الحالي", value=f"🔹 `{decision}`", inline=True)
        embed.add_field(name="📈 حالة الاتجاه (Trend)", value=f"🔹 `{metrics_data.get('market_trend', 'غير معروفة')}`", inline=True)
        embed.add_field(name="💡 نصيحة الأداة", value="⚠️ التداول ينطوي على مخاطر. يرجى دائماً الالتزام بإدارة رأس المال المستهدفة وعدم الدخول العشوائي.", inline=False)
        
        # إضافة تذييل وشعار أسفل البطاقة
        embed.set_footer(text=f"TradePilot AI • طلب بواسطة {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        # مسح رسالة الانتظار وإرسال البطاقة الاحترافية
        await waiting_msg.delete()
        await ctx.send(embed=embed)
        
    except Exception as e:
        # في حال حدوث أي خطأ، يتم إرساله داخل بطاقة حمراء منسقة
        error_embed = discord.Embed(
            title="❌ حدث خطأ داخلي",
            description=f"لم نتمكن من إتمام التحليل بسبب:\n`{str(e)}`",
            color=discord.Color.red()
        )
        await waiting_msg.delete()
        await ctx.send(embed=error_embed)

# استدعاء التوكن السري
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)

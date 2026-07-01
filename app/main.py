import os
import discord
from discord.ext import commands
from app.analyzer import generate_trading_decision, analyze_technical_indicators

# إعداد الصلاحيات للبوت
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# تحديد علامة التعجب ! كبادئة للأوامر
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'تم تشغيل البوت بنجاح باسم: {bot.user.name}')

@bot.command(name='analyze')
async def analyze(ctx):
    # إرسال رسالة انتظار للمستخدم أثناء جلب البيانات
    await ctx.send("🔄 جاري سحب البيانات وتحليل المؤشرات الفنية للأسواق... انتظر لحظة.")
    
    try:
        # استدعاء دالة التحليل الفني الموجودة مسبقاً في مشروعك
        decision_data = generate_trading_decision()
        metrics_data = analyze_technical_indicators()
        
        # تنسيق رسالة واضحة بداخل ديسكورد بالنتائج
        response = (
            f"📊 **تقرير التحليل الفني لـ TradePilot AI** 📊\n\n"
            f"🏁 **القرار الحالي:** {decision_data.get('decision', 'غير محدد')}\n"
            f"📈 **حالة السوق:** {metrics_data.get('market_trend', 'غير معروفة')}\n"
            f"💡 **نصيحة الأداة:** التداول بحذر وبناءً على إدارة المخاطر المستهدفة."
        )
        await ctx.send(response)
        
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ أثناء جلب التحليل الفني: {str(e)}")

# استدعاء التوكن السري من بيئة تشغيل Railway بأمان
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)

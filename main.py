import asyncio
from datetime import datetime, timedelta
import pytz
from telethon import TelegramClient, events
import random
import time
import os

# بيانات الحساب - عدل هذه القيم
API_ID = 20529343
API_HASH = "656199efaf0935e731164fb9d02e4aa6"
SESSION_STRING = "1BJWap1sAUKbAMz0u0rlA2N-DGqdv0nN_Y0mTgWlImj3-l4Q0y1EorS3bap1HwkZOnPuCq7qQ9x5h18e3HNITp0zxEjvo2nYnLfkQ64Xz07npQ3FYaXXjCOfkG8dorysjJ5g3G2WFSPIobFmcrVeNL-4GJ-AQncGxbPHuf5WtqMpi_7ZYq1rX2qitx9ZYM4TL6xSKbyfnEjqTBVp4m3ZJBfDkbU0MuP43l-RPOeRKMC_07KF-rZVYV0eWqfsW_zKXblaBUKVqMDU0ewBFYc9pxNvaqLyn0ZLz3NB8gPd8ygayjNvujLA04CuooUr1RrB_iYW-bc4RDI7sssxZbLYE1RttpiLsz1s="

client = TelegramClient(session=None, api_id=API_ID, api_hash=API_HASH)
TIMEZONE = pytz.timezone('Africa/Tripoli')  # توقيت ليبيا

# نظام الحماية من Flood
last_schedule_time = 0
min_delay = 13
max_delay = 32

def can_schedule():
    global last_schedule_time
    current_time = time.time()
    if current_time - last_schedule_time < min_delay:
        return False
    return True

def update_schedule_time():
    global last_schedule_time
    last_schedule_time = time.time()

def get_random_delay():
    return random.uniform(min_delay, max_delay)

def split_and_shuffle_messages(message_text):
    lines = message_text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    if len(lines) <= 1:
        return lines
    
    random.shuffle(lines)
    return lines

def generate_time_slots():
    now = datetime.now(TIMEZONE)
    
    # بداية اليوم (00:00)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # نهاية اليوم (24:00)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # الوقت الحالي مقرب لأقرب 15 دقيقة للأعلى
    current_hour = now.hour
    current_minute = now.minute
    
    # حساب أقرب 15 دقيقة قادمة
    next_quarter = ((current_minute // 15) + 1) * 15
    if next_quarter == 60:
        current_hour += 1
        next_quarter = 0
    
    start_time = now.replace(hour=current_hour, minute=next_quarter, second=0, microsecond=0)
    
    # إذا كان الوقت بعد 23:45، نبدأ من يوم جديد
    if start_time > end_of_day.replace(hour=23, minute=45):
        start_time = start_of_day + timedelta(days=1)
        end_of_day = end_of_day + timedelta(days=1)
    
    time_slots = []
    current_time_slot = start_time
    
    while current_time_slot <= end_of_day:
        time_slots.append(current_time_slot)
        current_time_slot += timedelta(minutes=15)
        
        # نتأكد ألا نتجاوز منتصف الليل
        if current_time_slot.hour == 0 and current_time_slot.minute == 0:
            break
    
    print(f"🕒 تم إنشاء {len(time_slots)} وقت جدولة من {start_time.strftime('%H:%M')}")
    return time_slots

def generate_time_slots_from_now():
    """إنشاء الأوقات بدءاً من الوقت الحالي (للأمر 'جدولة اليوم')"""
    now = datetime.now(TIMEZONE)
    
    # نهاية اليوم (23:59)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # الوقت الحالي مقرب لأقرب 15 دقيقة للأعلى
    current_hour = now.hour
    current_minute = now.minute
    
    # حساب أقرب 15 دقيقة قادمة
    next_quarter = ((current_minute // 15) + 1) * 15
    if next_quarter == 60:
        current_hour += 1
        next_quarter = 0
        if current_hour == 24:
            current_hour = 0
    
    start_time = now.replace(hour=current_hour, minute=next_quarter, second=0, microsecond=0)
    
    time_slots = []
    current_time_slot = start_time
    
    while current_time_slot <= end_of_day:
        time_slots.append(current_time_slot)
        current_time_slot += timedelta(minutes=15)
    
    print(f"📅 اليوم: {len(time_slots)} وقت من {start_time.strftime('%H:%M')} إلى 23:45")
    return time_slots

async def schedule_message(chat_id, message_text, schedule_time):
    try:
        now = datetime.now(TIMEZONE)
        time_difference = schedule_time - now
        
        if time_difference.total_seconds() > 0:
            await client.send_message(
                chat_id,
                message_text,
                schedule=schedule_time
            )
            print(f"✅ تم جدولة: '{message_text[:30]}...' في {schedule_time.strftime('%H:%M')}")
            return True
        else:
            print(f"⏰ الوقت مضى: {schedule_time.strftime('%H:%M')}")
            return False
    except Exception as e:
        print(f"❌ خطأ في الجدولة: {e}")
        return False

@client.on(events.NewMessage(pattern='جدولة'))
async def schedule_message_handler(event):
    if not can_schedule():
        wait_time = int(min_delay - (time.time() - last_schedule_time))
        await event.reply(f"⏳ انتظر {wait_time} ثانية قبل الجدولة مرة أخرى")
        return
    
    update_schedule_time()
    
    if event.is_reply:
        try:
            reply_message = await event.get_reply_message()
            message_text = reply_message.text
            
            if not message_text:
                await event.reply("❌ الرسالة فارغة")
                return
            
            split_messages = split_and_shuffle_messages(message_text)
            
            if not split_messages:
                await event.reply("❌ لا توجد رسائل صالحة للجدولة")
                return
            
            time_slots = generate_time_slots()
            
            if not time_slots:
                await event.reply("❌ لا توجد أوقات متاحة للجدولة اليوم")
                return
            
            successful = 0
            failed = 0
            
            total_messages = min(len(time_slots), len(split_messages))
            await event.reply(f"⏰ جاري جدولة {total_messages} رسالة بدءاً من {time_slots[0].strftime('%H:%M')}...")
            
            for i, schedule_time in enumerate(time_slots):
                if i >= len(split_messages):
                    break  # نتوقف إذا انتهت الرسائل
                
                message_to_schedule = split_messages[i % len(split_messages)]
                
                success = await schedule_message(event.chat_id, message_to_schedule, schedule_time)
                if success:
                    successful += 1
                else:
                    failed += 1
                
                delay = get_random_delay()
                await asyncio.sleep(delay)
            
            start_time = time_slots[0].strftime('%H:%M') if time_slots else "N/A"
            end_time = time_slots[-1].strftime('%H:%M') if time_slots else "N/A"
            
            report = f"""📊 تقرير الجدولة:
✅ تم الجدولة: {successful} رسالة
❌ فشل: {failed} رسالة
📝 الأسطر: {len(split_messages)}
🕒 الأوقات: {len(time_slots)}
⏰ من {start_time} إلى {end_time}"""
            await event.reply(report)
            
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}")
            print(f"خطأ رئيسي: {e}")
    else:
        await event.reply("↩️ الرد على الرسالة المراد جدولتها")

@client.on(events.NewMessage(pattern='جدولة اليوم'))
async def schedule_today_handler(event):
    if not can_schedule():
        wait_time = int(min_delay - (time.time() - last_schedule_time))
        await event.reply(f"⏳ انتظر {wait_time} ثانية قبل الجدولة مرة أخرى")
        return
    
    update_schedule_time()
    
    if event.is_reply:
        try:
            reply_message = await event.get_reply_message()
            message_text = reply_message.text
            
            if not message_text:
                await event.reply("❌ الرسالة فارغة")
                return
            
            split_messages = split_and_shuffle_messages(message_text)
            
            if not split_messages:
                await event.reply("❌ لا توجد رسائل صالحة للجدولة")
                return
            
            time_slots = generate_time_slots_from_now()
            
            if not time_slots:
                await event.reply("❌ لا توجد أوقات متاحة لليوم")
                return
            
            successful = 0
            failed = 0
            
            total_messages = min(len(time_slots), len(split_messages))
            await event.reply(f"📅 جاري جدولة {total_messages} رسالة لليوم بدءاً من {time_slots[0].strftime('%H:%M')}...")
            
            for i, schedule_time in enumerate(time_slots):
                if i >= len(split_messages):
                    break  # نتوقف إذا انتهت الرسائل
                
                message_to_schedule = split_messages[i % len(split_messages)]
                
                success = await schedule_message(event.chat_id, message_to_schedule, schedule_time)
                if success:
                    successful += 1
                else:
                    failed += 1
                
                delay = get_random_delay()
                await asyncio.sleep(delay)
            
            start_time = time_slots[0].strftime('%H:%M') if time_slots else "N/A"
            end_time = time_slots[-1].strftime('%H:%M') if time_slots else "N/A"
            
            report = f"""📊 تقرير جدولة اليوم:
✅ تم الجدولة: {successful} رسالة
❌ فشل: {failed} رسالة
📝 الأسطر: {len(split_messages)}
🕒 الأوقات: {len(time_slots)}
⏰ من {start_time} إلى {end_time}"""
            await event.reply(report)
            
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}")
            print(f"خطأ رئيسي: {e}")
    else:
        await event.reply("↩️ الرد على الرسالة المراد جدولتها")

@client.on(events.NewMessage(pattern='تقسيم'))
async def split_only_handler(event):
    if event.is_reply:
        try:
            reply_message = await event.get_reply_message()
            message_text = reply_message.text
            
            if not message_text:
                await event.reply("❌ الرسالة فارغة")
                return
            
            split_messages = split_and_shuffle_messages(message_text)
            
            if not split_messages:
                await event.reply("❌ لا توجد رسائل صالحة")
                return
            
            response = f"📋 الأسطر بعد التقسيم ({len(split_messages)}):\n\n"
            for i, line in enumerate(split_messages, 1):
                response += f"{i}. {line}\n"
            
            await event.reply(response)
            
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}")

@client.on(events.NewMessage(pattern='فحص'))
async def test_handler(event):
    try:
        now = datetime.now(TIMEZONE)
        time_slots = generate_time_slots()
        today_slots = generate_time_slots_from_now()
        
        response = f"""✅ البوت يعمل بشكل طبيعي
📍 التوقيت: ليبيا (Africa/Tripoli)
🕒 الوقت الحالي: {now.strftime('%Y-%m-%d %H:%M:%S')}
📊 الأوقات المتاحة:
   - الجدولة الكاملة: {len(time_slots)} وقت
   - جدولة اليوم: {len(today_slots)} وقت"""
        
        await event.reply(response)
        print("✅ تم فحص البوت")
    except Exception as e:
        print(f"❌ خطأ في الفحص: {e}")

@client.on(events.NewMessage(pattern='حذف المجدول'))
async def delete_scheduled_handler(event):
    if not can_schedule():
        wait_time = int(min_delay - (time.time() - last_schedule_time))
        await event.reply(f"⏳ انتظر {wait_time} ثانية قبل الحذف مرة أخرى")
        return
    
    update_schedule_time()
    
    try:
        scheduled_messages = await client.get_scheduled_messages(event.chat_id)
        
        if not scheduled_messages:
            await event.reply("ℹ️ لا توجد رسائل مجدولة")
            return
        
        deleted_count = 0
        for msg in scheduled_messages:
            try:
                await client.delete_messages(event.chat_id, [msg.id])
                deleted_count += 1
                print(f"🗑️ تم حذف رسالة مجدولة")
                
                delay = get_random_delay()
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"❌ خطأ في حذف رسالة: {e}")
        
        await event.reply(f"✅ تم حذف {deleted_count} رسالة مجدولة")
        
    except Exception as e:
        await event.reply(f"❌ خطأ في الحذف: {e}")

@client.on(events.NewMessage(pattern='عرض المجدول'))
async def show_scheduled_handler(event):
    try:
        scheduled_messages = await client.get_scheduled_messages(event.chat_id)
        
        if not scheduled_messages:
            await event.reply("ℹ️ لا توجد رسائل مجدولة")
            return
        
        scheduled_messages.sort(key=lambda x: x.date)
        
        response = f"📋 الرسائل المجدولة ({len(scheduled_messages)}):\n\n"
        
        for i, msg in enumerate(scheduled_messages[:10], 1):
            message_preview = msg.message[:50] + "..." if len(msg.message) > 50 else msg.message
            schedule_time = msg.date.astimezone(TIMEZONE).strftime('%H:%M')
            response += f"{i}. ⏰ {schedule_time} - {message_preview}\n"
        
        if len(scheduled_messages) > 10:
            response += f"\n... و {len(scheduled_messages) - 10} رسالة أخرى"
        
        await event.reply(response)
        
    except Exception as e:
        await event.reply(f"❌ خطأ في العرض: {e}")

async def main():
    await client.start(session_string=SESSION_STRING)
    print("✅ البوت يعمل...")
    print("📍 توقيت ليبيا (Africa/Tripoli)")
    print("🕒 نظام الجدولة: من 00:00 إلى 24:00")
    print("📅 جاهز لجدولة الرسائل")
    
    # عرض معلومات عن الأوقات الحالية
    now = datetime.now(TIMEZONE)
    time_slots = generate_time_slots()
    today_slots = generate_time_slots_from_now()
    
    print(f"⏰ الوقت الحالي: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 الأوقات المتاحة للجدولة: {len(time_slots)}")
    print(f"📅 الأوقات المتبقية لليوم: {len(today_slots)}")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
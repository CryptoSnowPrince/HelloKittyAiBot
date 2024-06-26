import aiogram
import asyncio
import config
import messages
import time
import urllib.request
import replicate
import os
from PIL import Image

os.environ['REPLICATE_API_TOKEN'] = config.REPLICATE_API_TOKEN
bot = aiogram.Bot(token=config.API_TOKEN,
                  parse_mode=aiogram.types.ParseMode.HTML)

loop = asyncio.get_event_loop()
dp = aiogram.Dispatcher(bot, loop=loop)
comps = {}

@dp.message_handler(commands=['help'])
async def help_message(message: aiogram.types.Message):
    await message.reply(messages.message['/help'])


@dp.message_handler(commands=['start'])
async def start_message(message: aiogram.types.Message):
    await message.reply(messages.message['/start'])


async def pending(message, username, origin_username):
    wait_t = int(time.time() - comps[username])
    wait_t = 40 - wait_t
    if wait_t > 0:
        countdown_m = await message.reply('@' + origin_username + ' You\'re in countdown mode please wait ' + str(wait_t) + ' seconds before using Prince again.')


@dp.message_handler(lambda message: (message.text not in config.commands and message.text.startswith("/prince ")))
async def handle_input(message: aiogram.types.Message):
    prompt = message.text.split("/prince ")[1]
    if prompt.strip() == "":
        return

    print(message['from']['id'], message['chat']['username'],
          message['from']['username'], message.text)
    username = message['from']['username']
    origin_username = username if username else "none"
    if not username:
        username = str(time.time)

    if username in comps.keys() and (time.time() - comps[username]) < 40:
        await pending(message, username, origin_username)
        return
    comps[username] = time.time()
    model = replicate.models.get("stability-ai/stable-diffusion")
    version = model.versions.get(
        "db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5bf")

    # https://replicate.com/stability-ai/stable-diffusion/versions/f178fa7a1ae43a9a9af01b833b9d2ecf97b1bcb0acfd2dc5dd04895e042863f1#input
    inputs = {
        'width': 768,
        'height': 768,
        'prompt_strength': 0.8,
        'num_outputs': 1,
        'num_inference_steps': 50,
        'guidance_scale': 7.5,
        'scheduler': "DPMSolverMultistep",
    }
    inputs['prompt'] = prompt
    wait_m = await message.reply(messages.message["/wait"])
    prediction = replicate.predictions.create(version=version, input=inputs)
    print("prediction thread")
    tm = 40
    output = []
    old_percent_m = ""
    while tm > 0:
        prediction.reload()
        print(prediction.status)
        if prediction.status == "failed":
            break
        print(prediction.logs)
        percent = 0
        if prediction.logs:
            percent = prediction.logs.split("\n")[-1].split("|")[0]

        percent_m = ""
        if percent:
            percent_m = percent
        print(prediction.status, origin_username, message.text, percent)
        if percent_m != old_percent_m:
            await wait_m.edit_text("Processing request from @" + origin_username + " | " + prompt + " | " + percent_m)
        old_percent_m = percent_m
        if prediction.status == 'succeeded':
            output = prediction.output
            break
        await asyncio.sleep(5)
        tm -= 5

    if len(output) == 0:
        await wait_m.edit_text("Try running it again, or try a different prompt")
        return
    generated_image_url = output[0]
    water_mark(generated_image_url, username)
    photo = open(f"images/{username}_watermarked.png", 'rb')
    await wait_m.delete()
    Telegram = "https://t.me/cryptosnowprince"
    Twitter = "https://t.me/cryptosnowprince"
    Website = "https://metabest.tech"
    BuyLink = "https://metabest.tech"
    caption = f"{prompt}\nimage generated by @{origin_username}\n\n <a href ='{Website}'>Website</a> | <a href ='{Telegram}'>Telegram</a> | <a href ='{Twitter}'>Twitter</a> | <a href ='{BuyLink}'>Buy $Prince</a>"
    await bot.send_photo(message.chat.id, photo, caption)
    photo.close()

def water_mark(image_url, username):
    urllib.request.urlretrieve(image_url, f"images/{username}.png")
    im = Image.open(f"images/{username}.png").convert("RGBA")
    water_mark = Image.open("watermark.png").convert("RGBA")
    alpha = water_mark.split()[-1]
    alpha = alpha.point(lambda p: int(float(p)/1.5))
    # print("\nalpha\n", alpha)
    water_mark.putalpha(alpha)
    water_mark_width, water_mark_height = water_mark.size
    width, height = im.size

    watermark_im = Image.new('RGBA', im.size, color=(0, 0, 0, 0))
    watermark_im.paste(
        water_mark, (width-water_mark_width, height-water_mark_height))

    watermark_im = Image.alpha_composite(im, watermark_im)

    watermark_im.save(f"images/{username}_watermarked.png")

if __name__ == "__main__":
    print("CryptoSnowPrinceAiBot Started...")

    aiogram.executor.start_polling(dp, skip_updates=True)

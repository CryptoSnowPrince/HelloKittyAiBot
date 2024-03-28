# Telegram bot

## ENV

```
Python3 version: python3.10.12
pip3 version: 22.0.2
```

```text
Make `myenv.py` file from `myenv.example.py` file.
```

## Install Packages

```
pip install -r requirements.txt
```

## dev mode

```
python3 bot.py
```

## product mode

```
pm2 start bot.py --name text2image-tg-bot --interpreter python3 --time
```
```
pm2 stop bot.py
```

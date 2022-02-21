
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import requests, urllib.parse, filetype, os, time, shutil, tldextract, asyncio, json, math
from PIL import Image
from plugins.config import *
import time
from plugins.main import Translation
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram import filters
from pyrogram import Client
from .database.add import add_user_to_database
from .functions.display_progress import humanbytes
from .functions.help_uploadbot import DownLoadFile
from .functions.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from .functions.ran_text import random_char
from .functions.forcesub import handle_force_subscribe

@Client.on_message(filters.private & filters.regex(pattern=".*https.*"))
async def echo(bot, update):
    await add_user_to_database(bot, update)
    logger.info(update.from_user)
    if Config.UPDATES_CHANNEL:
      fsub = await handle_force_subscribe(bot, update)
      if fsub == 400:
        return
    url = update.text
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    print(url)
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0]
            file_name = url_parts[1]
        elif len(url_parts) == 4:
            url = url_parts[0]
            file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
        if url is not None:
            url = url.strip()
        if file_name is not None:
            file_name = file_name.strip()
        # https://stackoverflow.com/a/761825/4723940
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(url)
        logger.info(file_name)
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]
    if Config.HTTP_PROXY != "":
        command_to_exec = [
        "yt-dlp",
        "--no-warnings",
        "--youtube-skip-dash-manifest",
        "--no-check-certificate",
        "-j",
        url,
    ]
    if "hotstar" in url:
        command_to_exec.append("--geo-bypass-country")
        command_to_exec.append("IN")
    #
    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(yt_dl_user_name)
    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(yt_dl_pass_word)

 
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    logger.info(e_response)
    t_response = stdout.decode().strip()
    # LOGGER.info(t_response)
    # https://github.com/rg3/youtube-dl/issues/2630#issuecomment-38635239
    if e_response:
        # logger.warn("Status : FAIL", exc.returncode, exc.output)
        error_message = e_response.replace(
            "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.",
            "",
        )
        return None, error_message, None
    if t_response:
        # logger.info(t_response)
        x_reponse = t_response
        response_json = []
        if "\n" in x_reponse:
            for yu_r in x_reponse.split("\n"):
                response_json.append(json.loads(yu_r))
        else:
            response_json.append(json.loads(x_reponse))
        # response_json = json.loads(x_reponse)
        save_ytdl_json_path = user_working_dir + "/" + str("ytdleech") + ".json"
        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)
        # logger.info(response_json)
        inline_keyboard = []
        #
        thumb_image = DEF_THUMB_NAIL_VID_S
        #
        # LOGGER.info(response_json)
        for current_r_json in response_json:
            #
            thumb_image = current_r_json.get("thumbnail", thumb_image)
            #
            duration = None
            if "duration" in current_r_json:
                duration = current_r_json["duration"]
            if "formats" in current_r_json:
                for formats in current_r_json["formats"]:
                    format_id = formats.get("format_id")
                    format_string = formats.get("format_note")
                    if format_string is None:
                        format_string = formats.get("format")
                    format_ext = formats.get("ext")
                    approx_file_size = ""
                    if "filesize" in formats:
                        approx_file_size = humanbytes(formats["filesize"])
                    dipslay_str_uon = (
                        " "
                        + format_string
                        + " ("
                        + format_ext.upper()
                        + ") "
                        + approx_file_size
                        + " "
                    )
                    cb_string_video = "{}|{}|{}".format("video", format_id, format_ext)
                    ikeyboard = []
                    if "drive.google.com" in url:
                        if format_id == "source":
                            ikeyboard = [
                                pyrogram.InlineKeyboardButton(
                                    dipslay_str_uon,
                                    callback_data=(cb_string_video).encode("UTF-8"),
                                )
                            ]
                    else:
                        if (
                            format_string is not None
                            and not "audio only" in format_string
                        ):
                            ikeyboard = [
                                pyrogram.InlineKeyboardButton(
                                    dipslay_str_uon,
                                    callback_data=(cb_string_video).encode("UTF-8"),
                                )
                            ]
                        else:
                            # special weird case :\
                            ikeyboard = [
                                pyrogram.InlineKeyboardButton(
                                    "SVideo [" + "] ( " + approx_file_size + " )",
                                    callback_data=(cb_string_video).encode("UTF-8"),
                                )
                            ]
                    inline_keyboard.append(ikeyboard)
                if duration is not None:
                    cb_string_64 = "{}|{}|{}".format("audio", "64k", "mp3")
                    cb_string_128 = "{}|{}|{}".format("audio", "128k", "mp3")
                    cb_string = "{}|{}|{}".format("audio", "320k", "mp3")
                    inline_keyboard.append(
                        [
                            pyrogram.InlineKeyboardButton(
                                "MP3 " + "(" + "64 kbps" + ")",
                                callback_data=cb_string_64.encode("UTF-8"),
                            ),
                            pyrogram.InlineKeyboardButton(
                                "MP3 " + "(" + "128 kbps" + ")",
                                callback_data=cb_string_128.encode("UTF-8"),
                            ),
                        ]
                    )
                    inline_keyboard.append(
                        [
                            pyrogram.InlineKeyboardButton(
                                "MP3 " + "(" + "320 kbps" + ")",
                                callback_data=cb_string.encode("UTF-8"),
                            )
                        ]
                    )
            else:
                format_id = current_r_json["format_id"]
                format_ext = current_r_json["ext"]
                cb_string_video = "{}|{}|{}".format("video", format_id, format_ext)
                inline_keyboard.append(
                    [
                        pyrogram.InlineKeyboardButton(
                            "SVideo", callback_data=(cb_string_video).encode("UTF-8")
                        )
                    ]
                )
            break
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await chk.delete(True)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION.format(""),
            reply_markup=reply_markup,
            parse_mode="html",
            reply_to_message_id=update.message_id
        )
            

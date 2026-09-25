import os
import asyncio
import yt_dlp
from yt_dlp.utils import UnsupportedError ,DownloadError
from time import time
def list_available_formats(url):
    
    ydl_opts = {
        "simulate": True, 
        "quiet": True,
         'remote_components': ['ejs:github'],
         "extract_flat": False,
         
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            format_options = []
            formats = info_dict.get('formats', [])
            title = info_dict.get("title")
            duration = info_dict.get("duration", 0)
            
            hours = duration // 3600
            minutes = (duration // 60) % 60
            seconds = duration % 60
            real_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            for f in formats:
                fmt_id = f.get("format_id", 'N/A')
                ext = f.get('ext', 'N/A')
                resolution = f.get('resolution', 'N/A')

                filesize = f.get('filesize') or f.get('filesize_approx')
                filesize_str = f"{filesize / (1024*1024):.2f} MB" if filesize else "Unknown"

                acodec= f.get("acodec")
                vcodec = f.get('vcodec')

            

                if vcodec == 'none' or not vcodec: 
                    note = "audio"
                else:
                    note = "video"


                format_options.append((fmt_id, ext, resolution, filesize_str, note))
                
            return format_options, title, real_duration

    except UnsupportedError:

        return "unsupported","unsupported url","00:00:00"
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return [], "Unknown Title", "00:00:00"

def _sync_download(url, chosen_format_id, note, bot, chat_id, message_id, loop):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, "Downloads")
        os.makedirs(output_path, exist_ok=True)

        # 1. Fetch the absolute metadata dictionary first
        with yt_dlp.YoutubeDL({"simulate": True, "quiet": True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            formats = info_dict.get('formats', [])

        has_audio = True  # Default to True just in case
        acodec = "unknown"  # Safe initialization to prevent variable execution bugs

        for f in formats:
            if str(f.get("format_id")) == str(chosen_format_id):
                acodec = f.get("acodec")
                
                # FIXED INDENTATION: These checks and the break must live inside the IF block
                if acodec == "none" or not acodec:
                    has_audio = False
                break  # Exit the loop safely since we found our format match

        if not has_audio:
            download_format = f"{chosen_format_id}+bestaudio/best"
        else:
            download_format = chosen_format_id

        ydl_opts = {
            'format': download_format,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'remote_components': ['ejs:github'],  # Wrapped inside clean list elements
            'quiet': True,
            'progress_hooks': [create_progress_hook(bot, chat_id, message_id, loop)],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            vcodec = info.get("vcodec")
        
            if vcodec == "none" or not vcodec:
                fileType = "audio"
            else:
                fileType = "video"

            if not os.path.exists(filename):
                filename = os.path.splitext(filename)[0] + ".mp4"
            
            return filename, fileType
        
    except DownloadError as e:
        if "time out" in str(e).lower() or "timeout" in str(e).lower():
            print(f"timeoutError: {e}")
            return "timeout", "None"
        return "error", "none"  # Fallback return for alternative download error signatures
        
    except Exception as e:
        print(f"an error occurred: {e}")
        return "error", "none"  # FIXED: Returns a clean tuple instead of NoneType to stop aiogram crashing

def create_progress_hook(bot, chat_id, message_id, loop):
    
    last_update_time = 0

    def hook(d):
        
        nonlocal last_update_time 
        
        if d['status'] == 'downloading':
            current_time = time()
            
            #THE THROTTLE CHECK: Only proceed if more than 2 seconds have passed [0_5.1]
            if current_time - last_update_time > 2.0:
                
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    percent = int((downloaded / total) * 100)
                    text = f"📥 Downloading video... {percent}% complete."
                    
                    # Push the edit command safely to the main thread loop
                    asyncio.run_coroutine_threadsafe(
                        bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id),
                        loop
                    )
                    
                    #LOCK IT: Update the timestamp to the current clock time
                    last_update_time = current_time
                    
    return hook
        
async def download(url, chosen_format_id, note, bot, chat_id, message_id, loop):
    return await asyncio.to_thread(_sync_download, url, chosen_format_id, note, bot, chat_id, message_id, loop)

import random
import requests

from typing import Optional
from urllib.parse import urlparse, parse_qs

from typing import Optional
from urllib.parse import urlparse, parse_qs

import concurrent.futures
from youtube_transcript_api import YouTubeTranscriptApi

def get_proxies(how_many=7):
    print('Getting proxies ...')
    user_agents = [
        # Google Chrome User Agents
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/537.36",
        
        # Mozilla Firefox User Agents
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) FxiOS/121.0 Mobile/15E148 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) FxiOS/121.0 Mobile/15E148 Safari/537.36",
        
        # Microsoft Edge User Agents
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 EdgA/120.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) EdgiOS/120.0.0.0 Mobile/15E148 Safari/537.36",
        
        # Apple Safari User Agents
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.1 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/537.36",
        
        # Opera User Agents
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/104.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/104.0.0.0",
        "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 OPR/104.0.0.0",
        
        # Bots and Crawlers
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; DuckDuckBot/1.1; +http://duckduckgo.com/duckduckbot)",
        "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
        "Mozilla/5.0 (compatible; Twitterbot/1.0)",
        "Mozilla/5.0 (compatible; LinkedInBot/1.0; +http://www.linkedin.com)"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(
            f"https://proxylist.geonode.com/api/proxy-list?limit={how_many}&page=1&sort_by=lastChecked&sort_type=desc",
            headers=headers,
            timeout=5  # Optional: set a timeout for the request itself
        )
        response = response.json()
        # print("Response:", response)
        
        ips = []
        if response and 'data' in response:
            for d in response["data"]:
                ips.append({
                    "ip": d['ip'],
                    "protocols": d['protocols']
                })
        return ips
    except Exception as ex:
        print(ex)
        return None

def get_proxies_with_timeout(attempts=3, timeout=3):
    """
    * problem: getting proxies does not always work.
    Attempts to get proxies using get_proxies(), retrying up to 'attempts' times,
    with each attempt timing out after 'timeout' seconds.
    """
    for attempt in range(attempts):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(get_proxies)
            try:
                proxies = future.result(timeout=timeout)
                if proxies:
                    print(f"Successfully fetched proxies on attempt {attempt + 1}.")
                    return proxies
            except concurrent.futures.TimeoutError:
                print(f"Timeout error when fetching proxies. Attempt {attempt + 1} of {attempts}.")
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
    print("Failed to fetch proxies after", attempts, "attempts.")
    return []

def extract_video_id(url: str) -> Optional[str]:
    """
        * Extract a YouTube video ID from a URL if valid, otherwise return None.
        
        * inspired from `_parse_video_id` function from langchain : https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/document_loaders/youtube.py#L116
        
        * pytube library does seems to extract id from url, but installing a library just to extract id from video seems overkill. reference. https://gist.github.com/ivansaul/ac2794ecbddec6c54f1c2e62cccfc175
    """

    ALLOWED_SCHEMES = {"http", "https"}
    ALLOWED_NETLOCS = {"www.youtube.com", "youtube.com", "youtu.be", "m.youtube.com"}
    
    # Prepend scheme if missing.
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_url = urlparse(url)
    
    if parsed_url.scheme not in ALLOWED_SCHEMES:
        return None
    
    if parsed_url.netloc not in ALLOWED_NETLOCS:
        return None
    
    path = parsed_url.path
    
    # For standard YouTube URLs like 'https://www.youtube.com/watch?v=VIDEO_ID'
    if parsed_url.netloc in {"www.youtube.com", "youtube.com", "m.youtube.com"} and path == "/watch":
        query = parsed_url.query
        parsed_query = parse_qs(query)
        if "v" in parsed_query:
            video_id = parsed_query["v"][0]
        else:
            return None
    # For youtu.be URLs
    elif parsed_url.netloc == "youtu.be":
        # Handle non-standard case: 'youtu.be/watch?v=VIDEO_ID'
        if path.startswith("/watch"):
            query = parsed_url.query
            parsed_query = parse_qs(query)
            if "v" in parsed_query:
                video_id = parsed_query["v"][0]
            else:
                return None
        else:
            # Typical shortened URL: 'https://youtu.be/VIDEO_ID'
            video_id = path.lstrip("/")
    else:
        # Fallback: use the last segment of the path
        video_id = path.lstrip("/").split("/")[-1]
        
    # Ensure the video ID is exactly 11 characters long.
    if len(video_id) != 11:
        return None
    
    return video_id

def is_youtube_url(url: str) -> bool:
    return (url.startswith('https://www.youtube.com') or
            url.startswith('https://www.m.youtube.com') or
            url.startswith('https://youtu.be') or
            url.startswith('https://m.youtube.com') or
            url.startswith('https://youtube.com'))


def get_transcript_with_timeout(video_id, proxies, timeout=3):
    """
    Attempts to get transcript with a timeout using a ThreadPoolExecutor.
    skip if it did not get subtitles within 3 seconds (the proxy may be blocked by youtube)
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(YouTubeTranscriptApi.get_transcript, video_id, proxies=proxies)
        try:
            transcript = future.result(timeout=timeout)
            return transcript
        except concurrent.futures.TimeoutError:
            print("Timeout error when fetching transcript.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

def get_subtitle(url):
    proxies = get_proxies_with_timeout(attempts=5, timeout=5)
    if not proxies:
        print('Could not get the proxies.')
        return ''
    # For now, the video id is hardcoded.
    # Optionally, you can add logic to extract the video id from the url.
    # video_id = 'SW14tOda_kI'
    video_id = extract_video_id(url)
    
    subtitles = None
    if video_id:
        for proxy in proxies:
            # Determine protocol for the proxy (prefer https over http)
            protocol = 'https' if any('https' in p.lower() for p in proxy['protocols']) else 'http'
            proxy_dict = {protocol: proxy['ip']}
            print(f"Trying proxy: {proxy_dict}")
            transcript = get_transcript_with_timeout(video_id, proxy_dict, timeout=5)
            if transcript:
                subtitles = transcript
                break
    
    if subtitles and type(subtitles)==list:
        # Extract Text only
        return '\n'.join([s['text'] for s in subtitles])
    
    return str(subtitles) if subtitles else ''


if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=v0gjI__RyCY&t=4824s"
    subtitles=get_subtitle('https://www.youtube.com/watch?v=v0gjI__RyCY&t=4824s')
import os
import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

BASE_URL = "https://ftp.ctgfun.com/"

def fetch_links(url):
    """FTP ডিরেক্টরি থেকে পুনরাবৃত্তিমূলকভাবে (Recursively) ফাইল স্ক্র্যাপ করার ফাংশন"""
    media_data = []
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return media_data
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href or href in ['../', './', '/']:
                continue
                
            full_url = urllib.parse.urljoin(url, href)
            
            # যদি সাব-ডিরেক্টরি হয় তবে ভিতরে গিয়ে আবার সার্চ করবে
            if href.endswith('/'):
                media_data.extend(fetch_links(full_url))
            elif href.lower().endswith('.mp4'):
                # ক্যাটাগরি এক্সট্র্যাক্ট করা (URL Path থেকে)
                parsed_path = urllib.parse.urlparse(full_url).path.split('/')
                category = parsed_path[1] if len(parsed_path) > 2 else "Uncategorized"
                
                filename = urllib.parse.unquote(os.path.basename(full_url))
                movie_name = re.sub(r'\.mp4$', '', filename, flags=re.IGNORECASE).replace('.', ' ').replace('_', ' ')
                
                media_data.append({
                    "title": movie_name.strip(),
                    "category": urllib.parse.unquote(category),
                    "download_url": full_url,
                    "image_path": f"images/{clean_filename(movie_name)}.jpg"
                })
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        
    return media_data

def clean_filename(name):
    """ফাইলনেমের অবৈধ ক্যারেক্টার অপসারণ"""
    return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")

def generate_movie_image(title, category, output_path):
    """মুভি নেম ও ক্যাটাগরি ব্যবহার করে প্রিমিয়াম অটোমেটিক ইমেজ/পোস্টার তৈরি"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # পোস্টার ইমেজ সাইজ
    width, height = 800, 450
    
    # গ্রেডিয়েন্ট ব্যাকগ্রাউন্ড তৈরি
    image = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(image)
    
    # ডেকোরেটিভ ডিজাইন এলিমেন্ট
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(56, 189, 248), width=3)
    draw.rectangle([(30, 30), (180, 70)], fill=(225, 29, 72))
    
    try:
        # ডিফল্ট ফন্ট লোড (অথবা পছন্দমতো .ttf ব্যবহার করতে পারেন)
        font_title = ImageFont.load_default()
        font_category = ImageFont.load_default()
    except Exception:
        font_title = font_category = None

    # ক্যাটাগরি ও টাইটেল ড্র করা
    draw.text((45, 42), category.upper(), fill=(255, 255, 255), font=font_category)
    
    # দীর্ঘ টাইটেল সামলানো
    wrapped_title = title[:45] + "..." if len(title) > 45 else title
    draw.text((50, 200), wrapped_title, fill=(241, 245, 249), font=font_title)
    draw.text((50, 380), "CTGFUN FTP MEDIA", fill=(148, 163, 184), font=font_category)

    image.save(output_path, "JPEG", quality=90)

def main():
    print("Scraping FTP server for MP4 files...")
    movies = fetch_links(BASE_URL)
    
    print(f"Total MP4 files found: {len(movies)}")
    
    # ইমেজ তৈরি ও ডেটা প্রসেসিং
    for movie in movies:
        generate_movie_image(movie["title"], movie["category"], movie["image_path"])
        
    # JSON ফাইলে সংরক্ষন
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)
        
    print("Scraping and image generation completed successfully!")

if __name__ == "__main__":
    main()

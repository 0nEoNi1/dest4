import asyncio
import aiohttp
from lxml import html
from urllib.parse import urlparse
import csv
from colorama import Fore, init
import time
import random
import os
import ujson
from collections import defaultdict
from aiohttp_retry import RetryClient, ExponentialRetry

# Initialize colorama for colored output
init(autoreset=True)

# DNS cache
dns_cache = {}

# Rate limiting
rate_limits = defaultdict(lambda: {'last_request': 0, 'delay': 1})

async def get_url_title(session, url, max_retries=3):
    domain = urlparse(url).netloc
    current_time = time.time()
    time_since_last_request = current_time - rate_limits[domain]['last_request']
    if time_since_last_request < rate_limits[domain]['delay']:
        await asyncio.sleep(rate_limits[domain]['delay'] - time_since_last_request)
    
    rate_limits[domain]['last_request'] = time.time()

    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                tree = html.fromstring(content)
                title = tree.findtext('.//title') or "No title found"
                return title.strip(), True
            else:
                return f"Error: HTTP {response.status}", False
    except Exception as e:
        return f"Error: {str(e)}", False

async def process_url(session, url, count, total):
    if not urlparse(url).scheme:
        url = 'http://' + url
    title, status = await get_url_title(session, url)
    return url, title, status, count, total

async def process_urls_chunk(session, urls, start_count, total):
    tasks = []
    for i, url in enumerate(urls):
        task = asyncio.create_task(process_url(session, url.strip(), start_count + i, total))
        tasks.append(task)
    return await asyncio.gather(*tasks)

async def process_urls_file(file_path, chunk_size=200):
    results = []
    temp_file_path = file_path + '.temp'
    removed_count = 0
    total_links = sum(1 for line in open(file_path) if line.strip())
    print(f"Total links in file: {total_links}")

    retry_options = ExponentialRetry(attempts=3)
    async with RetryClient(retry_options=retry_options) as session:
        connector = aiohttp.TCPConnector(ssl=False, limit=100, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector, json_serialize=ujson.dumps) as session:
            with open(file_path, 'r') as input_file, open(temp_file_path, 'w') as temp_file:
                chunk = []
                count = 0
                for line in input_file:
                    chunk.append(line)
                    if len(chunk) == chunk_size:
                        chunk_results = await process_urls_chunk(session, chunk, count + 1, total_links)
                        for result in chunk_results:
                            url, title, status, _, _ = result
                            results.append((url, title, status))
                            print_result(*result)
                            if status:
                                temp_file.write(f"{url}\n")
                            else:
                                removed_count += 1
                        count += len(chunk)
                        chunk = []

                if chunk:
                    chunk_results = await process_urls_chunk(session, chunk, count + 1, total_links)
                    for result in chunk_results:
                        url, title, status, _, _ = result
                        results.append((url, title, status))
                        print_result(*result)
                        if status:
                            temp_file.write(f"{url}\n")
                        else:
                            removed_count += 1

    # Replace the original file with the temporary file
    os.replace(temp_file_path, file_path)
    print(f"\nRemoved {removed_count} invalid URLs from the original file.")
    return results

def print_result(url, title, status, count, total):
    print(f"[{count}/{total}] URL: {url}")
    print(f"Title: {title}")
    if status:
        print(f"Status: {Fore.GREEN}True")
    else:
        print(f"Status: {Fore.RED}False")
    print("-" * 50)

def save_to_csv(results, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['URL', 'Title', 'Status'])
        for url, title, status in results:
            writer.writerow([url, title, status])

async def main():
    input_file = "D:/DEST/url.txt"
    output_file = "D:/DEST/url.csv"
    print("\nProcessing URLs:")
    results = await process_urls_file(input_file)
    save_to_csv(results, output_file)
    print(f"\nResults have been saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
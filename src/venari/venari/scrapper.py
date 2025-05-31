# # venari/src/venari/scrape_jobs.py
#
# import asyncio
# import httpx
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
#
#
# URL = "https://justjoin.it/job-offers/all-locations/python?remote=yes&from=1"
# BASE_URL = "https://justjoin.it"
#
#
# async def fetch_job_page():
#     async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
#         response = await client.get(URL)
#         response.raise_for_status()
#         return response.text
#
#
# # def parse_jobs(html: str):
# #     soup = BeautifulSoup(html, "html.parser")
# #     jobs = []
# #
# #     # As of now, JustJoin.it renders jobs dynamically with JavaScript
# #     # So plain HTML parsing won't find actual job listings unless they're SSR'd
# #     # But let's try printing the soup to verify what’s there
# #     print("Page title:", soup.title)
# #     # You can try finding divs or JSON-LD if available
# #     for script_tag in soup.find_all("script", type="application/ld+json"):
# #         print("Found JSON-LD:")
# #         print(script_tag.string[:500])  # show first part
# #         # Optionally: use `json.loads(script_tag.string)` to parse
# #
# #     return jobs
#
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
#
# BASE_URL = "https://justjoin.it"
#
# def parse_jobs(html: str):
#     soup = BeautifulSoup(html, "html.parser")
#     jobs = []
#
#     for offer in soup.select("a.offer-card"):
#         relative_url = offer.get("href")
#         full_url = urljoin(BASE_URL, relative_url)
#
#         title_tag = offer.select_one("h3")
#         title = title_tag.text.strip() if title_tag else "No title"
#
#         logo_tag = offer.select_one("img")
#         logo_url = logo_tag.get("src") if logo_tag else None
#
#         # Get full text from span (e.g., '29K – 36K PLN/month' or per hour equivalents)
#         # salary_tag = offer.select_one("span")
#         span_values = offer.select("span")
#         span_data = [x.get_text() for x in span_values]
#         # breakpoint()
#         # salary = salary_tag.get_text(strip=False) if salary_tag else "N/A"
#         min_s, max_s, unit, *_= span_data
#         jobs.append({
#             "title": title,
#             "url": full_url,
#             "logo": logo_url,
#             "salary": f"{min_s} - {max_s} {unit}",
#             # "company": org_name,
#             # "remote": remote
#         })
#
#     print(f"Found {len(jobs)} jobs:")
#     for job in jobs:
#         print(f"- [{job['salary']}] {job['title']} -> {job['url']}")
#         # {job['company']}[{job['remote']}]        ")
#     return jobs
#
#
#
# async def main():
#     html = await fetch_job_page()
#     parse_jobs(html)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

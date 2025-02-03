import json
import pickle
from playwright.sync_api import sync_playwright

def extract_blog_data(url: str) -> dict:
    """
    Extracts title, date, author, and content from a blog post using Playwright.

    Args:
        url: The URL of the blog post.

    Returns:
        A dictionary containing the extracted data, or None if an error occurs.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # with open('content.html','w') as f:
        #     f.write(page.content)
        try:
            page.goto(url, timeout=30000)

            title = page.locator('h1').first.text_content()  # Get the first h1
            # print(f'title:{title}')
            date = page.locator('.posted-on').text_content().replace("Posted ", "") # Clean the date
            # print(f'date:{date}')
            
            author_element = page.locator('.auth a').first
            author = author_element.text_content() if author_element.count() > 0 else None #Handle missing authors
            # print(f'author:{author}')
            content_paragraphs = page.locator('.tombstone-enable p')
            content = [p for p in content_paragraphs.all_inner_texts()] #List of paragraphs
            # print(f'content:{content}')
            data = {
                "title": title.strip() if title else None, #Strip whitespace
                "date": date.strip() if date else None,
                "author": author.strip() if author else None,
                "content": content
            }
            return data

        except Exception as e:
            print(f"Error fetching URL {url}: {e}")
            return None
        finally:
            browser.close()

if __name__ == "__main__":
    # url = "https://a16z.com/announcement/investing-in-lumos/"
    with open('links.txt', 'r') as f:
        links = [line.strip() for line in f]  # Use list comprehension and strip()
    
    blog_posts = []
    error_links = []
    
    for i, link in enumerate(links):
        blog_data = extract_blog_data(link)

        if blog_data:
            print(f"{i}/{len(links)} - {blog_data['title']}")
            
            blog_posts.append(blog_data)

            # # print(blog_data)
            # with open("a16z_lumos.pkl", "wb") as f:
            #     pickle.dump(blog_data, f)
            # with open("a16z_lumos.json", "w") as f:
            #     json.dump(blog_data, f)
            # print("Blog data saved to a16z_lumos.pkl")
        else:
            print("Failed to retrieve blog data.")
            error_links.append(link)
    # Save error links to a file
    with open('error_links.json','w') as f:
        json.dump(error_links, f)

    # Save all blog posts to a file    
    with open('blog_posts.json','w') as file:
        json.dump(blog_posts, file)
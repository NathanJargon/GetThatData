import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def clean_text(text: str) -> str:
    """Helper to clean extra spaces and lines from text."""
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Replace multiple empty lines with a double newline
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def scrape_url(url: str) -> dict:
    """
    Fetches the URL, extracts title, description, and cleans body text.
    Returns a dictionary of results.
    """
    # Ensure URL has a scheme
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': f"Failed to fetch URL: {str(e)}"
        }

    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get metadata
        title = soup.title.string.strip() if soup.title else ""
        if not title:
            # Fallback to h1 or empty
            h1 = soup.find('h1')
            title = h1.get_text().strip() if h1 else "Untitled Page"

        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc and meta_desc.get('content'):
            description = meta_desc.get('content').strip()

        # Remove boilerplate/noise elements
        noise_tags = [
            'script', 'style', 'noscript', 'iframe', 'svg', 'canvas', 
            'nav', 'footer', 'header', 'aside', 'form', 'button', 'input'
        ]
        for tag in soup(noise_tags):
            tag.decompose()

        # Try to find main content areas first to exclude sidebar links and headers
        main_content = None
        for selector in ['article', 'main', '[role="main"]', '#content', '.content', '.main']:
            found = soup.select(selector)
            if found:
                # Use the largest one found
                found.sort(key=lambda x: len(x.get_text()), reverse=True)
                main_content = found[0]
                break
        
        # Fall back to body if no main selector matches
        if not main_content:
            main_content = soup.body if soup.body else soup

        # Reconstruct structured text (preserving headings, list structures, and paragraph separation)
        lines = []
        
        # Helper to process child nodes recursively
        def process_element(element):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Heading formatting
                level = int(element.name[1])
                lines.append(f"\n\n{'#' * level} {element.get_text().strip()}\n")
            elif element.name == 'p':
                lines.append(f"\n{element.get_text().strip()}\n")
            elif element.name == 'li':
                lines.append(f"\n- {element.get_text().strip()}")
            elif element.name == 'pre' or element.name == 'code':
                lines.append(f"\n```\n{element.get_text().strip()}\n```\n")
            elif element.name == 'table':
                # Convert tables to simplified text representation
                table_lines = []
                for row in element.find_all('tr'):
                    cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                    table_lines.append(" | ".join(cells))
                lines.append("\n" + "\n".join(table_lines) + "\n")
            elif hasattr(element, 'children') and element.name not in ['script', 'style']:
                for child in element.children:
                    if child.name:
                        process_element(child)
                    elif child.strip():
                        # Just text node
                        lines.append(child.strip())

        process_element(main_content)

        # Merge, clean spacing, and measure
        full_text = " ".join(lines)
        cleaned_content = clean_text(full_text)

        # Let's count words roughly
        words = cleaned_content.split()
        word_count = len(words)

        return {
            'success': True,
            'url': url,
            'title': title,
            'description': description,
            'content': cleaned_content,
            'word_count': word_count
        }

    except Exception as e:
        return {
            'success': False,
            'url': url,
            'error': f"Failed to parse content: {str(e)}"
        }

if __name__ == '__main__':
    # Quick test
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else 'https://example.com'
    print(f"Scraping: {test_url}...")
    res = scrape_url(test_url)
    if res['success']:
        print(f"Title: {res['title']}")
        print(f"Description: {res['description']}")
        print(f"Word count: {res['word_count']}")
        print("\nFirst 300 chars of content:")
        print(res['content'][:300] + "...")
    else:
        print(f"Error: {res['error']}")

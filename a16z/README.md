# a16z investment decisioin posts

## step-1: get Investment links from `https://a16z.com/news-content/`
```
const links = Array.from(document.querySelectorAll('a'))
                  .map(a => a.getAttribute('href'))
                  .filter(href => href?.startsWith('/announcement/'))
                  .map(href => new URL(href, window.location.origin).href);

// Convert links to text format
const blob = new Blob([links.join("\n")], { type: "text/plain" });

// Create a temporary link element
const a = document.createElement("a");
a.href = URL.createObjectURL(blob);
a.download = "links.txt";

// Append to DOM, trigger download, then remove
document.body.appendChild(a);
a.click();
document.body.removeChild(a);

console.log("File downloaded: links.txt");
```


# step-2: crawl data from those links
* please refer to [./crawl_content.py](./crawl_content.py)
* it seems to be dynamic site, using playwright


# Step-3: use the data as knowledge base for our chatbot (to give it personality)
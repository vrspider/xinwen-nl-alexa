import type { VercelRequest, VercelResponse } from '@vercel/node';
import fs from 'fs';
import path from 'path';

interface SiteConfig {
    id: string;
    name: string;
    url: string;
    outputDir: string;
    publicDir: string;
    rss: {
        title: string;
        description: string;
        link: string;
    };
}

interface Config {
    sites: SiteConfig[];
}

function loadConfig(): Config {
    const configPath = path.join(process.cwd(), "config/sites.json");
    const content = fs.readFileSync(configPath, "utf-8");
    return JSON.parse(content);
}

export default function handler(request: VercelRequest, response: VercelResponse) {
    let config: Config;
    try {
        config = loadConfig();
    } catch (e) {
        response.status(500).send("Configuration error");
        return;
    }

    const museumLink = `<a class="link" href="/exhibitions/museum_weekly.md">博物馆周报</a>`;
    const museumPodcastLink = `<a class="link" href="/exhibitions/rss">博物馆周报 Podcast</a>`;
    const concertLink = `<a class="link" href="/concerts/concert_weekly.md">演出周报</a>`;
    const concertPodcastLink = `<a class="link" href="/concerts/rss">演出周报 Podcast</a>`;

const sitesHtml = config.sites.map(site => 
        `<a class="link" href="/${site.id}/rss">${site.name} RSS</a>`
    ).join("\n");

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日荷兰</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 600px;
      margin: 50px auto;
      padding: 20px;
      background: #f5f5f5;
    }
    h1 { color: #333; }
    .link {
      display: block;
      padding: 15px;
      margin: 10px 0;
      background: white;
      border-radius: 8px;
      text-decoration: none;
      color: #0066cc;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .link:hover { background: #f0f0f0; }
    .link-row { display: flex; gap: 10px; }
    .link-row .link { flex: 1; }
  </style>
</head>
<body>
  <h1>每日荷兰</h1>
  <h2>新闻</h2>
  ${sitesHtml}
  <h2>博物馆</h2>
  <div class="link-row">
    ${museumLink}
    ${museumPodcastLink}
  </div>
  <h2>演出</h2>
  <div class="link-row">
    ${concertLink}
    ${concertPodcastLink}
  </div>
</body>
</html>
`;
    response.setHeader('Content-Type', 'text/html');
    response.send(html);
}

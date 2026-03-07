import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(request: VercelRequest, response: VercelResponse) {
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
  </style>
</head>
<body>
  <h1>每日荷兰</h1>
  <a class="link" href="/dutchnews/rss">Dutch News RSS</a>
</body>
</html>
`;
  response.setHeader('Content-Type', 'text/html');
  response.send(html);
}

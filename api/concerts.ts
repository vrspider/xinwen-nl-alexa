import type { VercelRequest, VercelResponse } from '@vercel/node';
import fs from 'fs';
import path from 'path';

export default function handler(request: VercelRequest, response: VercelResponse) {
    const filePath = path.join(process.cwd(), "public/concerts/concert_weekly.md");
    
    try {
        const content = fs.readFileSync(filePath, "utf-8");
        
        // Simple markdown to HTML conversion
        let html = content
            // Headers
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        const fullHtml = `<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>荷兰演出周报</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 20px;
      background: #fafafa;
      line-height: 1.8;
      color: #333;
    }
    h1 { color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
    h2 { color: #2a2a2a; margin-top: 30px; }
    h3 { color: #444; }
    p { margin: 10px 0; }
    strong { color: #0066cc; }
    hr { border: none; border-top: 1px solid #ddd; margin: 30px 0; }
  </style>
</head>
<body>
  <p>${html}</p>
</body>
</html>`;
        
        response.setHeader('Content-Type', 'text/html; charset=UTF-8');
        response.send(fullHtml);
    } catch (e) {
        response.status(404).send("File not found");
    }
}

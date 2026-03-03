import type { VercelRequest, VercelResponse } from "vercel";
import fs from "fs";
import path from "path";

// helper builds an RSS string from a list of episodes
function buildRss(items: Array<{
    title: string;
    description: string;
    url: string;
    pubDate: string;
    guid: string;
}>) {
    const now = new Date().toUTCString();
    const channelTitle = "Xinwen 新闻";
    const channelLink = "https://xinwen.nl/";
    const channelDescription = "荷兰新闻每日播报";

    let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
    xml += `<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n`;
    xml += `<channel>\n`;
    xml += `<title>${channelTitle}</title>\n`;
    xml += `<link>${channelLink}</link>\n`;
    xml += `<description>${channelDescription}</description>\n`;
    xml += `<language>zh-cn</language>\n`;
    xml += `<pubDate>${now}</pubDate>\n`;

    items.forEach(item => {
        xml += `<item>\n`;
        xml += `<title><![CDATA[${item.title}]]></title>\n`;
        xml += `<description><![CDATA[${item.description}]]></description>\n`;
        xml += `<enclosure url="${item.url}" type="audio/mpeg" length="0"/>\n`;
        xml += `<guid>${item.guid}</guid>\n`;
        xml += `<pubDate>${item.pubDate}</pubDate>\n`;
        xml += `</item>\n`;
    });

    xml += `</channel>\n`;
    xml += `</rss>`;
    return xml;
}

export default function handler(
    req: VercelRequest,
    res: VercelResponse
) {
    // scan the output directory for mp3 files
    const outputDir = path.join(process.cwd(), "output");
    let items: Array<any> = [];
    try {
        const files = fs.readdirSync(outputDir);
        files
            .filter(f => f.toLowerCase().endsWith(".mp3"))
            .sort()
            .forEach(f => {
                const datePart = path.basename(f, ".mp3");
                const pub = new Date(datePart).toUTCString();
                const url = `https://xinwen-alexa.vercel.app/audio/${f}`;
                items.push({
                    title: `Xinwen 新闻 ${datePart}`,
                    description: `每天的新闻摘要，生成于 ${datePart}`,
                    url,
                    pubDate: pub,
                    guid: url
                });
            });
    } catch (e) {
        // if directory missing or empty, still respond with empty channel
    }

    const rss = buildRss(items);
    res.setHeader("Content-Type", "application/rss+xml; charset=UTF-8");
    res.status(200).send(rss);
}

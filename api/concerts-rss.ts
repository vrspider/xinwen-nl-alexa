import type { VercelRequest, VercelResponse } from "@vercel/node";
import fs from "fs";
import path from "path";

function buildRss(
    items: Array<{
        title: string;
        description: string;
        url: string;
        pubDate: string;
        guid: string;
        length?: number;
    }>
) {
    const now = new Date().toUTCString();
    const channelTitle = "演出周报 Podcast";
    const channelLink = "https://xinwen-alexa.vercel.app/concerts/concert_weekly.md";
    const channelDescription = "荷兰演出活动周报语音版，每周更新";

    let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
    xml += `<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n`;
    xml += `<channel>\n`;
    xml += `<title>${channelTitle}</title>\n`;
    xml += `<link>${channelLink}</link>\n`;
    xml += `<description>${channelDescription}</description>\n`;
    xml += `<language>zh-cn</language>\n`;
    xml += `<pubDate>${now}</pubDate>\n`;
    xml += `<itunes:author>XiaXia</itunes:author>\n`;
    xml += `<itunes:owner>\n`;
    xml += `<itunes:name>XiaXia</itunes:name>\n`;
    xml += `<itunes:email>podcast@example.com</itunes:email>\n`;
    xml += `</itunes:owner>\n`;
    xml += `<itunes:summary><![CDATA[${channelDescription}]]></itunes:summary>\n`;
    xml += `<itunes:explicit>no</itunes:explicit>\n`;
    xml += `<itunes:category text="Music"/>\n`;
    xml += `<itunes:image href="https://xinwen-alexa.vercel.app/logo.jpg"/>\n`;

    items.forEach(item => {
        xml += `<item>\n`;
        xml += `<title><![CDATA[${item.title}]]></title>\n`;
        xml += `<itunes:subtitle><![CDATA[${item.description}]]></itunes:subtitle>\n`;
        xml += `<itunes:summary><![CDATA[${item.description}]]></itunes:summary>\n`;
        xml += `<description><![CDATA[${item.description}]]></description>\n`;
        const lengthAttr = item.length ? item.length.toString() : "0";
        xml += `<enclosure url="${item.url}" type="audio/mpeg" length="${lengthAttr}"/>\n`;
        xml += `<link>${item.url}</link>\n`;
        xml += `<guid>${item.guid}</guid>\n`;
        xml += `<pubDate>${item.pubDate}</pubDate>\n`;
        xml += `<itunes:explicit>no</itunes:explicit>\n`;
        xml += `</item>\n`;
    });

    xml += `</channel>\n`;
    xml += `</rss>`;
    return xml;
}

export default function handler(req: VercelRequest, res: VercelResponse) {
    // 扫描 concerts 音频目录
    const audioDir = path.join(process.cwd(), "public", "audio", "concerts");
    let items: Array<any> = [];
    
    try {
        if (fs.existsSync(audioDir)) {
            const files = fs.readdirSync(audioDir);
            files
                .filter(f => f.toLowerCase().endsWith(".mp3"))
                .sort()
                .reverse()
                .forEach(f => {
                    // 文件名格式: concert-weekly-report-2026-3-8.mp3
                    const baseName = path.basename(f, ".mp3");
                    // 提取日期部分
                    const datePart = baseName.replace("concert-weekly-report-", "");
                    const pub = new Date(datePart).toUTCString();
                    const url = `https://xinwen-alexa.vercel.app/audio/concerts/${f}`;
                    let size = 0;
                    try {
                        const stat = fs.statSync(path.join(audioDir, f));
                        size = stat.size;
                    } catch {}
                    items.push({
                        title: `演出周报 ${datePart}`,
                        description: `荷兰演出活动周报，生成于 ${datePart}`,
                        url,
                        pubDate: pub,
                        guid: url,
                        length: size
                    });
                });
        }
    } catch (e) {
        // directory missing or empty
    }

    const rss = buildRss(items);
    
    res.setHeader("Content-Type", "application/rss+xml; charset=UTF-8");
    res.status(200).send(rss);
}

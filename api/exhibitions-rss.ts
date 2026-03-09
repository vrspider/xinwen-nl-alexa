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
    const channelTitle = "博物馆周报 Podcast";
    const channelLink = "https://xinwen-alexa.vercel.app/exhibitions/museum_weekly.md";
    const channelDescription = "荷兰博物馆展览周报语音版，每周更新";

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
    xml += `<itunes:category text="Arts"/>\n`;
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
    // 扫描 exhibitions 音频目录
    const audioDir = path.join(process.cwd(), "public", "audio", "exhibitions");
    let items: Array<any> = [];
    
    try {
        if (fs.existsSync(audioDir)) {
            const files = fs.readdirSync(audioDir);
            files
                .filter(f => f.toLowerCase().endsWith(".mp3"))
                .sort()
                .reverse()
                .forEach(f => {
                    // 文件名格式: museum-weekly-report-2026-3-8.mp3
                    const baseName = path.basename(f, ".mp3");
                    // 提取日期部分: museum-weekly-report-2026-3-8 -> 2026-3-8
                    const datePart = baseName.replace("museum-weekly-report-", "");
                    const pub = new Date(datePart).toUTCString();
                    const url = `https://xinwen-alexa.vercel.app/audio/exhibitions/${f}`;
                    let size = 0;
                    try {
                        const stat = fs.statSync(path.join(audioDir, f));
                        size = stat.size;
                    } catch {}
                    items.push({
                        title: `博物馆周报 ${datePart}`,
                        description: `荷兰博物馆展览周报，生成于 ${datePart}`,
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

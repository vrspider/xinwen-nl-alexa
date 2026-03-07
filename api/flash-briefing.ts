import type { VercelRequest, VercelResponse } from "vercel";
import fs from "fs";
import path from "path";

// 站点配置
interface SiteConfig {
    id: string;
    name: string;
    url: string;
    selectors: {
        articles: string;
        title: string;
        content: string;
        updateTime: string;
    };
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
    const configPath = path.join(process.cwd(), "sites.json");
    const content = fs.readFileSync(configPath, "utf-8");
    return JSON.parse(content);
}

// helper builds an RSS string from a list of episodes
function buildRss(
    items: Array<{
        title: string;
        description: string;
        url: string;
        pubDate: string;
        guid: string;
        length?: number;
    }>,
    channelTitle: string,
    channelLink: string,
    channelDescription: string,
    siteId: string
) {
    const now = new Date().toUTCString();

    let xml = `<?xml version="1.0" encoding="UTF-8"?>\n`;
    xml += `<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n`;
    xml += `<channel>\n`;
    xml += `<title>${channelTitle}</title>\n`;
    xml += `<link>${channelLink}</link>\n`;
    xml += `<description>${channelDescription}</description>\n`;
    xml += `<language>zh-cn</language>\n`;
    xml += `<pubDate>${now}</pubDate>\n`;
    xml += `<itunes:author>Xinwen</itunes:author>\n`;
    xml += `<itunes:owner>\n`;
    xml += `<itunes:name>Xinwen</itunes:name>\n`;
    xml += `<itunes:email>podcast@example.com</itunes:email>\n`;
    xml += `</itunes:owner>\n`;
    xml += `<itunes:summary><![CDATA[${channelDescription}]]></itunes:summary>\n`;
    xml += `<itunes:explicit>no</itunes:explicit>\n`;
    xml += `<itunes:category text="News"/>\n`;
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

function getSiteFromPath(reqPath: string, config: Config): SiteConfig | null {
    // 路径格式: /dutchnews/rss 或 /{siteId}/rss
    const match = reqPath.match(/^\/([^/]+)\/rss$/);
    if (!match) return null;
    
    const siteId = match[1];
    return config.sites.find(s => s.id === siteId) || null;
}

export default function handler(req: VercelRequest, res: VercelResponse) {
    const reqPath = req.url || "";
    
    // 获取站点配置
    let config: Config;
    try {
        config = loadConfig();
    } catch (e) {
        res.status(500).send("Configuration error");
        return;
    }
    
    // 查找对应的站点
    const site = getSiteFromPath(reqPath, config);
    
    if (!site) {
        res.status(404).send("Site not found");
        return;
    }
    
    // 扫描对应站点的音频目录
    const audioDir = path.join(process.cwd(), "public", "audio", site.publicDir);
    let items: Array<any> = [];
    
    try {
        if (fs.existsSync(audioDir)) {
            const files = fs.readdirSync(audioDir);
            files
                .filter(f => f.toLowerCase().endsWith(".mp3"))
                .sort()
                .reverse()
                .forEach(f => {
                    const datePart = path.basename(f, ".mp3");
                    const pub = new Date(datePart).toUTCString();
                    const url = `https://xinwen-alexa.vercel.app/audio/${site.publicDir}/${f}`;
                    let size = 0;
                    try {
                        const stat = fs.statSync(path.join(audioDir, f));
                        size = stat.size;
                    } catch {}
                    items.push({
                        title: `${site.name} ${datePart}`,
                        description: `每天的新闻摘要，生成于 ${datePart}`,
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

    const rss = buildRss(
        items,
        site.rss.title,
        site.rss.link,
        site.rss.description,
        site.id
    );
    
    res.setHeader("Content-Type", "application/rss+xml; charset=UTF-8");
    res.status(200).send(rss);
}

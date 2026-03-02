import type { VercelRequest, VercelResponse } from "vercel";

export default function handler(
    req: VercelRequest,
    res: VercelResponse
) {
    res.setHeader("Content-Type", "application/json");

    res.status(200).json([
        {
            uid: "xinwen-2026-01-28",
            updateDate: new Date().toISOString(),
            titleText: "Xinwen 今日新闻",
            mainText: "这里是 Xinwen.nl 今天的主要新闻摘要。",
            streamUrl: "https://xinwen-alexa.vercel.app/audio/today.mp3",
            redirectionUrl: "https://xinwen.nl/"
        }
    ]);
}

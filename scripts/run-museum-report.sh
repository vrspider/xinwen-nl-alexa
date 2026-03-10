#!/bin/bash
cd /Users/yuankunma/DEV/Tools/xinwen-nl-alexa
source venv/bin/activate
python src/local-report.py groq --voice zh-CN-YunxiNeural
vercel --prod

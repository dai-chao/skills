---
name: media-content-creation
description: "Create and process media content: GIF search, YouTube transcripts, audio analysis (Songsee), music generation (HeartMuLa, AudioCraft), songwriting, blog monitoring, OCR, PDF editing, and PowerPoint creation."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Media, Content Creation, GIF, YouTube, Audio, Music, OCR, PDF, PowerPoint, Blog Monitoring]
    related_skills: [creative-visual-generation]
---

# Media Content Creation

## When to Use This Skill

Trigger when the user wants to:
- Search for GIFs or other media
- Extract YouTube transcripts and create content from them
- Analyze audio (spectrograms, features)
- Generate music with AI
- Write songs and create AI music prompts
- Monitor blogs and RSS feeds
- Extract text from images/PDFs (OCR)
- Edit or generate PDFs
- Create PowerPoint presentations

## Section 1: GIF Search

Search and download GIFs from Tenor.
```bash
# Search GIFs via Tenor API
curl "https://g.tenor.com/v1/search?q=hello&key=$TENOR_API_KEY&limit=10"
```

See [references/gif-search.md](references/gif-search.md) for full details.

## Section 2: YouTube Content

Extract transcripts, summarize, create threads and blogs.
```bash
# Download transcript
yt-dlp --write-auto-sub --sub-langs en --skip-download "VIDEO_URL"
```

See [references/youtube-content.md](references/youtube-content.md) for full details.

## Section 3: Audio Analysis with Songsee

Audio spectrograms and features (mel, chroma, MFCC).
```bash
pip install songsee
songsee analyze input.wav --output report.html
```

See [references/songsee.md](references/songsee.md) for full details.

## Section 4: Music Generation

### HeartMuLa
Open-source music generation setup.
```bash
git clone https://github.com/heartmula/heartmula.git
cd heartmula
pip install -r requirements.txt
```

See [references/heartmula.md](references/heartmula.md) for full details.

### Songwriting & AI Music
Craft songs and generate Suno AI music prompts.
```markdown
# Song structure
[Verse 1]
...
[Chorus]
...
```

See [references/songwriting-and-ai-music.md](references/songwriting-and-ai-music.md) for full details.

### Third-Party Music APIs (e.g., 云五音乐)
When the user provides a private/internal API documentation URL (e.g., Apifox, Postman, internal docs) that you cannot access directly:

1. **Do not block on the URL** — immediately ask the user for:
   - A screenshot of the API docs
   - Or the full request/response text copied from the docs
   - Or the endpoint URL, method, headers, request body schema, and auth method
2. **Do not fabricate parameters** — wait for real docs before writing the integration code.
3. Once docs are provided, write a clean client module (Python or Node.js) with typed request/response models and error handling.

See [references/third-party-music-api-integration.md](references/third-party-music-api-integration.md) for a working example and template.

## Section 5: Blog Monitoring

Monitor blogs and RSS/Atom feeds.
```bash
pip install blogwatcher
blogwatcher add "https://example.com/feed.xml"
blogwatcher check
```

See [references/blogwatcher.md](references/blogwatcher.md) for full details.

## Section 6: OCR & Documents

Extract text from PDFs and scanned documents.
```bash
pip install pytesseract pdf2image
python -c "import pytesseract; print(pytesseract.image_to_string('scan.png'))"
```

See [references/ocr-and-documents.md](references/ocr-and-documents.md) for full details.

## Section 7: PDF Tools

### Nano PDF
Edit PDF text/typos/titles via natural language prompts.
```bash
pip install nano-pdf
nano-pdf edit "fix typo on page 3" input.pdf output.pdf
```

See [references/nano-pdf.md](references/nano-pdf.md) for full details.

### Chinese PDF Generation
Generate professional PDFs with Chinese text.
```python
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
```

See [references/chinese-pdf-generation.md](references/chinese-pdf-generation.md) for full details.

## Section 8: PowerPoint

Create, read, edit .pptx decks.
```python
from pptx import Presentation
prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[0])
prs.save('presentation.pptx')
```

See [references/powerpoint.md](references/powerpoint.md) for full details.

## Common Pitfalls

1. **GIF API limits**: Tenor has rate limits; cache results
2. **YouTube captions**: Auto-generated captions may have errors
3. **Audio analysis**: Use appropriate sample rates (44.1kHz for music)
4. **Music generation VRAM**: Large models need significant GPU memory
5. **OCR accuracy**: Low-quality scans need preprocessing (denoise, deskew)
6. **PDF editing**: Nano-pdf works best on text-based PDFs, not scanned images
7. **PowerPoint compatibility**: Test on target PowerPoint version
8. **Private API docs**: When a user shares an Apifox/internal API URL you cannot access, immediately ask for a screenshot or copy-paste of the endpoint details. Never fabricate parameters.

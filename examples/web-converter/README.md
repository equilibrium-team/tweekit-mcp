# Claude File Format Enabler

**Overcome Claude's file type limitations** - Convert 450+ unsupported file formats into Claude-compatible formats (PDF, PNG, JPEG, WebP).

## The Problem

Claude and other AI tools have built-in file type restrictions. They reject legacy and specialized formats like:

- Legacy Microsoft Office: DOC, XLS, PPT
- Adobe files: PSD, AI, INDD
- CAD files: DWG, DXF
- OpenDocument: ODT, ODS
- And 400+ other formats

This creates frustrating workflow bottlenecks where you have valuable content but Claude simply won't accept the file.

## The Solution

This web-based converter transforms **any file format** into Claude-compatible formats so you can analyze, extract, and work with content that would otherwise be rejected.

## Quick Start

### Option 1: Launch Script

```bash
./scripts/launch-converter.sh
```

### Option 2: Manual Launch

```bash
cd examples/web-converter
python3 -m http.server 8080
# Open http://localhost:8080
```

### Option 3: Direct File Access

Simply open `index.html` directly in your browser.

## How to Use

1. **Open the converter** in your browser
2. **Enter API credentials** - Get free credentials at [tweekit.io](https://www.tweekit.io) (10,000 free API calls)
3. **Upload any file** - DOCX, XLSX, PSD, DWG, AI, etc.
4. **Select output format**:
   - **PDF** - For documents and multi-page files
   - **PNG** - For high-quality images
   - **JPEG** - For photos and compressed images
   - **WebP** - For modern web-optimized images
5. **Download** the converted file
6. **Upload to Claude** - Now Claude can read it!

## Common Use Cases

| Input Format | Output Format | Use Case |
|--------------|---------------|----------|
| DOC (legacy) | PDF | Analyze Word documents in Claude |
| XLS (legacy) | PNG | Convert spreadsheets to images |
| PPT (legacy) | PDF | Extract content from presentations |
| PSD, AI | PNG | Work with design files |
| DWG, DXF | PDF | Review CAD drawings |
| ODT, ODS | PDF | Convert OpenDocument files |

## Features

- ✅ **450+ file formats** supported
- ✅ **No installation required** - runs in browser
- ✅ **Privacy focused** - credentials stored locally
- ✅ **Fast conversion** - powered by TweekIT API
- ✅ **Claude-optimized** - outputs only Claude-compatible formats

## Why This Matters

**Before**: Upload legacy DOC file → Claude rejects it → Manual conversion → Re-upload → Frustration

**After**: Upload DOC file → Convert with tool → Upload to Claude → Success!

## Technical Details

### Supported Input Formats (450+)

- **Documents**: DOC, DOCX, PDF, ODT, RTF, TXT, PAGES
- **Spreadsheets**: XLS, XLSX, ODS, CSV
- **Presentations**: PPT, PPTX, ODP, KEY
- **Images**: PNG, JPG, TIFF, PSD, AI, EPS, SVG, WebP
- **Camera RAW**: CR2, NEF, ARW, DNG, and 40+ more
- **CAD**: DWG, DXF, SKP
- **And many more...**

Full list: [https://tweekit.io/supported-files](https://www.tweekit.io/supported-files)

### Supported Output Formats (Claude-Compatible)

- **PDF** - Best for documents, presentations, multi-page files
- **PNG** - Best for screenshots, diagrams, high-quality images
- **JPEG** - Best for photos
- **WebP** - Best for web-optimized images

## API Credentials

### Getting Your Free API Key

1. Visit [tweekit.io](https://www.tweekit.io)
2. Sign up for a free account
3. Navigate to **Manage Account**
4. Copy your **API Key** and **API Secret**
5. Paste them into the converter

### Security

- Credentials are stored in your browser's localStorage (never sent to our servers)
- Files are processed server-side and immediately deleted after conversion
- No persistent storage of your files or credentials

## Troubleshooting

### Conversion Failed

- **Check credentials**: Make sure API Key and Secret are correct
- **Verify file**: Ensure the input file isn't corrupted
- **Try different format**: Some formats may work better as PNG vs PDF

### File Too Large

- Maximum file size: 100MB
- For larger files, consider splitting or compressing first

### Format Not Supported

If you encounter an unsupported format, contact support@tweekit.io

## Integration with Claude Desktop

For seamless integration, install the TweekIT MCP server in Claude Desktop:

```json
{
  "mcpServers": {
    "tweekit": {
      "transport": { "type": "http", "url": "https://mcp.tweekit.io/mcp" }
    }
  }
}
```

Then ask Claude to convert files directly without using this web tool.

## Support

- **Documentation**: [Main README](../../README.md#solving-claudes-file-type-limitations)
- **Email**: tweekitsupport@equilibrium.com
- **Website**: https://www.tweekit.io

## License

See main repository LICENSE file.

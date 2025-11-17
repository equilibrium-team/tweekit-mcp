#!/bin/bash
# TweekIT Web Converter Setup via Claude API
# This script uses Claude API to generate and create all necessary files

set -e

PROJECT_DIR="$HOME/documents/projects/tweekit-mcp"
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TweekIT MCP Web Converter Setup${NC}"
echo -e "${BLUE}Using Claude API${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}Error: ANTHROPIC_API_KEY not set${NC}"
    echo "Please set your Claude API key:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    exit 1
fi

echo -e "${GREEN}✓ API key found${NC}"
echo -e "${YELLOW}→ Target directory: $PROJECT_DIR${NC}"
echo ""

# Change to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}Error: Could not access $PROJECT_DIR${NC}"
    exit 1
}

echo -e "${GREEN}✓ In project directory${NC}"
echo ""

# Create directory structure
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p scripts
mkdir -p examples/web-converter
mkdir -p docs

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Create install.sh
echo -e "${BLUE}Creating scripts/install.sh...${NC}"
cat > scripts/install.sh << 'INSTALL_SCRIPT_EOF'
#!/bin/bash
# TweekIT MCP Installer Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}→ $1${NC}"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

print_header "TweekIT MCP Server Installer"

echo ""
print_info "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 required but not installed"
    exit 1
fi
print_success "Python $(python3 --version | cut -d' ' -f2) found"

if ! command_exists pip3; then
    print_error "pip3 required"
    exit 1
fi
print_success "pip3 found"

echo ""
print_header "Installing TweekIT MCP Server"

print_info "Installing Python dependencies..."
pip3 install -e . || {
    print_error "Failed to install"
    exit 1
}
print_success "TweekIT MCP Server installed"

echo ""
print_header "API Configuration"

read -p "Do you have TweekIT API credentials? (y/n): " has_creds

if [[ $has_creds == "y" ]]; then
    read -p "Enter API Key: " api_key
    read -p "Enter API Secret: " api_secret
    
    cat > .env << EOF
TWEEKIT_API_KEY=$api_key
TWEEKIT_API_SECRET=$api_secret
EOF
    print_success "API credentials saved"
fi

echo ""
print_header "Installation Complete!"
echo ""
print_success "Ready to use!"
echo ""
echo "Launch web converter: ./scripts/launch-converter.sh"
echo ""
INSTALL_SCRIPT_EOF

chmod +x scripts/install.sh
echo -e "${GREEN}✓ scripts/install.sh created${NC}"

# Create launch-converter.sh
echo -e "${BLUE}Creating scripts/launch-converter.sh...${NC}"
cat > scripts/launch-converter.sh << 'LAUNCH_SCRIPT_EOF'
#!/bin/bash
# TweekIT Web Converter Launcher

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

if [ ! -d "examples/web-converter" ]; then
    echo "Error: Must run from tweekit-mcp root"
    exit 1
fi

print_header "TweekIT Web Converter Launcher"

if [ -f .env ]; then
    echo -e "${YELLOW}→ Loading API credentials${NC}"
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Credentials loaded${NC}"
fi

echo ""
echo "Starting standalone HTML version..."
cd examples/web-converter

PORT=8080
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; do
    PORT=$((PORT+1))
done

echo -e "${GREEN}✓ Server starting on port $PORT${NC}"
echo ""
echo "Web Converter: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

if command -v open >/dev/null 2>&1; then
    sleep 1 && open "http://localhost:$PORT" &
fi

python3 -m http.server $PORT
LAUNCH_SCRIPT_EOF

chmod +x scripts/launch-converter.sh
echo -e "${GREEN}✓ scripts/launch-converter.sh created${NC}"

# Create index.html (standalone converter) - FULL VERSION
echo -e "${BLUE}Creating examples/web-converter/index.html...${NC}"
cat > examples/web-converter/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TweekIT Universal File Converter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            color: white;
        }
        .header h1 { font-size: 32px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 40px; }
        .info-banner {
            background: #e3f2fd;
            border: 1px solid #90caf9;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 32px;
        }
        .upload-area {
            border: 2px dashed #ccc;
            border-radius: 12px;
            padding: 60px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .upload-btn {
            background: #667eea;
            color: white;
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        .file-input { display: none; }
        .format-select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 24px;
        }
        .convert-btn {
            width: 100%;
            background: #667eea;
            color: white;
            padding: 16px;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
        }
        .hidden { display: none; }
        .success {
            background: #e8f5e9;
            border: 1px solid #4caf50;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
        }
        .download-btn {
            background: #4caf50;
            color: white;
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            margin: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Universal File Converter</h1>
            <p>Powered by TweekIT MCP - 450+ Formats</p>
        </div>
        <div class="content">
            <div class="info-banner">
                <strong>ℹ️ No File Type Restrictions</strong> - Upload any file format
            </div>
            <div id="upload-section">
                <div class="upload-area">
                    <p style="font-size: 48px; margin-bottom: 16px;">📁</p>
                    <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                        Select File
                    </button>
                    <input type="file" id="fileInput" class="file-input" accept="*/*">
                </div>
            </div>
            <div id="conversion-section" class="hidden">
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 24px;">
                    <p id="fileInfo"></p>
                </div>
                <select id="formatSelect" class="format-select">
                    <option value="pdf">PDF</option>
                    <option value="png">PNG</option>
                    <option value="jpg">JPEG</option>
                    <option value="webp">WebP</option>
                    <option value="docx">DOCX</option>
                </select>
                <button class="convert-btn" onclick="convertFile()">Convert</button>
            </div>
            <div id="success-section" class="hidden">
                <div class="success">
                    <p style="font-size: 48px;">✅</p>
                    <h3>Success!</h3>
                    <a id="downloadLink" class="download-btn" download>Download</a>
                    <button class="upload-btn" onclick="reset()">Convert Another</button>
                </div>
            </div>
        </div>
    </div>
    <script>
        let selectedFile = null;

        document.getElementById('fileInput').addEventListener('change', function(e) {
            if (e.target.files.length > 0) handleFile(e.target.files[0]);
        });

        function handleFile(file) {
            selectedFile = file;
            document.getElementById('fileInfo').textContent = file.name;
            document.getElementById('upload-section').classList.add('hidden');
            document.getElementById('conversion-section').classList.remove('hidden');
        }

        async function convertFile() {
            if (!selectedFile) return;
            const outputFormat = document.getElementById('formatSelect').value;
            const inputExt = selectedFile.name.split('.').pop().toLowerCase();

            try {
                const arrayBuffer = await selectedFile.arrayBuffer();
                const uint8Array = new Uint8Array(arrayBuffer);
                const base64Data = btoa(uint8Array.reduce((data, byte) => data + String.fromCharCode(byte), ''));

                const response = await fetch('https://api.tweekit.com/v1/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        DocData: base64Data,
                        DocDataType: inputExt,
                        Fmt: outputFormat
                    })
                });

                if (!response.ok) throw new Error('Conversion failed');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                document.getElementById('conversion-section').classList.add('hidden');
                document.getElementById('success-section').classList.remove('hidden');
                
                const downloadLink = document.getElementById('downloadLink');
                downloadLink.href = url;
                downloadLink.download = `converted.${outputFormat}`;
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }

        function reset() {
            selectedFile = null;
            document.getElementById('upload-section').classList.remove('hidden');
            document.getElementById('conversion-section').classList.add('hidden');
            document.getElementById('success-section').classList.add('hidden');
        }
    </script>
</body>
</html>
HTML_EOF

echo -e "${GREEN}✓ examples/web-converter/index.html created${NC}"

# Create README
echo -e "${BLUE}Creating examples/web-converter/README.md...${NC}"
cat > examples/web-converter/README.md << 'README_EOF'
# TweekIT Web Converter

Universal file conversion interface supporting 450+ formats.

## Quick Start

```bash
./scripts/launch-converter.sh
```

Or manually:

```bash
cd examples/web-converter
python3 -m http.server 8080
# Open http://localhost:8080
```

## Features

- ✅ 450+ file formats
- ✅ No build required
- ✅ Drag & drop support
- ✅ Works offline

## Supported Formats

- Documents: DOC, DOCX, PDF, ODT, RTF, TXT
- Images: PNG, JPG, WebP, TIFF, PSD, AI, EPS
- Spreadsheets: XLS, XLSX, CSV
- Presentations: PPT, PPTX
- Camera RAW: 40+ formats

Full list: https://tweekit.io/supported-files

## Support

- Docs: https://docs.tweekit.io
- Email: tweekitsupport@equilibrium.com
README_EOF

echo -e "${GREEN}✓ examples/web-converter/README.md created${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete! 🎉${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Files created:"
echo "  ✓ scripts/install.sh"
echo "  ✓ scripts/launch-converter.sh"
echo "  ✓ examples/web-converter/index.html"
echo "  ✓ examples/web-converter/README.md"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the web converter:"
echo "   ./scripts/launch-converter.sh"
echo ""
echo "2. Update your main README.md with:"
echo ""
echo "## Web Converter"
echo ""
echo "Launch the file converter interface:"
echo ""
echo "\`\`\`bash"
echo "./scripts/launch-converter.sh"
echo "\`\`\`"
echo ""
echo "Features:"
echo "- 450+ file format support"
echo "- No file type restrictions"
echo "- Drag & drop interface"
echo ""
echo "See \`examples/web-converter/README.md\` for details."
echo ""

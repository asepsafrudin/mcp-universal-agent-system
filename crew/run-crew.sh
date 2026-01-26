#!/bin/bash

# Auto-run script untuk CrewAI 3-Agent System
# Mengaktifkan virtual environment dan menjalankan sistem dokumentasi otomatis

set -e  # Exit on any error

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"

echo -e "${BLUE}"
echo "🚀 CREWAI 3-AGENT MCP DOCUMENTATION SYSTEM"
echo "============================================================"
echo -e "${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Virtual environment tidak ditemukan di $VENV_DIR${NC}"
    echo -e "${YELLOW}💡 Membuat virtual environment...${NC}"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Activate and install CrewAI
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install crewai==1.7.2
    
    echo -e "${GREEN}✅ Virtual environment berhasil dibuat dan CrewAI diinstall${NC}"
else
    echo -e "${GREEN}✅ Virtual environment ditemukan${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Mengaktifkan virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check if CrewAI is installed
if ! python -c "import crewai" 2>/dev/null; then
    echo -e "${RED}❌ CrewAI tidak terinstall di virtual environment${NC}"
    echo -e "${YELLOW}💡 Menginstall CrewAI...${NC}"
    pip install crewai==1.7.2
fi

# Change to script directory
cd "$SCRIPT_DIR"

echo -e "${GREEN}📁 Working directory: $SCRIPT_DIR${NC}"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py tidak ditemukan di $SCRIPT_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}"
echo "🔬 Starting MCP Documentation CrewAI System..."
echo "   🔍 Researcher Agent: Code analysis & architecture review"
echo "   ✍️  Writer Agent: Technical documentation generation"
echo "   ✅ Checker Agent: Quality assurance & validation"
echo "============================================================"
echo -e "${NC}"

# Run the crew
echo -e "${YELLOW}🚀 Menjalankan CrewAI system...${NC}"
echo ""

# Execute with error handling
if python main.py; then
    echo ""
    echo -e "${GREEN}"
    echo "🎉 CREWAI EXECUTION COMPLETED SUCCESSFULLY!"
    echo "============================================================"
    echo -e "${NC}"
    
    echo -e "${GREEN}📁 Generated files:${NC}"
    
    # Check for output files
    if [ -f "output/mcp-documentation.md" ]; then
        size=$(stat -f%z "output/mcp-documentation.md" 2>/dev/null || stat -c%s "output/mcp-documentation.md" 2>/dev/null || echo "unknown")
        echo -e "   📄 Documentation: output/mcp-documentation.md (${size} bytes)"
    fi
    
    if [ -f "qa_report.md" ]; then
        size=$(stat -f%z "qa_report.md" 2>/dev/null || stat -c%s "qa_report.md" 2>/dev/null || echo "unknown")
        echo -e "   📊 QA Report: qa_report.md (${size} bytes)"
    fi
    
    if [ -f "research_results.json" ]; then
        size=$(stat -f%z "research_results.json" 2>/dev/null || stat -c%s "research_results.json" 2>/dev/null || echo "unknown")
        echo -e "   🔍 Research Data: research_results.json (${size} bytes)"
    fi
    
    if [ -f "crew_execution.log" ]; then
        size=$(stat -f%z "crew_execution.log" 2>/dev/null || stat -c%s "crew_execution.log" 2>/dev/null || echo "unknown")
        echo -e "   📝 Execution Log: crew_execution.log (${size} bytes)"
    fi
    
    echo ""
    echo -e "${BLUE}💡 Tips:${NC}"
    echo "   • Lihat dokumentasi di: output/mcp-documentation.md"
    echo "   • Review QA report untuk quality check"
    echo "   • Jalankan ulang dengan: ./run-crew.sh"
    echo ""
    
else
    echo ""
    echo -e "${RED}❌ CREWAI EXECUTION FAILED${NC}"
    echo "============================================================"
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo "   1. Pastikan MCP server sedang berjalan"
    echo "   2. Check koneksi ke PostgreSQL"
    echo "   3. Lihat execution log untuk detail error"
    echo "   4. Pastikan semua dependencies tersedia"
    echo ""
    exit 1
fi

# Deactivate virtual environment
deactivate 2>/dev/null || true

echo -e "${GREEN}✅ Script selesai dijalankan${NC}"

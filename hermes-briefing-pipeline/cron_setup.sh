#!/usr/bin/env bash
# cron_setup.sh — install the briefing pipeline as a daily cron job
# Usage: bash cron_setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_TIME="0 7 * * *"  # daily at 07:00 — adjust as needed

echo "=== Automated Daily Briefing Pipeline — Cron Setup ==="
echo ""

# Check for fpdf2
python3 -c "import fpdf2" 2>/dev/null || python3 -c "import fpdf" 2>/dev/null || {
  echo "Installing fpdf2..."
  pip install fpdf2 pypdf 2>/dev/null || pip3 install fpdf2 pypdf
}

# Copy example config if not present
if [ ! -f "$SCRIPT_DIR/briefing_config.json" ]; then
  cp "$SCRIPT_DIR/example_config.json" "$SCRIPT_DIR/briefing_config.json"
  echo "📝 Created briefing_config.json from example — edit it with your sources."
fi

# Test build
echo ""
echo "=== Testing PDF generation ==="
python3 "$SCRIPT_DIR/build_briefing.py" "$SCRIPT_DIR/briefing_config.json" /tmp/test_briefing.pdf
echo "✅ Test PDF generated at /tmp/test_briefing.pdf"

# Install cron job
CRON_JOB="$CRON_TIME cd $SCRIPT_DIR && python3 $SCRIPT_DIR/build_briefing.py $SCRIPT_DIR/briefing_config.json $SCRIPT_DIR/daily_briefing.pdf"
(crontab -l 2>/dev/null | grep -v "briefing_config.json"; echo "$CRON_JOB") | crontab -

echo ""
echo "=== ✅ Cron job installed ==="
echo "Runs daily at 07:00"
echo "Output: $SCRIPT_DIR/daily_briefing.pdf"
echo ""
echo "Next step: edit briefing_config.json with your sources, then add email delivery."
echo "See .env.example for SMTP setup."

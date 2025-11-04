#!/bin/bash
# Quick deployment readiness check

echo "🔍 Deployment Readiness Check"
echo

# Check essential files
files=("render.yaml" "requirements.txt")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

# Check FastAPI service
if [ -f "src/ticket_service/src/ticket_service/main.py" ]; then
    echo "✅ FastAPI service found"
else
    echo "❌ FastAPI service missing"
    exit 1
fi

# Check git status
if git status > /dev/null 2>&1; then
    uncommitted=$(git status --porcelain | wc -l)
    if [ "$uncommitted" -gt 0 ]; then
        echo "⚠️  $uncommitted uncommitted changes"
        echo "   Run: git add . && git commit -m 'Ready for deployment'"
    else
        echo "✅ Git ready"
    fi
else
    echo "❌ Not a git repository"
    exit 1
fi

echo
echo "🚀 Ready to deploy!"
echo "   1. git push origin main"
echo "   2. Deploy on render.com"
echo "   3. Set Jira OAuth credentials"
echo
echo "📖 See RENDER_DEPLOYMENT.md for details"
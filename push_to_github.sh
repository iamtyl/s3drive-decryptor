#!/bin/bash
# S3Drive Decryptor - SECURE GitHub Push Script
PROJECT_DIR="/home/tyl/s3drive-decryptor"
TOKEN_FILE="/home/tyl/github_token/token.txt"
REPO_URL="https://github.com/iamtyl/s3drive-decryptor.git"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "❌ Error: Token file not found at $TOKEN_FILE"
    exit 1
fi

# Read token into a local variable
TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n' | tr -d ' ')
AUTH_URL="https://$TOKEN@github.com/iamtyl/s3drive-decryptor.git"

cd "$PROJECT_DIR"

echo "🚀 Starting SECURE push to GitHub..."

# Simple commit message for the decryptor
COMMIT_MSG="Initial commit for S3Drive Decryptor"

git init
git remote set-url origin "$AUTH_URL" 2>/dev/null || git remote add origin "$AUTH_URL"

git add .
git commit -m "$COMMIT_MSG"

git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ SUCCESS! Your code is now on GitHub!"
else
    echo "❌ Push failed. Please check your new token permissions!"
fi

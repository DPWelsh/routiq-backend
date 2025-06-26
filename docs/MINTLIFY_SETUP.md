# 🚀 Mintlify Documentation Setup

**Beautiful API documentation that doesn't suck!** 

We've replaced FastAPI's default documentation with **Mintlify** - a modern, interactive documentation platform that actually helps developers understand and use your API.

## 🎯 What's Included

✅ **Professional Design** - Beautiful, modern UI that looks like real documentation  
✅ **Interactive Examples** - Live code samples in multiple languages  
✅ **Comprehensive Coverage** - All endpoints documented with real examples  
✅ **Search & Navigation** - Easy to find what you need  
✅ **Mobile Responsive** - Works perfectly on all devices  
✅ **Dark/Light Mode** - Automatic theme switching  

## 🏗️ Setup Instructions

### 1. Install Mintlify CLI

```bash
npm install -g mintlify
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
# or
mintlify dev
```

This will start the documentation server at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
# or
mintlify build
```

## 📁 Documentation Structure

```
├── mint.json              # Main configuration
├── introduction.mdx       # Homepage content
├── quickstart.mdx         # Getting started guide
├── authentication.mdx     # Auth documentation
├── api-reference/         # API endpoint docs
│   ├── introduction.mdx
│   └── endpoints/
│       ├── health.mdx     # Example endpoint
│       ├── auth/
│       ├── patients/
│       ├── sync/
│       └── cliniko/
└── package.json          # NPM configuration
```

## 🎨 Customization

### Colors & Branding

Edit `mint.json` to customize:

```json
{
  "colors": {
    "primary": "#0D9373",    // Your primary brand color
    "light": "#07C983",      // Lighter accent
    "dark": "#0D9373"        // Darker accent
  }
}
```

### Navigation

Add/remove pages in `mint.json`:

```json
{
  "navigation": [
    {
      "group": "Get Started",
      "pages": ["introduction", "quickstart"]
    }
  ]
}
```

### Logo & Favicon

Add your logo files to the root directory:
- `/logo/light.svg` - Light mode logo
- `/logo/dark.svg` - Dark mode logo  
- `/favicon.svg` - Favicon

## 📝 Writing Documentation

### MDX Format

All documentation uses **MDX** (Markdown + React components):

```mdx
---
title: "My Endpoint"
api: "GET https://api.example.com/endpoint"
---

## Overview

This endpoint does amazing things!

<Info>
This is an info callout that stands out.
</Info>

<CodeGroup>
```bash cURL
curl https://api.example.com/endpoint
```

```javascript JavaScript
const response = await fetch('https://api.example.com/endpoint');
```
</CodeGroup>
```

### Special Components

Mintlify provides rich components:

- `<Info>` - Information callouts
- `<Warning>` - Warning messages  
- `<Tip>` - Helpful tips
- `<CodeGroup>` - Multi-language code examples
- `<Card>` - Clickable cards
- `<AccordionGroup>` - Collapsible sections

## 🚀 Deployment Options

### Option 1: Mintlify Hosting (Recommended)

```bash
# Deploy to Mintlify's CDN
mintlify deploy
```

### Option 2: Vercel/Netlify

```bash
# Build static files
mintlify build

# Deploy the _site directory to your hosting provider
```

### Option 3: GitHub Pages

Add to `.github/workflows/docs.yml`:

```yaml
name: Deploy Docs
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install -g mintlify
      - run: mintlify build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./_site
```

## 🔧 Advanced Features

### API Integration

Mintlify can auto-generate docs from OpenAPI specs:

```json
{
  "api": {
    "baseUrl": "https://routiq-backend-prod.up.railway.app",
    "auth": {
      "method": "bearer"
    }
  }
}
```

### Custom Domain

Set up a custom domain in `mint.json`:

```json
{
  "domain": "docs.routiq.com"
}
```

### Analytics

Add analytics tracking:

```json
{
  "analytics": {
    "gtag": {
      "measurementId": "G-XXXXXXXXXX"
    }
  }
}
```

## 🆚 Before vs After

### Before (FastAPI Default)
- ❌ Basic, ugly interface
- ❌ No examples or guides  
- ❌ Poor mobile experience
- ❌ No branding
- ❌ Hard to navigate

### After (Mintlify)
- ✅ Professional, beautiful design
- ✅ Interactive examples in multiple languages
- ✅ Perfect mobile experience  
- ✅ Full branding control
- ✅ Easy navigation and search

## 🎯 Next Steps

1. **Customize the branding** - Update colors, logos, and domain
2. **Add more endpoints** - Document all your API endpoints
3. **Add guides** - Create integration guides and tutorials
4. **Deploy** - Make it live for your users
5. **Iterate** - Keep improving based on user feedback

## 🤝 Contributing

To add new documentation:

1. Create new `.mdx` files in appropriate directories
2. Update `mint.json` navigation
3. Test locally with `mintlify dev`
4. Deploy changes

---

**Your API documentation just went from 💩 to ✨!**

Need help? Check out [Mintlify's documentation](https://mintlify.com/docs) or reach out to the team. 
# TradeWise Frontend

Next.js 14 + shadcn/ui frontend for the TradeWise trading dashboard.

## Features

- 📱 **Mobile-first responsive design** - Optimized for all screen sizes
- 🎨 **shadcn/ui components** - Beautiful, accessible UI components
- 🌙 **Dark theme** - Easy on the eyes for trading
- 📊 **PWA support** - Install as a mobile app
- ⚡ **Fast** - Next.js App Router with React Server Components

## Pages

- **Dashboard** (`/`) - Main trading dashboard with signals and overview
- **Login** (`/login`) - Authentication page
- **Stock Screener** (`/screener`) - Scan stocks for trading opportunities
- **Options Scanner** (`/options`) - Find high-probability option trades
- **Index Analyzer** (`/analyzer`) - Deep analysis of index option chains

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Configuration

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard
│   ├── login/             # Login page
│   ├── screener/          # Stock screener
│   ├── options/           # Options scanner
│   └── analyzer/          # Index analyzer
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── layout/            # Header, navigation
│   └── trading/           # Trading-specific components
├── lib/
│   ├── utils.ts           # Utility functions
│   ├── api.ts             # API client
│   └── supabase.ts        # Supabase client
└── public/
    └── manifest.json      # PWA manifest
```

## Mobile Optimization

The app is optimized for mobile with:
- Touch-friendly tap targets (min 44px)
- Responsive typography scaling
- Swipe-friendly navigation
- Safe area insets for notched phones
- Horizontal scroll for data tables
- Collapsible sections on mobile

## Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Static Export

```bash
npm run build
# Output in .next/standalone
```

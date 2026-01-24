'use client'

import * as React from 'react'
import { Header } from '@/components/layout/header'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Bot, Download, Terminal, CheckCircle2, ExternalLink, Copy, Check } from 'lucide-react'
import Link from 'next/link'

export default function MCPIntegrationPage() {
  const [copied, setCopied] = React.useState(false)
  
  const copyCommand = (command: string) => {
    navigator.clipboard.writeText(command)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const oneLineInstall = `curl -fsSL https://raw.githubusercontent.com/fdscoop/stocxer-mcp/main/install.sh | bash`

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <Badge className="mb-4" variant="secondary">
            <Bot className="w-3 h-3 mr-1" />
            AI Assistant Integration
          </Badge>
          <h1 className="text-4xl font-bold mb-4">
            Connect Stocxer to Your AI Assistant
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Access your trading portfolio, get market analysis, and receive actionable signals through natural conversation with Claude, Cursor, or Windsurf.
          </p>
        </div>

        {/* Quick Install */}
        <Card className="mb-8 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="w-5 h-5" />
              Quick Install (Recommended)
            </CardTitle>
            <CardDescription>
              One command to install and configure everything
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted/50 p-4 rounded-lg font-mono text-sm mb-4 flex items-center justify-between">
              <code className="flex-1">{oneLineInstall}</code>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => copyCommand(oneLineInstall)}
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Then restart Claude Desktop and you're ready to go!
            </p>
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">💬 Natural Conversations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>"What are my current positions?"</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>"Analyze NIFTY using ICT concepts"</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>"Should I buy RELIANCE today?"</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">🛡️ Secure & Private</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>No credentials stored locally</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Read-only access (no order placement)</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>Uses your authenticated session</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Supported Assistants */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Supported AI Assistants</CardTitle>
            <CardDescription>
              Works with leading AI coding assistants and chat interfaces
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Claude Desktop</h3>
                <Badge variant="secondary" className="mb-2">Auto-configured</Badge>
                <p className="text-sm text-muted-foreground">
                  Run installer and restart Claude
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Cursor IDE</h3>
                <Badge variant="outline" className="mb-2">Manual config</Badge>
                <p className="text-sm text-muted-foreground">
                  Add to MCP settings
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2">Windsurf</h3>
                <Badge variant="outline" className="mb-2">Manual config</Badge>
                <p className="text-sm text-muted-foreground">
                  Add to settings.json
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Installation Methods */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Download className="w-5 h-5" />
                Method 1: pip
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted/50 p-3 rounded-lg font-mono text-sm mb-3">
                <code>pip install stocxer-mcp</code>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                Then run the installer script from the package directory.
              </p>
              <Link href="https://pypi.org/project/stocxer-mcp/" target="_blank">
                <Button variant="outline" size="sm" className="w-full">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View on PyPI
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                Method 2: Git Clone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted/50 p-3 rounded-lg font-mono text-sm mb-3 break-all">
                <code>git clone https://github.com/fdscoop/stocxer-mcp.git</code>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                Clone the repository and run the installer.
              </p>
              <Link href="https://github.com/fdscoop/stocxer-mcp" target="_blank">
                <Button variant="outline" size="sm" className="w-full">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View on GitHub
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Getting Started */}
        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
            <CardDescription>
              Three simple steps to start trading with AI assistance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                  1
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Install MCP Server</h3>
                  <p className="text-sm text-muted-foreground">
                    Run the one-line installer or use pip to install the package
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                  2
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Authenticate with Stocxer</h3>
                  <p className="text-sm text-muted-foreground">
                    Login at stocxer.in with your Fyers credentials to enable trading features
                  </p>
                </div>
              </div>
              
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold">
                  3
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Start Chatting</h3>
                  <p className="text-sm text-muted-foreground">
                    Restart your AI assistant and start asking questions about your portfolio and the market
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* CTA */}
        <div className="text-center mt-12">
          <Link href="https://github.com/fdscoop/stocxer-mcp" target="_blank">
            <Button size="lg" className="mr-4">
              <Download className="w-5 h-5 mr-2" />
              Get Started
            </Button>
          </Link>
          <Link href="/">
            <Button size="lg" variant="outline">
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </main>
    </div>
  )
}

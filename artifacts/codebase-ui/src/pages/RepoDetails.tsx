import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { repoApi, analysisApi } from "@/lib/api";
import { Navbar } from "@/components/layout/Navbar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle, FileText, CheckCircle2, AlertTriangle, Info, MessageSquare, Send, GitBranch, ArrowLeft, Loader2, GitCommit, Layers, Code2, AlertOctagon } from "lucide-react";
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState } from "@xyflow/react";
import "@xyflow/react/dist/style.css";

// ── Components ─────────────────────────────────────────────────────────────

function OverviewTab({ id }: { id: string }) {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', id],
    queryFn: () => repoApi.summary(id),
    refetchInterval: (query) => (query.state.data?.status === 'complete' || query.state.data?.status === 'failed') ? false : 5000,
  });

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-48 w-full" /><Skeleton className="h-64 w-full" /></div>;
  if (!summary) return <div>Failed to load overview</div>;

  return (
    <div className="grid gap-6 md:grid-cols-3">
      <Card className="md:col-span-2 shadow-sm border-muted">
        <CardHeader>
          <CardTitle>Architecture Summary</CardTitle>
          <CardDescription>AI-generated overview of the codebase</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {summary.architecture_summary ? (
              <div className="whitespace-pre-wrap font-mono text-sm bg-muted/30 p-6 rounded-md border">{summary.architecture_summary}</div>
            ) : (
              <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground border border-dashed rounded-md">
                <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
                <p>Analyzing architecture...</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      <div className="space-y-6">
        <Card className="shadow-sm border-muted">
          <CardHeader>
            <CardTitle className="text-lg">Repository Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-1">Status</div>
              <div className="flex items-center">
                <Badge variant={summary.status === 'complete' ? 'default' : 'secondary'} className={summary.status === 'complete' ? 'bg-green-100 text-green-800' : ''}>
                  {summary.status}
                </Badge>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-1">Files</div>
                <div className="text-2xl font-bold font-mono">{summary.file_count?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-1">Lines</div>
                <div className="text-2xl font-bold font-mono">{summary.total_lines?.toLocaleString()}</div>
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-2">Languages</div>
              <div className="flex flex-wrap gap-2">
                {summary.languages?.map(lang => (
                  <Badge key={lang} variant="outline" className="bg-slate-50">{lang}</Badge>
                ))}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground mb-1">Source</div>
              <a href={summary.github_url} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline flex items-center break-all">
                {summary.github_url}
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function IssuesTab({ id }: { id: string }) {
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  
  const { data: issues, isLoading } = useQuery({
    queryKey: ['issues', id],
    queryFn: () => analysisApi.issues(id),
  });

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-24 w-full" /><Skeleton className="h-24 w-full" /></div>;
  if (!issues || issues.length === 0) return (
    <div className="text-center p-12 border border-dashed rounded-lg bg-white">
      <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900">No issues found</h3>
      <p className="text-muted-foreground mt-1">The codebase looks clean.</p>
    </div>
  );

  const filteredIssues = severityFilter === "all" ? issues : issues.filter(i => i.severity.toLowerCase() === severityFilter);

  const getSeverityIcon = (sev: string) => {
    switch(sev.toLowerCase()) {
      case 'critical': return <AlertOctagon className="w-5 h-5 text-red-500" />;
      case 'high': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      case 'medium': return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch(sev.toLowerCase()) {
      case 'critical': return <Badge variant="destructive" className="bg-red-100 text-red-800 uppercase text-[10px]">Critical</Badge>;
      case 'high': return <Badge variant="outline" className="border-orange-200 bg-orange-50 text-orange-800 uppercase text-[10px]">High</Badge>;
      case 'medium': return <Badge variant="outline" className="border-yellow-200 bg-yellow-50 text-yellow-800 uppercase text-[10px]">Medium</Badge>;
      default: return <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-800 uppercase text-[10px]">Low</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button variant={severityFilter === "all" ? "default" : "outline"} size="sm" onClick={() => setSeverityFilter("all")}>All ({issues.length})</Button>
        <Button variant={severityFilter === "critical" ? "default" : "outline"} size="sm" onClick={() => setSeverityFilter("critical")} className={severityFilter === "critical" ? "bg-red-600" : ""}>Critical</Button>
        <Button variant={severityFilter === "high" ? "default" : "outline"} size="sm" onClick={() => setSeverityFilter("high")} className={severityFilter === "high" ? "bg-orange-500" : ""}>High</Button>
        <Button variant={severityFilter === "medium" ? "default" : "outline"} size="sm" onClick={() => setSeverityFilter("medium")} className={severityFilter === "medium" ? "bg-yellow-500" : ""}>Medium</Button>
      </div>

      <div className="grid gap-4">
        {filteredIssues.map((issue) => (
          <Card key={issue.issue_id} className="shadow-sm border-muted overflow-hidden">
            <div className="flex border-b border-muted bg-muted/20 px-4 py-3 items-center justify-between">
              <div className="flex items-center gap-3">
                {getSeverityIcon(issue.severity)}
                <div className="font-mono text-sm text-muted-foreground flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  {issue.file_path} {issue.line && <span className="text-xs ml-1 bg-muted px-1.5 py-0.5 rounded">:{issue.line}</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <Badge variant="outline" className="bg-slate-50 font-mono text-[10px]">{issue.issue_type}</Badge>
                {getSeverityBadge(issue.severity)}
              </div>
            </div>
            <CardContent className="p-4">
              <div className="text-sm font-medium mb-2">{issue.message}</div>
              {issue.suggestion && (
                <div className="mt-3 bg-green-50/50 border border-green-100 rounded-md p-3 text-sm">
                  <span className="font-semibold text-green-800 text-xs uppercase tracking-wider block mb-1">Suggestion</span>
                  <div className="text-green-900">{issue.suggestion}</div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function RefactorTab({ id }: { id: string }) {
  const { data: suggestions, isLoading } = useQuery({
    queryKey: ['refactor', id],
    queryFn: () => analysisApi.refactor(id),
  });

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-48 w-full" /></div>;
  if (!suggestions || suggestions.length === 0) return (
    <div className="text-center p-12 border border-dashed rounded-lg bg-white">
      <Code2 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900">No refactoring suggestions</h3>
      <p className="text-muted-foreground mt-1">Code structure looks solid.</p>
    </div>
  );

  return (
    <div className="space-y-6">
      {suggestions.map((suggestion) => (
        <Card key={suggestion.suggestion_id} className="shadow-sm border-muted">
          <CardHeader className="pb-3 border-b bg-muted/10">
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-lg text-primary">{suggestion.title}</CardTitle>
                <CardDescription className="mt-1 flex items-center font-mono text-xs">
                  <FileText className="w-3.5 h-3.5 mr-1" /> {suggestion.file_path}
                </CardDescription>
              </div>
              <Badge variant="outline" className="uppercase text-[10px] tracking-wider">{suggestion.effort} Effort</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <p className="text-sm text-gray-700 mb-6">{suggestion.description}</p>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {suggestion.original_code && (
                <div className="rounded-md border border-red-200 overflow-hidden">
                  <div className="bg-red-50 text-red-800 text-xs font-semibold px-3 py-1.5 border-b border-red-200 uppercase tracking-wider">Original</div>
                  <pre className="p-4 text-xs font-mono bg-slate-950 text-slate-50 overflow-x-auto m-0">
                    <code>{suggestion.original_code}</code>
                  </pre>
                </div>
              )}
              {suggestion.suggested_code && (
                <div className="rounded-md border border-green-200 overflow-hidden">
                  <div className="bg-green-50 text-green-800 text-xs font-semibold px-3 py-1.5 border-b border-green-200 uppercase tracking-wider">Suggested</div>
                  <pre className="p-4 text-xs font-mono bg-slate-950 text-slate-50 overflow-x-auto m-0">
                    <code>{suggestion.suggested_code}</code>
                  </pre>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function GraphTab({ id }: { id: string }) {
  const { data: graphData, isLoading } = useQuery({
    queryKey: ['graph', id],
    queryFn: () => analysisApi.graph(id),
  });

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (graphData && graphData.nodes) {
      // Basic layout - spread in a grid
      const cols = Math.ceil(Math.sqrt(graphData.nodes.length));
      const spacing = 150;
      
      const newNodes = graphData.nodes.map((node, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        
        let color = '#94a3b8'; // default
        if (node.node_type === 'file') color = '#3b82f6';
        if (node.node_type === 'class') color = '#22c55e';
        if (node.node_type === 'function') color = '#f97316';

        return {
          id: node.node_id,
          data: { label: node.name },
          position: { x: col * spacing + Math.random() * 20, y: row * spacing + Math.random() * 20 },
          style: { 
            background: '#fff', 
            border: `2px solid ${color}`,
            borderRadius: '4px',
            padding: '8px',
            fontSize: '12px',
            fontFamily: 'monospace'
          }
        };
      });

      const newEdges = graphData.edges.map((edge, i) => ({
        id: `e${i}`,
        source: edge.source_id,
        target: edge.target_id,
        animated: edge.edge_type === 'calls',
        label: edge.edge_type,
        style: { stroke: '#94a3b8' },
        labelStyle: { fontSize: 10, fill: '#64748b' }
      }));

      setNodes(newNodes);
      setEdges(newEdges);
    }
  }, [graphData, setNodes, setEdges]);

  if (isLoading) return <Skeleton className="h-[600px] w-full" />;
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return (
    <div className="text-center p-12 border border-dashed rounded-lg bg-white h-[400px] flex flex-col items-center justify-center">
      <GitCommit className="w-12 h-12 text-slate-300 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900">Graph generation pending</h3>
      <p className="text-muted-foreground mt-1">Check back once parsing is complete.</p>
    </div>
  );

  return (
    <Card className="h-[600px] w-full border-muted shadow-sm overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-right"
      >
        <Background gap={12} size={1} color="#f1f5f9" />
        <Controls />
        <MiniMap nodeStrokeColor="#e2e8f0" nodeColor="#f8fafc" maskColor="rgba(240, 245, 250, 0.6)" />
      </ReactFlow>
    </Card>
  );
}

function ChatTab({ id }: { id: string }) {
  const [messages, setMessages] = useState<{role: 'user' | 'assistant', content: string, chunks?: any[]}[]>([
    { role: 'assistant', content: 'Hello! I\'ve analyzed this repository. What would you like to know about the codebase?' }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const res = await analysisApi.ask(id, userMessage);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: res.answer,
        chunks: res.source_chunks
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error while analyzing the code to answer your question.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="flex flex-col h-[600px] shadow-sm border-muted">
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-6 pb-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-lg p-4 ${
                msg.role === 'user' 
                  ? 'bg-primary text-primary-foreground ml-auto' 
                  : 'bg-muted/50 border shadow-sm text-foreground'
              }`}>
                <div className="prose prose-sm dark:prose-invert max-w-none break-words">
                  {msg.content}
                </div>
                
                {msg.chunks && msg.chunks.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-border/50">
                    <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center">
                      <Layers className="w-3 h-3 mr-1" /> Sources
                    </div>
                    <div className="space-y-2">
                      {msg.chunks.map((chunk, j) => (
                        <div key={j} className="bg-background rounded text-xs border overflow-hidden">
                          <div className="bg-muted px-2 py-1 border-b font-mono text-[10px] text-muted-foreground">
                            {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line})
                          </div>
                          <pre className="p-2 m-0 font-mono text-[10px] overflow-x-auto max-h-32 text-slate-700">
                            <code>{chunk.content}</code>
                          </pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted/50 border rounded-lg p-4 text-muted-foreground flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Analyzing codebase...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
      <div className="p-3 border-t bg-muted/10">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex gap-2"
        >
          <Input 
            value={input} 
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about the architecture, how a feature works, or where to find something..."
            className="flex-1 bg-background"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </Card>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function RepoDetails() {
  const { id } = useParams();
  
  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', id],
    queryFn: () => repoApi.summary(id!),
    enabled: !!id
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50/50">
        <Navbar />
        <main className="container mx-auto py-8 px-4 max-w-6xl">
          <Skeleton className="h-10 w-64 mb-8" />
          <Skeleton className="h-[600px] w-full" />
        </main>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-gray-50/50">
        <Navbar />
        <main className="container mx-auto py-8 px-4 max-w-6xl text-center pt-24">
          <h2 className="text-2xl font-bold mb-2">Repository not found</h2>
          <p className="text-muted-foreground mb-6">The analysis you're looking for doesn't exist or has been deleted.</p>
          <Link href="/dashboard"><Button>Back to Dashboard</Button></Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50/50 pb-12">
      <Navbar />
      
      <main className="container mx-auto py-6 px-4 max-w-6xl">
        <div className="mb-6">
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold font-mono tracking-tight flex items-center gap-3">
                {summary.github_url.split('github.com/')[1] || summary.github_url}
              </h1>
            </div>
            {summary.status === 'processing' && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 py-1">
                <Loader2 className="w-3 h-3 mr-2 animate-spin" /> Processing
              </Badge>
            )}
          </div>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="w-full justify-start border-b rounded-none h-12 bg-transparent p-0 space-x-6 mb-6">
            <TabsTrigger value="overview" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 h-12 font-medium">
              Overview
            </TabsTrigger>
            <TabsTrigger value="issues" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 h-12 font-medium flex items-center gap-2">
              Issues
            </TabsTrigger>
            <TabsTrigger value="refactoring" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 h-12 font-medium flex items-center gap-2">
              Refactoring
            </TabsTrigger>
            <TabsTrigger value="graph" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 h-12 font-medium flex items-center gap-2">
              Dependency Graph
            </TabsTrigger>
            <TabsTrigger value="chat" className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-primary data-[state=active]:shadow-none rounded-none px-2 h-12 font-medium flex items-center gap-2">
              <MessageSquare className="w-4 h-4" /> Q&A Chat
            </TabsTrigger>
          </TabsList>
          
          <div className="mt-2">
            <TabsContent value="overview" className="m-0"><OverviewTab id={id!} /></TabsContent>
            <TabsContent value="issues" className="m-0"><IssuesTab id={id!} /></TabsContent>
            <TabsContent value="refactoring" className="m-0"><RefactorTab id={id!} /></TabsContent>
            <TabsContent value="graph" className="m-0"><GraphTab id={id!} /></TabsContent>
            <TabsContent value="chat" className="m-0"><ChatTab id={id!} /></TabsContent>
          </div>
        </Tabs>
      </main>
    </div>
  );
}

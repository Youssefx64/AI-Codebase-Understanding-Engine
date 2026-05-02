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
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion } from "framer-motion";

// ── Components ─────────────────────────────────────────────────────────────

function OverviewTab({ id }: { id: string }) {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['summary', id],
    queryFn: () => repoApi.summary(id),
    refetchInterval: (query) => (query.state.data?.status === 'complete' || query.state.data?.status === 'failed') ? false : 5000,
  });

  if (isLoading) return <div className="space-y-6"><Skeleton className="h-[200px] w-full bg-muted/50 rounded-xl" /><Skeleton className="h-[300px] w-full bg-muted/50 rounded-xl" /></div>;
  if (!summary) return <div>Failed to load overview</div>;

  return (
    <motion.div initial={{opacity:0, y:16}} animate={{opacity:1, y:0}} className="grid gap-6 md:grid-cols-3">
      <Card className="md:col-span-2 bg-card shadow-none">
        <CardHeader>
          <CardTitle>Architecture Summary</CardTitle>
          <CardDescription>AI-generated overview of the codebase structure and patterns</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {summary.architecture_summary ? (
              <div className="whitespace-pre-wrap font-mono text-sm bg-muted/30 p-6 rounded-xl border leading-relaxed text-muted-foreground">{summary.architecture_summary}</div>
            ) : (
              <div className="flex flex-col items-center justify-center p-12 text-center text-muted-foreground border border-dashed rounded-xl bg-muted/10">
                <Loader2 className="h-8 w-8 animate-spin mb-4 text-primary" />
                <p>Analyzing architecture and generating summary...</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      <div className="space-y-6">
        <Card className="bg-card shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Repository Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Status</div>
              <Badge variant={summary.status === 'complete' ? 'default' : 'secondary'} className={summary.status === 'complete' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-zinc-800 text-zinc-400 border border-zinc-700'}>
                {summary.status}
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Files</div>
                <div className="text-2xl font-bold font-mono text-foreground">{summary.file_count?.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Lines</div>
                <div className="text-2xl font-bold font-mono text-foreground">{summary.total_lines?.toLocaleString()}</div>
              </div>
            </div>
            <div>
              <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Languages</div>
              <div className="flex flex-wrap gap-2">
                {summary.languages?.map(lang => (
                  <Badge key={lang} variant="secondary" className="bg-muted text-muted-foreground font-mono text-xs">{lang}</Badge>
                ))}
              </div>
            </div>
            <div>
              <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Source</div>
              <a href={summary.github_url} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline flex items-center break-all font-mono">
                {summary.github_url}
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}

function IssuesTab({ id }: { id: string }) {
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  
  const { data: issues, isLoading } = useQuery({
    queryKey: ['issues', id],
    queryFn: () => analysisApi.issues(id),
  });

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-24 w-full bg-muted/50 rounded-xl" /><Skeleton className="h-24 w-full bg-muted/50 rounded-xl" /></div>;
  if (!issues || issues.length === 0) return (
    <div className="text-center p-16 border border-border/50 rounded-xl bg-card mt-4">
      <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-foreground">No issues found</h3>
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
      case 'critical': return <Badge variant="destructive" className="bg-red-950 text-red-400 border border-red-800 uppercase text-[10px]">Critical</Badge>;
      case 'high': return <Badge variant="outline" className="bg-orange-950 text-orange-400 border border-orange-800 uppercase text-[10px]">High</Badge>;
      case 'medium': return <Badge variant="outline" className="bg-yellow-950 text-yellow-400 border border-yellow-800 uppercase text-[10px]">Medium</Badge>;
      default: return <Badge variant="outline" className="bg-blue-950 text-blue-400 border border-blue-800 uppercase text-[10px]">Low</Badge>;
    }
  };

  const getSeverityColor = (sev: string) => {
    switch(sev.toLowerCase()) {
      case 'critical': return "border-l-red-500";
      case 'high': return "border-l-orange-500";
      case 'medium': return "border-l-yellow-500";
      default: return "border-l-blue-500";
    }
  };

  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05 } } };
  const itemVariants = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } };

  return (
    <div className="space-y-6 mt-4">
      <div className="flex gap-2 p-1 bg-muted/30 rounded-lg w-max border">
        <Button variant={severityFilter === "all" ? "secondary" : "ghost"} size="sm" onClick={() => setSeverityFilter("all")} className="text-xs h-8">All ({issues.length})</Button>
        <Button variant={severityFilter === "critical" ? "secondary" : "ghost"} size="sm" onClick={() => setSeverityFilter("critical")} className="text-xs h-8 text-red-500 hover:text-red-400">Critical</Button>
        <Button variant={severityFilter === "high" ? "secondary" : "ghost"} size="sm" onClick={() => setSeverityFilter("high")} className="text-xs h-8 text-orange-500 hover:text-orange-400">High</Button>
        <Button variant={severityFilter === "medium" ? "secondary" : "ghost"} size="sm" onClick={() => setSeverityFilter("medium")} className="text-xs h-8 text-yellow-500 hover:text-yellow-400">Medium</Button>
      </div>

      <motion.div initial="hidden" animate="visible" variants={containerVariants} className="grid gap-4">
        {filteredIssues.map((issue) => (
          <motion.div variants={itemVariants} key={issue.issue_id}>
            <Card className={`shadow-none border-border overflow-hidden border-l-[3px] ${getSeverityColor(issue.severity)}`}>
              <div className="flex border-b border-border bg-muted/20 px-5 py-3 items-center justify-between">
                <div className="flex items-center gap-3">
                  {getSeverityIcon(issue.severity)}
                  <div className="font-mono text-sm text-foreground flex items-center gap-2">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    {issue.file_path} {issue.line && <span className="text-xs ml-1 bg-muted text-muted-foreground px-1.5 py-0.5 rounded">:{issue.line}</span>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Badge variant="secondary" className="bg-muted text-muted-foreground font-mono text-[10px]">{issue.issue_type}</Badge>
                  {getSeverityBadge(issue.severity)}
                </div>
              </div>
              <CardContent className="p-5">
                <div className="text-sm font-medium mb-3 text-foreground leading-relaxed">{issue.message}</div>
                {issue.suggestion && (
                  <div className="mt-4 bg-primary/5 border border-primary/20 rounded-lg p-4 text-sm">
                    <span className="font-semibold text-primary text-[10px] uppercase tracking-wider block mb-2">Suggestion</span>
                    <div className="text-muted-foreground leading-relaxed">{issue.suggestion}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}

function RefactorTab({ id }: { id: string }) {
  const { data: suggestions, isLoading } = useQuery({
    queryKey: ['refactor', id],
    queryFn: () => analysisApi.refactor(id),
  });

  if (isLoading) return <div className="space-y-4"><Skeleton className="h-48 w-full bg-muted/50 rounded-xl" /></div>;
  if (!suggestions || suggestions.length === 0) return (
    <div className="text-center p-16 border border-border/50 rounded-xl bg-card mt-4">
      <Code2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
      <h3 className="text-lg font-medium text-foreground">No refactoring suggestions</h3>
      <p className="text-muted-foreground mt-1">Code structure looks solid.</p>
    </div>
  );

  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05 } } };
  const itemVariants = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } };

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-6 mt-4">
      {suggestions.map((suggestion) => (
        <motion.div variants={itemVariants} key={suggestion.suggestion_id}>
          <Card className="shadow-none border-border bg-card">
            <CardHeader className="pb-4 border-b border-border bg-muted/10">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg text-foreground font-semibold">{suggestion.title}</CardTitle>
                  <CardDescription className="mt-2 flex items-center font-mono text-xs">
                    <FileText className="w-3.5 h-3.5 mr-1.5 text-muted-foreground" /> {suggestion.file_path}
                  </CardDescription>
                </div>
                <Badge variant="outline" className="uppercase text-[10px] tracking-wider text-muted-foreground border-border">{suggestion.effort} Effort</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">{suggestion.description}</p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {suggestion.original_code && (
                  <div className="rounded-xl border border-red-900/50 overflow-hidden bg-black/40">
                    <div className="bg-red-950/30 text-red-400 text-[10px] font-semibold px-4 py-2 border-b border-red-900/50 uppercase tracking-wider">Original</div>
                    <pre className="p-4 text-xs font-mono text-slate-300 overflow-x-auto m-0 leading-relaxed">
                      <code>{suggestion.original_code}</code>
                    </pre>
                  </div>
                )}
                {suggestion.suggested_code && (
                  <div className="rounded-xl border border-emerald-900/50 overflow-hidden bg-black/40">
                    <div className="bg-emerald-950/30 text-emerald-400 text-[10px] font-semibold px-4 py-2 border-b border-emerald-900/50 uppercase tracking-wider">Suggested</div>
                    <pre className="p-4 text-xs font-mono text-slate-300 overflow-x-auto m-0 leading-relaxed">
                      <code>{suggestion.suggested_code}</code>
                    </pre>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}

function GraphTab({ id }: { id: string }) {
  const { data: graphData, isLoading } = useQuery({
    queryKey: ['graph', id],
    queryFn: () => analysisApi.graph(id),
  });

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (graphData && graphData.nodes) {
      const cols = Math.ceil(Math.sqrt(graphData.nodes.length));
      const spacing = 180;
      
      const newNodes = graphData.nodes.map((node, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        
        let color = '#475569'; // muted
        if (node.node_type === 'file') color = '#0ea5e9'; // blue
        if (node.node_type === 'class') color = '#10b981'; // green
        if (node.node_type === 'function') color = '#8b5cf6'; // purple

        return {
          id: node.node_id,
          data: { label: node.name },
          position: { x: col * spacing + Math.random() * 30, y: row * spacing + Math.random() * 30 },
          style: { 
            background: '#0a0a0f', 
            border: `1px solid ${color}`,
            borderRadius: '8px',
            padding: '12px 16px',
            fontSize: '12px',
            fontFamily: 'JetBrains Mono, monospace',
            color: '#f8fafc',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
          }
        };
      });

      const newEdges = graphData.edges.map((edge, i) => ({
        id: `e${i}`,
        source: edge.source_id,
        target: edge.target_id,
        animated: edge.edge_type === 'calls',
        label: edge.edge_type,
        style: { stroke: '#475569', strokeWidth: 1.5 },
        labelStyle: { fontSize: 10, fill: '#94a3b8', background: '#0a0a0f' },
        labelBgStyle: { fill: '#0a0a0f' }
      }));

      setNodes(newNodes);
      setEdges(newEdges);
    }
  }, [graphData, setNodes, setEdges]);

  if (isLoading) return <Skeleton className="h-[600px] w-full bg-muted/50 rounded-xl mt-4" />;
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return (
    <div className="text-center p-16 border border-border/50 rounded-xl bg-card h-[400px] flex flex-col items-center justify-center mt-4">
      <GitCommit className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
      <h3 className="text-lg font-medium text-foreground">Graph generation pending</h3>
      <p className="text-muted-foreground mt-1">Check back once parsing is complete.</p>
    </div>
  );

  return (
    <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mt-4">
      <Card className="h-[600px] w-full border-border shadow-none overflow-hidden bg-[#0a0a0f] rounded-xl">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          attributionPosition="bottom-right"
          style={{ background: 'transparent' }}
          colorMode="dark"
        >
          <Background gap={16} size={1} color="#333" />
          <Controls className="bg-muted border-border fill-foreground" />
          <MiniMap nodeStrokeColor="#333" nodeColor="#1a1a1a" maskColor="rgba(0, 0, 0, 0.6)" className="bg-card border-border" />
        </ReactFlow>
      </Card>
    </motion.div>
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

  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } };

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants} className="mt-4">
      <Card className="flex flex-col h-[600px] shadow-none border-border bg-card rounded-xl">
        <ScrollArea className="flex-1 p-6" ref={scrollRef}>
          <div className="space-y-6 pb-4">
            {messages.map((msg, i) => (
              <motion.div variants={itemVariants} key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-5 text-sm leading-relaxed ${
                  msg.role === 'user' 
                    ? 'bg-primary/20 text-foreground rounded-2xl rounded-br-sm' 
                    : 'bg-muted/30 border border-border text-foreground rounded-2xl rounded-bl-sm'
                }`}>
                  <div className="prose prose-sm dark:prose-invert max-w-none break-words text-foreground">
                    {msg.content}
                  </div>
                  
                  {msg.chunks && msg.chunks.length > 0 && (
                    <div className="mt-5 pt-4 border-t border-border">
                      <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-3 flex items-center">
                        <Layers className="w-3.5 h-3.5 mr-1.5" /> Source Citations
                      </div>
                      <div className="space-y-2">
                        {msg.chunks.map((chunk, j) => (
                          <div key={j} className="bg-black/40 rounded-lg border border-border overflow-hidden">
                            <div className="bg-muted/50 px-3 py-1.5 border-b border-border font-mono text-[10px] text-muted-foreground">
                              {chunk.file_path} <span className="opacity-50 ml-1">:{chunk.start_line}-{chunk.end_line}</span>
                            </div>
                            <pre className="p-3 m-0 font-mono text-[11px] overflow-x-auto max-h-32 text-slate-300 leading-relaxed">
                              <code>{chunk.content}</code>
                            </pre>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
            {isLoading && (
              <motion.div initial={{opacity:0}} animate={{opacity:1}} className="flex justify-start">
                <div className="bg-muted/30 border border-border rounded-2xl rounded-bl-sm p-4 text-muted-foreground flex items-center gap-3">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="text-sm font-medium">Analyzing codebase...</span>
                </div>
              </motion.div>
            )}
          </div>
        </ScrollArea>
        <div className="p-4 border-t border-border bg-muted/10 rounded-b-xl">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex gap-3 max-w-4xl mx-auto w-full relative"
          >
            <Input 
              value={input} 
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about the architecture, how a feature works..."
              className="flex-1 h-12 bg-background border-border pr-12 rounded-xl text-sm font-medium"
              disabled={isLoading}
            />
            <Button type="submit" size="icon" className="absolute right-1 top-1 h-10 w-10 rounded-lg glow-primary" disabled={isLoading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </motion.div>
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
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container max-w-7xl mx-auto py-12 px-6">
          <Skeleton className="h-10 w-64 mb-8 bg-muted/50 rounded-lg" />
          <Skeleton className="h-[600px] w-full bg-muted/50 rounded-2xl" />
        </main>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container max-w-7xl mx-auto py-24 px-6 text-center flex flex-col items-center">
          <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-6">
            <AlertCircle className="w-8 h-8 text-muted-foreground" />
          </div>
          <h2 className="text-2xl font-bold mb-3">Repository not found</h2>
          <p className="text-muted-foreground mb-8 max-w-sm">The analysis you're looking for doesn't exist or has been deleted.</p>
          <Link href="/dashboard"><Button className="h-11 px-6 font-medium">Back to Dashboard</Button></Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <Navbar />
      
      <main className="container max-w-7xl mx-auto py-10 px-6">
        <motion.div initial={{opacity:0, y:-10}} animate={{opacity:1, y:0}} className="mb-10">
          <Link href="/dashboard" className="text-xs font-semibold text-muted-foreground hover:text-foreground inline-flex items-center mb-6 transition-colors uppercase tracking-wider">
            <ArrowLeft className="w-3.5 h-3.5 mr-1.5" /> Back to Dashboard
          </Link>
          <div className="flex items-center justify-between border-b border-border pb-6">
            <div>
              <h1 className="text-3xl font-bold font-mono tracking-tight flex items-center gap-3">
                {summary.github_url.split('github.com/')[1] || summary.github_url}
              </h1>
            </div>
            {summary.status === 'processing' && (
              <Badge variant="outline" className="bg-violet-950 text-violet-300 border-violet-800 py-1.5 px-3 text-xs uppercase tracking-wider">
                <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> Processing
              </Badge>
            )}
          </div>
        </motion.div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="w-full justify-start h-auto bg-transparent p-0 gap-2 mb-8 flex-wrap">
            <TabsTrigger value="overview" className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:border-primary/20 data-[state=active]:shadow-none border border-transparent rounded-md px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-all">
              Overview
            </TabsTrigger>
            <TabsTrigger value="issues" className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:border-primary/20 data-[state=active]:shadow-none border border-transparent rounded-md px-4 py-2 text-sm font-medium flex items-center gap-2 text-muted-foreground hover:text-foreground transition-all">
              Issues
            </TabsTrigger>
            <TabsTrigger value="refactoring" className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:border-primary/20 data-[state=active]:shadow-none border border-transparent rounded-md px-4 py-2 text-sm font-medium flex items-center gap-2 text-muted-foreground hover:text-foreground transition-all">
              Refactoring
            </TabsTrigger>
            <TabsTrigger value="graph" className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:border-primary/20 data-[state=active]:shadow-none border border-transparent rounded-md px-4 py-2 text-sm font-medium flex items-center gap-2 text-muted-foreground hover:text-foreground transition-all">
              Dependency Graph
            </TabsTrigger>
            <TabsTrigger value="chat" className="data-[state=active]:bg-primary/15 data-[state=active]:text-primary data-[state=active]:border-primary/20 data-[state=active]:shadow-none border border-transparent rounded-md px-4 py-2 text-sm font-medium flex items-center gap-2 text-muted-foreground hover:text-foreground transition-all">
              <MessageSquare className="w-4 h-4" /> Q&A Chat
            </TabsTrigger>
          </TabsList>
          
          <div className="mt-2">
            <TabsContent value="overview" className="m-0 border-none p-0 focus-visible:ring-0"><OverviewTab id={id!} /></TabsContent>
            <TabsContent value="issues" className="m-0 border-none p-0 focus-visible:ring-0"><IssuesTab id={id!} /></TabsContent>
            <TabsContent value="refactoring" className="m-0 border-none p-0 focus-visible:ring-0"><RefactorTab id={id!} /></TabsContent>
            <TabsContent value="graph" className="m-0 border-none p-0 focus-visible:ring-0"><GraphTab id={id!} /></TabsContent>
            <TabsContent value="chat" className="m-0 border-none p-0 focus-visible:ring-0"><ChatTab id={id!} /></TabsContent>
          </div>
        </Tabs>
      </main>
    </div>
  );
}
import { useState } from "react";
import { Link, useLocation } from "wouter";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Github, Search, Clock, Code, GitBranch, ArrowRight, Loader2, XCircle, CheckCircle } from "lucide-react";
import { repoApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form";
import { Skeleton } from "@/components/ui/skeleton";
import { Navbar } from "@/components/layout/Navbar";
import { motion } from "framer-motion";

const analyzeSchema = z.object({
  github_url: z.string().url("Must be a valid URL").includes("github.com", { message: "Must be a GitHub URL" }),
  branch: z.string().default("main"),
});

type AnalyzeFormValues = z.infer<typeof analyzeSchema>;

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [searchTerm, setSearchTerm] = useState("");

  const { data: repos, isLoading, error } = useQuery({
    queryKey: ['repos'],
    queryFn: repoApi.list,
    refetchInterval: 5000 // Poll every 5s for status updates
  });

  const form = useForm<AnalyzeFormValues>({
    resolver: zodResolver(analyzeSchema),
    defaultValues: { github_url: "", branch: "main" },
  });

  const analyzeMutation = useMutation({
    mutationFn: (data: AnalyzeFormValues) => repoApi.analyze(data.github_url, data.branch),
    onSuccess: (data) => {
      toast.success("Repository analysis started");
      form.reset();
      queryClient.invalidateQueries({ queryKey: ['repos'] });
      if (data.repo_id) {
        setLocation(`/repo/${data.repo_id}`);
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to start analysis");
    },
  });

  function onSubmit(data: AnalyzeFormValues) {
    analyzeMutation.mutate(data);
  }

  const filteredRepos = repos?.filter(repo => 
    repo.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    repo.owner.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    switch(status.toLowerCase()) {
      case 'pending': 
        return <Badge variant="secondary" className="bg-zinc-800 text-zinc-400 border border-zinc-700 uppercase text-[10px]"><Clock className="w-3 h-3 mr-1"/> Pending</Badge>;
      case 'complete': 
        return <Badge variant="default" className="bg-emerald-950 text-emerald-400 border border-emerald-800 uppercase text-[10px]"><CheckCircle className="w-3 h-3 mr-1"/> Complete</Badge>;
      case 'failed': 
        return <Badge variant="destructive" className="bg-red-950 text-red-400 border border-red-800 uppercase text-[10px]"><XCircle className="w-3 h-3 mr-1"/> Failed</Badge>;
      default: 
        return <Badge variant="outline" className="bg-violet-950 text-violet-300 border border-violet-800 uppercase text-[10px]"><Loader2 className="w-3 h-3 mr-1 animate-spin"/> {status}</Badge>;
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.06 } }
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container max-w-7xl mx-auto py-12 px-6">
        <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-12">
          
          {/* Header Area */}
          <motion.div variants={itemVariants} className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">
              {getGreeting()}, {user?.username || 'Developer'}
            </h1>
            <p className="text-muted-foreground">
              Here are your analyzed repositories.
            </p>
          </motion.div>

          {/* Submit Form Banner */}
          <motion.div variants={itemVariants}>
            <div className="w-full rounded-2xl border border-primary/20 bg-primary/5 p-6 md:p-8">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Github className="w-5 h-5 text-primary" /> Analyze a new repository
              </h2>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col md:flex-row gap-4">
                  <FormField
                    control={form.control}
                    name="github_url"
                    render={({ field }) => (
                      <FormItem className="flex-1 space-y-0">
                        <FormControl>
                          <Input placeholder="https://github.com/owner/repo" {...field} className="h-12 bg-background font-mono text-sm border-border" />
                        </FormControl>
                        <FormMessage className="mt-1" />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="branch"
                    render={({ field }) => (
                      <FormItem className="w-full md:w-32 space-y-0">
                        <FormControl>
                          <div className="relative">
                            <GitBranch className="absolute left-3 top-3.5 h-4 w-4 text-muted-foreground" />
                            <Input placeholder="main" {...field} className="h-12 pl-10 bg-background font-mono text-sm border-border" />
                          </div>
                        </FormControl>
                        <FormMessage className="mt-1" />
                      </FormItem>
                    )}
                  />
                  <Button type="submit" className="h-12 px-8 glow-primary font-medium" disabled={analyzeMutation.isPending}>
                    {analyzeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Code className="w-4 h-4 mr-2" />}
                    {analyzeMutation.isPending ? "Analyzing..." : "Analyze Codebase"}
                  </Button>
                </form>
              </Form>
            </div>
          </motion.div>

          {/* Repositories */}
          <motion.div variants={itemVariants} className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold tracking-tight">Recent Analysis</h3>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Search repos..." 
                  className="pl-9 h-10 bg-muted/50 border-transparent focus:border-border" 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            {isLoading ? (
              <div className="grid gap-6 md:grid-cols-2">
                {[1, 2, 3, 4].map((i) => (
                  <Card key={i} className="bg-card">
                    <CardHeader className="pb-4">
                      <Skeleton className="h-6 w-1/2 mb-2" />
                      <Skeleton className="h-4 w-1/4" />
                    </CardHeader>
                    <CardContent>
                      <div className="flex gap-2">
                        <Skeleton className="h-5 w-16" />
                        <Skeleton className="h-5 w-16" />
                      </div>
                    </CardContent>
                    <CardFooter className="pt-0 border-t border-border mt-4 py-4">
                      <Skeleton className="h-4 w-1/3" />
                    </CardFooter>
                  </Card>
                ))}
              </div>
            ) : error ? (
              <div className="p-8 text-center border border-destructive/20 rounded-xl bg-destructive/10 text-destructive">
                Failed to load repositories. Please try again.
              </div>
            ) : filteredRepos?.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-16 border border-border/50 rounded-2xl bg-card text-center">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-6">
                  <Github className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold mb-2">No repositories yet</h3>
                <p className="text-muted-foreground max-w-md mx-auto mb-8">
                  {searchTerm ? "No repositories match your search." : "Submit a GitHub repository URL above to generate your first architecture analysis."}
                </p>
                {searchTerm && (
                  <Button variant="outline" onClick={() => setSearchTerm("")}>Clear search</Button>
                )}
              </div>
            ) : (
              <div className="grid gap-6 md:grid-cols-2">
                {filteredRepos?.map((repo) => (
                  <Link key={repo.repo_id} href={`/repo/${repo.repo_id}`}>
                    <motion.div whileHover={{ y: -2 }} className="h-full">
                      <Card className="h-full cursor-pointer bg-card border-border hover:border-primary/40 transition-colors shadow-none group">
                        <CardHeader className="pb-4">
                          <div className="flex justify-between items-start mb-2">
                            <CardTitle className="font-mono text-lg font-bold group-hover:text-primary transition-colors">
                              {repo.owner}/{repo.name}
                            </CardTitle>
                            {getStatusBadge(repo.status)}
                          </div>
                          <CardDescription className="flex items-center gap-3 text-xs font-mono">
                            <span className="flex items-center text-muted-foreground"><GitBranch className="w-3.5 h-3.5 mr-1.5"/> {repo.branch}</span>
                            {repo.created_at && (
                              <span className="flex items-center text-muted-foreground"><Clock className="w-3.5 h-3.5 mr-1.5"/> {new Date(repo.created_at).toLocaleDateString()}</span>
                            )}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="pb-6">
                          <div className="flex flex-wrap gap-2">
                            {repo.languages?.slice(0, 4).map(lang => (
                              <Badge key={lang} variant="secondary" className="text-[10px] font-mono py-0 h-5 bg-muted text-muted-foreground">{lang}</Badge>
                            ))}
                            {repo.languages?.length > 4 && (
                              <Badge variant="secondary" className="text-[10px] font-mono py-0 h-5 bg-muted text-muted-foreground">+{repo.languages.length - 4}</Badge>
                            )}
                          </div>
                        </CardContent>
                        <CardFooter className="pt-4 pb-4 border-t border-border flex justify-between text-xs text-muted-foreground bg-muted/20">
                          <div className="flex gap-6">
                            <span><strong className="text-foreground font-medium">{repo.file_count?.toLocaleString() || 0}</strong> files</span>
                            <span><strong className="text-foreground font-medium">{repo.total_lines?.toLocaleString() || 0}</strong> lines</span>
                          </div>
                          <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:text-primary transition-all -translate-x-2 group-hover:translate-x-0" />
                        </CardFooter>
                      </Card>
                    </motion.div>
                  </Link>
                ))}
              </div>
            )}
          </motion.div>
          
        </motion.div>
      </main>
    </div>
  );
}
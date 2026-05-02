import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Plus, Github, Search, Clock, Code, GitBranch, ArrowRight, Loader2, XCircle, CheckCircle } from "lucide-react";
import { repoApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Skeleton } from "@/components/ui/skeleton";
import { Navbar } from "@/components/layout/Navbar";

const analyzeSchema = z.object({
  github_url: z.string().url("Must be a valid URL").includes("github.com", { message: "Must be a GitHub URL" }),
  branch: z.string().default("main"),
});

type AnalyzeFormValues = z.infer<typeof analyzeSchema>;

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();
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
      case 'pending': return <Badge variant="secondary" className="bg-gray-100 text-gray-800"><Clock className="w-3 h-3 mr-1"/> Pending</Badge>;
      case 'complete': return <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-200"><CheckCircle className="w-3 h-3 mr-1"/> Complete</Badge>;
      case 'failed': return <Badge variant="destructive" className="bg-red-100 text-red-800 hover:bg-red-200"><XCircle className="w-3 h-3 mr-1"/> Failed</Badge>;
      default: return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200"><Loader2 className="w-3 h-3 mr-1 animate-spin"/> {status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/50">
      <Navbar />
      
      <main className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="flex flex-col md:flex-row gap-8">
          
          <div className="w-full md:w-1/3">
            <Card className="sticky top-20 shadow-sm border-muted">
              <CardHeader className="pb-4">
                <CardTitle className="font-mono text-lg flex items-center gap-2">
                  <Github className="w-5 h-5" />
                  Analyze Repository
                </CardTitle>
                <CardDescription>
                  Submit a new GitHub repository for AI analysis
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Form {...form}>
                  <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <FormField
                      control={form.control}
                      name="github_url"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-xs font-mono text-muted-foreground uppercase tracking-wider">GitHub URL</FormLabel>
                          <FormControl>
                            <Input placeholder="https://github.com/owner/repo" {...field} className="font-mono text-sm" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="branch"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Branch</FormLabel>
                          <FormControl>
                            <div className="relative">
                              <GitBranch className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                              <Input placeholder="main" {...field} className="pl-9 font-mono text-sm" />
                            </div>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <Button type="submit" className="w-full font-mono gap-2" disabled={analyzeMutation.isPending}>
                      {analyzeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Code className="w-4 h-4" />}
                      {analyzeMutation.isPending ? "Starting Analysis..." : "Analyze Codebase"}
                    </Button>
                  </form>
                </Form>
              </CardContent>
            </Card>
          </div>

          <div className="w-full md:w-2/3 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold tracking-tight">Your Repositories</h2>
              <div className="relative w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Search repos..." 
                  className="pl-9" 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardHeader className="pb-2">
                      <Skeleton className="h-6 w-1/3 mb-2" />
                      <Skeleton className="h-4 w-1/4" />
                    </CardHeader>
                    <CardContent>
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-2/3" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : error ? (
              <div className="p-8 text-center border rounded-lg bg-red-50 text-red-800">
                Failed to load repositories. Please try again.
              </div>
            ) : filteredRepos?.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 border rounded-xl bg-white border-dashed text-center">
                <div className="w-12 h-12 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-4">
                  <Github className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No repositories found</h3>
                <p className="text-gray-500 max-w-sm mb-6">
                  {searchTerm ? "No repositories match your search." : "You haven't analyzed any repositories yet. Submit one using the form on the left."}
                </p>
                {searchTerm && (
                  <Button variant="outline" onClick={() => setSearchTerm("")}>Clear search</Button>
                )}
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredRepos?.map((repo) => (
                  <Card key={repo.repo_id} className="group hover:border-primary/50 transition-colors">
                    <CardHeader className="pb-3 flex flex-row items-start justify-between space-y-0">
                      <div>
                        <CardTitle className="flex items-center gap-2 text-lg">
                          <Link href={`/repo/${repo.repo_id}`} className="hover:text-primary hover:underline">
                            {repo.owner}/{repo.name}
                          </Link>
                          {getStatusBadge(repo.status)}
                        </CardTitle>
                        <CardDescription className="flex items-center gap-3 mt-2 text-xs">
                          <span className="flex items-center"><GitBranch className="w-3 h-3 mr-1"/> {repo.branch}</span>
                          {repo.created_at && (
                            <span className="flex items-center"><Clock className="w-3 h-3 mr-1"/> {new Date(repo.created_at).toLocaleDateString()}</span>
                          )}
                        </CardDescription>
                      </div>
                      <Link href={`/repo/${repo.repo_id}`}>
                        <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <ArrowRight className="w-4 h-4" />
                        </Button>
                      </Link>
                    </CardHeader>
                    <CardContent className="pb-3">
                      <div className="flex flex-wrap gap-2">
                        {repo.languages?.slice(0, 5).map(lang => (
                          <Badge key={lang} variant="outline" className="text-xs py-0 h-5 bg-slate-50">{lang}</Badge>
                        ))}
                        {repo.languages?.length > 5 && (
                          <Badge variant="outline" className="text-xs py-0 h-5 text-muted-foreground bg-slate-50">+{repo.languages.length - 5}</Badge>
                        )}
                      </div>
                    </CardContent>
                    <CardFooter className="pt-0 text-xs text-muted-foreground flex justify-between border-t px-6 py-3 bg-muted/20">
                      <div className="flex gap-4">
                        <span><strong className="text-foreground">{repo.file_count?.toLocaleString() || 0}</strong> files</span>
                        <span><strong className="text-foreground">{repo.total_lines?.toLocaleString() || 0}</strong> lines</span>
                      </div>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

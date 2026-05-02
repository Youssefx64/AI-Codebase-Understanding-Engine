import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { ArrowRight, Code2, GitBranch, ShieldAlert } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-[100dvh] flex flex-col">
      <main className="flex-1">
        <section className="relative overflow-hidden py-24 md:py-32">
          <div className="container relative z-10 mx-auto px-4 text-center">
            <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-sm text-primary mb-8">
              <span className="flex h-2 w-2 rounded-full bg-primary mr-2 animate-pulse" />
              Engine v2.0 is now live
            </div>
            
            <h1 className="mx-auto max-w-4xl font-mono text-5xl font-bold tracking-tighter sm:text-6xl md:text-7xl lg:text-8xl">
              Understand any codebase <span className="text-muted-foreground">in seconds.</span>
            </h1>
            
            <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground md:text-xl">
              Submit your GitHub repository and get instant architecture diagrams, dependency graphs, 
              bug reports, and refactoring suggestions powered by AI.
            </p>
            
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/register">
                <Button size="lg" className="w-full sm:w-auto gap-2 font-mono">
                  Start Analyzing <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="w-full sm:w-auto font-mono">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
          
          {/* Decorative background grid */}
          <div className="absolute inset-0 -z-10 h-full w-full bg-background bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
        </section>

        <section className="border-t bg-muted/40 py-24">
          <div className="container mx-auto px-4">
            <div className="grid gap-12 md:grid-cols-3">
              <div className="flex flex-col items-center text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <GitBranch className="h-8 w-8" />
                </div>
                <h3 className="text-xl font-bold font-mono">Dependency Graphs</h3>
                <p className="mt-2 text-muted-foreground">
                  Visualize how your files interact. Automatically generated node-link diagrams of your entire architecture.
                </p>
              </div>
              <div className="flex flex-col items-center text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <ShieldAlert className="h-8 w-8" />
                </div>
                <h3 className="text-xl font-bold font-mono">Bug Detection</h3>
                <p className="mt-2 text-muted-foreground">
                  Catch issues before they hit production. AI identifies logical flaws, security vulnerabilities, and code smells.
                </p>
              </div>
              <div className="flex flex-col items-center text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Code2 className="h-8 w-8" />
                </div>
                <h3 className="text-xl font-bold font-mono">Smart Refactoring</h3>
                <p className="mt-2 text-muted-foreground">
                  Get actionable suggestions to improve code quality, with side-by-side diffs and effort estimates.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

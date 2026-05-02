import { Link } from "wouter";
import { Button } from "@/components/ui/button";
import { ArrowRight, Code2, GitBranch, ShieldAlert, MessageSquare } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.06 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
  };

  return (
    <div className="min-h-[100dvh] flex flex-col bg-background">
      <main className="flex-1">
        
        {/* Section 1: Hero */}
        <section className="relative min-h-screen flex flex-col justify-center overflow-hidden py-24">
          <div className="absolute inset-0 -z-10 h-full w-full bg-background bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
          
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 -z-10 w-[800px] h-[400px]">
            <div className="absolute top-0 left-0 w-[400px] h-[400px] bg-primary/20 blur-[120px] rounded-full mix-blend-screen" />
            <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-cyan-500/10 blur-[100px] rounded-full mix-blend-screen" />
          </div>

          <div className="container max-w-7xl mx-auto px-6 z-10 flex flex-col items-center text-center">
            <motion.div initial="hidden" animate="visible" variants={containerVariants} className="flex flex-col items-center w-full max-w-4xl mx-auto">
              
              <motion.div variants={itemVariants} className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs text-primary mb-8 tracking-wide uppercase font-semibold">
                <span className="flex h-2 w-2 rounded-full bg-green-500 mr-2 animate-pulse" />
                Engine v2.0 is now live
              </motion.div>
              
              <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tighter text-foreground mb-6 leading-[1.1]">
                Understand <span className="gradient-text">any codebase</span> in seconds.
              </motion.h1>
              
              <motion.p variants={itemVariants} className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-10 leading-relaxed">
                Submit your GitHub repository and get instant architecture diagrams, dependency graphs, 
                bug reports, and refactoring suggestions powered by AI.
              </motion.p>
              
              <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center">
                <Link href="/register">
                  <Button size="lg" className="w-full sm:w-auto h-12 px-8 font-medium glow-primary text-base">
                    Start Analyzing <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/login">
                  <Button variant="ghost" size="lg" className="w-full sm:w-auto h-12 px-8 font-medium text-base border border-border/50 hover:bg-muted/50">
                    Sign In
                  </Button>
                </Link>
              </motion.div>
              
              <motion.div 
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
                className="mt-16 w-full max-w-2xl glass rounded-xl overflow-hidden shadow-2xl"
              >
                <div className="flex items-center px-4 py-3 bg-muted/30 border-b border-border/50 gap-2">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/80" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                    <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  </div>
                  <div className="flex-1 text-center font-mono text-[10px] text-muted-foreground/70 tracking-wider">
                    engine-cli analyze ./frontend
                  </div>
                </div>
                <div className="p-6 text-left font-mono text-sm leading-relaxed overflow-x-auto bg-[#0a0a0f]/50 text-slate-300">
                  <div className="text-primary mb-2">➜ analyzing repository...</div>
                  <div className="text-slate-400 mb-1">✔ Cloned 4,302 files in 1.2s</div>
                  <div className="text-slate-400 mb-1">✔ Parsed AST and built dependency graph in 4.8s</div>
                  <div className="text-slate-400 mb-4">✔ Generated vector embeddings for semantic search in 2.1s</div>
                  
                  <div className="text-cyan-400 mb-1">➜ Results:</div>
                  <div>• Found <span className="text-red-400">3 critical</span> and <span className="text-orange-400">12 high</span> severity issues</div>
                  <div>• Identified <span className="text-emerald-400">5 refactoring opportunities</span> (estimated effort: ~2 days)</div>
                  <div>• Generated 24 graph nodes and 89 edges</div>
                  
                  <div className="mt-4 text-muted-foreground animate-pulse">_</div>
                </div>
              </motion.div>

            </motion.div>
          </div>
        </section>

        {/* Section 2: Features */}
        <section className="py-24 md:py-32 bg-card/30 border-y border-border">
          <div className="container max-w-7xl mx-auto px-6">
            <motion.div 
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              variants={containerVariants}
              className="grid gap-8 md:grid-cols-2 lg:grid-cols-4"
            >
              {[
                {
                  title: "Dependency Graphs",
                  desc: "Visualize how your files interact. Automatically generated node-link diagrams of your architecture.",
                  icon: <GitBranch className="h-6 w-6 text-primary" />
                },
                {
                  title: "Bug Detection",
                  desc: "Catch issues before production. AI identifies logical flaws, vulnerabilities, and smells.",
                  icon: <ShieldAlert className="h-6 w-6 text-primary" />
                },
                {
                  title: "Smart Refactoring",
                  desc: "Get actionable suggestions to improve code quality, with side-by-side diffs and effort estimates.",
                  icon: <Code2 className="h-6 w-6 text-primary" />
                },
                {
                  title: "RAG Q&A Chat",
                  desc: "Ask anything about your codebase in plain English. Powered by vector search and GPT-4.",
                  icon: <MessageSquare className="h-6 w-6 text-primary" />
                }
              ].map((feature, i) => (
                <motion.div key={i} variants={itemVariants} className="flex flex-col items-start p-8 rounded-2xl bg-card border border-border/50 hover:-translate-y-1 transition-transform duration-300">
                  <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 border border-primary/20">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-3">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.desc}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Section 3: How it Works */}
        <section className="py-24 md:py-32 relative overflow-hidden">
          <div className="container max-w-7xl mx-auto px-6 relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">How it works</h2>
              <p className="text-muted-foreground text-lg">Three steps to complete codebase clarity.</p>
            </div>
            
            <div className="relative">
              <div className="hidden md:block absolute top-1/2 left-[10%] right-[10%] h-[1px] bg-border -translate-y-1/2" />
              <div className="grid gap-12 md:gap-6 md:grid-cols-3 relative">
                {[
                  { step: "01", title: "Submit Repository", desc: "Paste any public or private GitHub URL." },
                  { step: "02", title: "AI Analysis", desc: "Engine clones, parses ASTs, and embeds code." },
                  { step: "03", title: "Explore Insights", desc: "Navigate graphs, review issues, and chat with your repo." }
                ].map((s, i) => (
                  <div key={i} className="flex flex-col items-center text-center relative">
                    <div className="w-10 h-10 rounded-full bg-background border border-primary text-primary flex items-center justify-center font-mono font-bold text-sm mb-6 z-10 shadow-[0_0_15px_rgba(var(--primary),0.2)]">
                      {s.step}
                    </div>
                    <h4 className="text-xl font-semibold mb-2">{s.title}</h4>
                    <p className="text-sm text-muted-foreground max-w-[250px] mx-auto">{s.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>
      
      {/* Section 4: Footer */}
      <footer className="border-t border-border/50 bg-card py-12">
        <div className="container max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 font-mono font-semibold text-sm text-muted-foreground">
            <div className="w-5 h-5 rounded bg-primary/20 text-primary flex items-center justify-center text-[10px]">⬡</div>
            © 2026 CodeEngine
          </div>
          <div className="flex gap-6 text-sm text-muted-foreground">
            <a href="#" className="hover:text-primary transition-colors">Docs</a>
            <a href="#" className="hover:text-primary transition-colors">GitHub</a>
            <a href="#" className="hover:text-primary transition-colors">Twitter</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
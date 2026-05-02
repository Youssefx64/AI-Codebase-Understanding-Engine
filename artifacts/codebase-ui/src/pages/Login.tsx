import { Link, useLocation } from "wouter";
import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function Login() {
  const [, setLocation] = useLocation();
  const { setUser } = useAuthStore();

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const loginMutation = useMutation({
    mutationFn: (data: LoginFormValues) => authApi.login(data),
    onSuccess: (data) => {
      setUser(data);
      toast.success("Logged in successfully");
      setLocation("/dashboard");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to login");
    },
  });

  function onSubmit(data: LoginFormValues) {
    loginMutation.mutate(data);
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.07 } }
  };
  const itemVariants = {
    hidden: { opacity: 0, y: 16 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } }
  };

  return (
    <div className="flex min-h-screen bg-background">
      
      {/* Left Panel */}
      <div className="hidden md:flex w-1/2 bg-card/50 border-r border-border relative flex-col items-center justify-center overflow-hidden">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-primary/10 blur-[120px] rounded-full" />
        
        <div className="relative z-10 w-full max-w-md px-8">
          <Link href="/" className="inline-flex items-center gap-3 font-mono font-semibold tracking-tight text-xl mb-12">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xl">
              ⬡
            </div>
            CodeEngine
          </Link>

          <div className="glass p-8 rounded-2xl border border-border">
            <div className="text-xl font-medium leading-relaxed text-foreground mb-6">
              "CodeEngine found 3 critical issues in our auth layer in under 2 minutes. It's fundamentally changed how we do code reviews."
            </div>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center font-mono text-sm border border-border">
                JD
              </div>
              <div>
                <div className="font-semibold text-sm">Jane Doe</div>
                <div className="text-xs text-muted-foreground">Staff Engineer, TechCorp</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-6">
        <motion.div 
          initial="hidden" animate="visible" variants={containerVariants}
          className="w-full max-w-[360px] flex flex-col"
        >
          <motion.div variants={itemVariants} className="md:hidden flex items-center gap-2 font-mono font-semibold tracking-tight text-sm mb-8">
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              ⬡
            </div>
            CodeEngine
          </motion.div>

          <motion.div variants={itemVariants} className="mb-8">
            <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-2xl mb-6 md:flex hidden">
              ⬡
            </div>
            <h1 className="text-2xl font-semibold tracking-tight mb-2">Welcome back</h1>
            <p className="text-sm text-muted-foreground">
              Sign in to your account to continue
            </p>
          </motion.div>
          
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <motion.div variants={itemVariants}>
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Email</FormLabel>
                      <FormControl>
                        <Input placeholder="name@example.com" className="h-11 bg-transparent" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </motion.div>
              <motion.div variants={itemVariants}>
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Password</FormLabel>
                      <FormControl>
                        <Input type="password" placeholder="••••••••" className="h-11 bg-transparent" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </motion.div>
              <motion.div variants={itemVariants} className="pt-4">
                <Button className="w-full h-11 glow-primary font-medium" type="submit" disabled={loginMutation.isPending}>
                  {loginMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Sign In
                </Button>
              </motion.div>
            </form>
          </Form>
          
          <motion.p variants={itemVariants} className="mt-8 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link href="/register" className="text-primary hover:text-primary/80 font-medium transition-colors">
              Sign up
            </Link>
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
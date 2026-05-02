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

const registerSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function Register() {
  const [, setLocation] = useLocation();
  const { setUser } = useAuthStore();

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", email: "", password: "" },
  });

  const registerMutation = useMutation({
    mutationFn: (data: RegisterFormValues) => authApi.register(data),
    onSuccess: (data) => {
      setUser(data);
      toast.success("Account created successfully");
      setLocation("/dashboard");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create account");
    },
  });

  function onSubmit(data: RegisterFormValues) {
    registerMutation.mutate(data);
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
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-cyan-500/10 blur-[120px] rounded-full" />
        
        <div className="relative z-10 w-full max-w-md px-8">
          <Link href="/" className="inline-flex items-center gap-3 font-mono font-semibold tracking-tight text-xl mb-12">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xl">
              ⬡
            </div>
            CodeEngine
          </Link>

          <div className="glass p-8 rounded-2xl border border-border">
            <h3 className="text-lg font-semibold mb-6">Platform Scale</h3>
            <div className="space-y-6">
              <div>
                <div className="text-3xl font-bold font-mono tracking-tight text-foreground">2,400+</div>
                <div className="text-sm text-muted-foreground mt-1">Repositories analyzed</div>
              </div>
              <div>
                <div className="text-3xl font-bold font-mono tracking-tight text-foreground">89K</div>
                <div className="text-sm text-muted-foreground mt-1">Critical issues caught</div>
              </div>
              <div>
                <div className="text-3xl font-bold font-mono tracking-tight text-foreground">12K</div>
                <div className="text-sm text-muted-foreground mt-1">Developers shipped faster</div>
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
            <h1 className="text-2xl font-semibold tracking-tight mb-2">Create an account</h1>
            <p className="text-sm text-muted-foreground">
              Enter your details to get started
            </p>
          </motion.div>
          
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <motion.div variants={itemVariants}>
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Username</FormLabel>
                      <FormControl>
                        <Input placeholder="johndoe" className="h-11 bg-transparent" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </motion.div>
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
                <Button className="w-full h-11 glow-primary font-medium" type="submit" disabled={registerMutation.isPending}>
                  {registerMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Sign Up
                </Button>
              </motion.div>
            </form>
          </Form>
          
          <motion.p variants={itemVariants} className="mt-8 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
              Sign in
            </Link>
          </motion.p>
        </motion.div>
      </div>
    </div>
  );
}
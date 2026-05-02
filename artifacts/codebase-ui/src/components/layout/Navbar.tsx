import { useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { motion } from "framer-motion";

export function Navbar() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const [, setLocation] = useLocation();
  const { theme, setTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 0);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleLogout = () => {
    logout();
    setLocation("/");
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return (
    <motion.nav 
      initial={{ y: -8, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={`h-[56px] sticky top-0 z-50 glass flex items-center transition-shadow ${scrolled ? 'shadow-[0_1px_0_0_hsl(var(--border))]' : ''}`}
    >
      <div className="container max-w-7xl mx-auto px-6 flex items-center justify-between w-full">
        <Link href="/" className="flex items-center gap-2 font-mono font-semibold tracking-tight text-sm">
          <div className="w-[28px] h-[28px] rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
            ⬡
          </div>
          CodeEngine
        </Link>

        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={toggleTheme} className="h-8 w-8 rounded-md">
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme</span>
          </Button>

          {isAuthenticated ? (
            <>
              <Link href="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                Dashboard
              </Link>
              <div className="h-4 w-px bg-border"></div>
              <div className="w-[28px] h-[28px] rounded-full bg-primary/20 text-primary flex items-center justify-center text-xs font-mono uppercase">
                {user?.username?.substring(0, 2) || "U"}
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout} className="text-xs h-8">
                Log out
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm" className="text-xs h-8">Log in</Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="text-xs h-8">Sign up</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
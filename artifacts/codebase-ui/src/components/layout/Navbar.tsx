import { useEffect } from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";

export function Navbar() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const [, setLocation] = useLocation();

  const handleLogout = () => {
    logout();
    setLocation("/");
  };

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container flex h-14 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-mono font-semibold tracking-tight">
          <div className="size-6 rounded bg-primary text-primary-foreground flex items-center justify-center text-xs">
            {"{ }"}
          </div>
          CodeEngine
        </Link>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link href="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground">
                Dashboard
              </Link>
              <div className="h-4 w-px bg-border"></div>
              <span className="text-sm text-muted-foreground">{user?.username}</span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" size="sm">Log in</Button>
              </Link>
              <Link href="/register">
                <Button size="sm">Sign up</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

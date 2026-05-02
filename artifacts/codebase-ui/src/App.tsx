import { useEffect } from "react";
import { Switch, Route, Router as WouterRouter, Redirect, useLocation } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "next-themes";
import { useAuthStore } from "@/lib/auth-store";

// Pages
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import RepoDetails from "@/pages/RepoDetails";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient();

// Protected Route Wrapper
const ProtectedRoute = ({ component: Component, ...rest }: any) => {
  const { isAuthenticated } = useAuthStore();
  const [location] = useLocation();

  if (!isAuthenticated) {
    return <Redirect to={`/login?returnTo=${encodeURIComponent(location)}`} />;
  }

  return <Component {...rest} />;
};

function Router() {
  const { isAuthenticated } = useAuthStore();

  return (
    <Switch>
      <Route path="/">
        {isAuthenticated ? <Redirect to="/dashboard" /> : <Home />}
      </Route>
      <Route path="/login" component={Login} />
      <Route path="/register" component={Register} />
      
      <Route path="/dashboard">
        <ProtectedRoute component={Dashboard} />
      </Route>
      <Route path="/repo/:id">
        {params => <ProtectedRoute component={RepoDetails} id={params.id} />}
      </Route>
      
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  const { loadFromStorage } = useAuthStore();

  // Load auth state from local storage on initial mount
  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <ThemeProvider defaultTheme="dark" attribute="class">
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <Router />
          </WouterRouter>
          <Toaster position="bottom-right" theme="dark" />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
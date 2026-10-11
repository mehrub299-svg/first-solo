import { useAuth } from "./auth/AuthContext";
import AuthPage from "./pages/AuthPage";
import HomePage from "./pages/HomePage";
import { WorkspaceProvider } from "./workspace/WorkspaceContext";

function Loading({ children }) {
  return <div className="grid min-h-screen place-items-center text-muted">{children}</div>;
}

export default function App() {
  const { token, user, booting } = useAuth();

  if (booting) return <Loading>Restoring your session…</Loading>;
  if (!token) return <AuthPage />;
  if (!user) return <Loading>Loading your account…</Loading>;

  return (
    <WorkspaceProvider key={user.id}>
      <HomePage />
    </WorkspaceProvider>
  );
}
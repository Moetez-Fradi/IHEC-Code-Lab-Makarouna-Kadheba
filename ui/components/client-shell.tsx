"use client";

import { usePathname } from "next/navigation";
import { AuthProvider } from "@/lib/auth-context";
import { RequireAuth } from "@/components/require-auth";
import { Sidebar } from "@/components/sidebar";
import { MobileNav } from "@/components/mobile-nav";
import { ChatbotBubble } from "@/components/chatbot-bubble";

const PUBLIC_ROUTES = ["/login", "/signup"];

export function ClientShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.includes(pathname);

  return (
    <AuthProvider>
      {isPublic ? (
        children
      ) : (
        <RequireAuth>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
          <MobileNav />
          <ChatbotBubble />
        </RequireAuth>
      )}
    </AuthProvider>
  );
}

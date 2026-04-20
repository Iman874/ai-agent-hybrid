import { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { ChatArea } from "@/components/chat/ChatArea";
import { GenerateContainer } from "@/components/generate/GenerateContainer";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useKeyboard } from "@/hooks/useKeyboard";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

export function AppLayout() {
  const sidebarOpen = useUIStore(s => s.sidebarOpen);
  const activeTool = useUIStore(s => s.activeTool);
  const toggleSidebar = useUIStore(s => s.toggleSidebar);
  const [isMobile, setIsMobile] = useState(false);
  
  useWebSocket(); // Boot up websocket on layout mount
  useKeyboard(); // Boot up keyboard shortcuts

  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile && useUIStore.getState().sidebarOpen) {
        useUIStore.getState().toggleSidebar();
      }
    };
    
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar - Mobile vs Desktop */}
      {isMobile ? (
        <Sheet open={sidebarOpen} onOpenChange={() => toggleSidebar()}>
          <SheetContent side="left" className="w-[80%] max-w-[300px] p-0 border-r-0">
            <SheetTitle className="sr-only">Menu Sidebar</SheetTitle>
            <div className="w-full h-full"><Sidebar /></div>
          </SheetContent>
        </Sheet>
      ) : (
        <aside
          className={cn(
            "flex-shrink-0 border-border bg-sidebar transition-all duration-300 overflow-hidden",
            sidebarOpen ? "w-64 border-r" : "w-0 border-r-0"
          )}
        >
          <div className="w-64 h-full"><Sidebar /></div>
        </aside>
      )}

      {/* Main area */}
      <main className="flex-1 flex flex-col min-w-0">
        <Header />
        <div className="flex-1 overflow-hidden">
          {activeTool === "chat" ? (
            <ChatArea />
          ) : (
            <div className="h-full overflow-y-auto">
              <GenerateContainer />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

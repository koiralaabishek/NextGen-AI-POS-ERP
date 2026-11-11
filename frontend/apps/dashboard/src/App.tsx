import React, { useState } from "react";
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Boxes,
  Users,
  BookOpen,
  Bot,
  Settings,
  TrendingUp,
  AlertTriangle,
  Receipt,
  Building2,
  ChevronDown,
  ArrowUpRight,
  Send,
  Sparkles,
} from "lucide-react";
import { SalesView } from "./components/SalesView";
import { AccountingView } from "./components/AccountingView";
import { InventoryView } from "./components/InventoryView";
import { CustomersView } from "./components/CustomersView";
import { ProductsView } from "./components/ProductsView";

export function App() {
  const [currentTab, setCurrentTab] = useState<
    "dashboard" | "ai-assistant" | "sales" | "products" | "inventory" | "accounting" | "customers"
  >("dashboard");
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiChat, setAiChat] = useState<{ sender: "user" | "ai"; text: string; time: string }[]>([
    {
      sender: "ai",
      text: "नमस्ते! I am your NextGen AI Business Assistant. You can ask me questions about your sales, profit margins, top products, or inventory in Nepali or English.",
      time: "10:30 AM",
    },
  ]);

  const handleSendAi = (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;

    const userMsg = aiPrompt;
    setAiChat((prev) => [
      ...prev,
      { sender: "user", text: userMsg, time: "Just now" },
    ]);
    setAiPrompt("");

    // Simulate smart AI business insight response
    setTimeout(() => {
      let reply = "आज तपाईंको पसलमा सबैभन्दा धेरै नाफा भएको उत्पादन Shakti Wheat Flour 5kg हो। Gross profit: Rs. 3,600 (24 units sold). Low stock alert: DDC Milk (5 units remaining).";
      if (userMsg.toLowerCase().includes("top") || userMsg.toLowerCase().includes("बढी")) {
        reply = "Today's top 3 performing items:\n1. Himalayan Basmati Rice 25kg (Rs. 28,500)\n2. Shakti Wheat Flour 5kg (Rs. 11,400)\n3. Dhara Mustard Oil 1L (Rs. 4,900)";
      }
      setAiChat((prev) => [
        ...prev,
        { sender: "ai", text: reply, time: "Just now" },
      ]);
    }, 700);
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/60 flex flex-col justify-between p-4">
        <div>
          {/* Organization Switcher */}
          <div className="flex items-center justify-between p-3 bg-slate-900 border border-slate-800 rounded-xl mb-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-sm">
                N
              </div>
              <div>
                <h3 className="text-sm font-bold leading-tight">Namaste Mart</h3>
                <span className="text-[11px] text-blue-400 font-medium">Kathmandu HQ</span>
              </div>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {[
              { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
              { id: "ai-assistant", label: "AI Copilot", icon: Bot, badge: "AI" },
              { id: "sales", label: "Sales & Invoices", icon: Receipt },
              { id: "products", label: "Products & SKU", icon: Package },
              { id: "inventory", label: "Inventory Ledger", icon: Boxes },
              { id: "accounting", label: "Accounts & VAT", icon: BookOpen },
              { id: "customers", label: "Customers & Khata", icon: Users },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id as any)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                    isActive
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 font-bold">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Quick Launch POS Terminal */}
        <div className="pt-4 border-t border-slate-800">
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noreferrer"
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-emerald-600 hover:bg-emerald-500 rounded-xl font-bold text-sm text-white shadow-lg transition"
          >
            <ShoppingCart className="w-4 h-4" />
            <span>Open POS Terminal</span>
            <ArrowUpRight className="w-4 h-4" />
          </a>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        {/* Top Header */}
        <header className="px-8 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80 backdrop-blur sticky top-0 z-10">
          <div>
            <h1 className="text-xl font-bold capitalize">
              {currentTab === "dashboard" ? "Business Workspace Overview" : currentTab.replace("-", " ")}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">Real-time multi-tenant SaaS analytics & ERP ledger</p>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              Fiscal Year: <b className="text-white">2083/84 (Nepal)</b>
            </span>
          </div>
        </header>

        {/* Dynamic Tab Body */}
        <div className="p-8 flex-1">
          {currentTab === "dashboard" && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { title: "Today's Revenue", val: "Rs. 1,48,250", change: "+14.2% vs yesterday", icon: TrendingUp, color: "text-emerald-400" },
                  { title: "Invoices Issued", val: "142 Bills", change: "100% gapless IRD compliant", icon: Receipt, color: "text-blue-400" },
                  { title: "Output VAT (13%)", val: "Rs. 19,272.50", change: "Accrued to Liability 2200", icon: BookOpen, color: "text-purple-400" },
                  { title: "Low Stock Warnings", val: "4 Variants", change: "Under reorder threshold", icon: AlertTriangle, color: "text-amber-400" },
                ].map((kpi, idx) => {
                  const Icon = kpi.icon;
                  return (
                    <div key={idx} className="p-5 bg-slate-900 border border-slate-800 rounded-2xl">
                      <div className="flex items-center justify-between text-slate-400">
                        <span className="text-xs font-medium">{kpi.title}</span>
                        <Icon className={`w-4 h-4 ${kpi.color}`} />
                      </div>
                      <div className="text-2xl font-bold text-white mt-2 font-mono">{kpi.val}</div>
                      <div className="text-[11px] text-slate-500 mt-1">{kpi.change}</div>
                    </div>
                  );
                })}
              </div>

              {/* Quick AI Business Summary Banner */}
              <div className="p-6 bg-gradient-to-r from-blue-950/60 to-purple-950/60 border border-blue-900/50 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-600 rounded-xl text-white">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-white">Daily AI Executive Brief</h3>
                    <p className="text-xs text-slate-300 mt-0.5 max-w-xl">
                      Wheat flour and mustard oil experienced a 28% velocity surge today. Stock of DDC Pasteurised Milk will run out in approximately 3 hours based on current checkout velocity.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setCurrentTab("ai-assistant")}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded-xl text-xs font-semibold text-white transition"
                >
                  Consult AI Copilot
                </button>
              </div>
            </div>
          )}

          {currentTab === "ai-assistant" && (
            <div className="h-[calc(100vh-220px)] flex flex-col bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center gap-2 bg-slate-950/50">
                <Bot className="w-5 h-5 text-blue-400" />
                <h3 className="font-bold text-sm">Tenant Business Copilot (Nepali / English)</h3>
              </div>

              {/* Chat Log */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {aiChat.map((m, i) => (
                  <div
                    key={i}
                    className={`flex ${m.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-lg p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                        m.sender === "user"
                          ? "bg-blue-600 text-white rounded-tr-none"
                          : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none"
                      }`}
                    >
                      {m.text}
                      <span className="block text-[10px] opacity-60 mt-1">{m.time}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSendAi} className="p-4 bg-slate-950 border-t border-slate-800 flex gap-3">
                <input
                  type="text"
                  placeholder="Ask a question (e.g. मेरो पसलमा आज सबैभन्दा बढी नाफा भएको सामान कुन हो?)..."
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sm focus:outline-none focus:border-blue-500"
                />
                <button
                  type="submit"
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold text-sm flex items-center gap-2 transition"
                >
                  <Send className="w-4 h-4" />
                  <span>Send</span>
                </button>
              </form>
            </div>
          )}
          {currentTab === "sales" && <SalesView />}
          {currentTab === "products" && <ProductsView />}
          {currentTab === "inventory" && <InventoryView />}
          {currentTab === "accounting" && <AccountingView />}
          {currentTab === "customers" && <CustomersView />}
        </div>
      </main>
    </div>
  );
}

export default App;

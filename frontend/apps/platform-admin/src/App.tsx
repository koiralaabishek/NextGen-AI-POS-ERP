import React, { useState } from "react";
import {
  ShieldAlert,
  Building2,
  CreditCard,
  Activity,
  Users,
  Server,
  Database,
  Cpu,
  Layers,
  Search,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Plus,
  ArrowUpRight,
  Sparkles,
  Lock,
  Globe,
  Radio,
  FileText,
} from "lucide-react";

interface TenantRecord {
  id: string;
  name: string;
  slug: string;
  business_type: "supermarket" | "retail" | "restaurant" | "wholesale";
  branches_count: number;
  plan: "Starter" | "Professional" | "Enterprise";
  mrr: number;
  status: "ACTIVE" | "TRIAL" | "SUSPENDED";
  joined: string;
}

const SAMPLE_TENANTS: TenantRecord[] = [
  { id: "t1", name: "Namaste Mart Pvt. Ltd.", slug: "namaste-mart", business_type: "supermarket", branches_count: 3, plan: "Enterprise", mrr: 15000, status: "ACTIVE", joined: "2026-08-14" },
  { id: "t2", name: "Himalayan Wholesale Distributors", slug: "himalayan-wholesale", business_type: "wholesale", branches_count: 5, plan: "Enterprise", mrr: 15000, status: "ACTIVE", joined: "2026-09-02" },
  { id: "t3", name: "Patan Fine Fabrics & Retail", slug: "patan-fabrics", business_type: "retail", branches_count: 1, plan: "Starter", mrr: 2500, status: "ACTIVE", joined: "2026-10-10" },
  { id: "t4", name: "Thamel Rooftop Cafe & Bar", slug: "thamel-cafe", business_type: "restaurant", branches_count: 2, plan: "Professional", mrr: 6500, status: "ACTIVE", joined: "2026-10-18" },
  { id: "t5", name: "Everest Organic Foods", slug: "everest-organic", business_type: "retail", branches_count: 1, plan: "Starter", mrr: 2500, status: "TRIAL", joined: "2026-11-04" },
];

export function App() {
  const [tab, setTab] = useState<"overview" | "tenants" | "subscriptions" | "health" | "logs">("overview");
  const [tenants, setTenants] = useState<TenantRecord[]>(SAMPLE_TENANTS);
  const [search, setSearch] = useState("");
  const [newTenantModal, setNewTenantModal] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgType, setNewOrgType] = useState<"supermarket" | "retail" | "restaurant" | "wholesale">("retail");
  const [newOrgPlan, setNewOrgPlan] = useState<"Starter" | "Professional" | "Enterprise">("Starter");
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const filteredTenants = tenants.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.slug.toLowerCase().includes(search.toLowerCase()) ||
      t.business_type.toLowerCase().includes(search.toLowerCase())
  );

  const handleToggleStatus = (id: string) => {
    setTenants((prev) =>
      prev.map((t) => {
        if (t.id === id) {
          const nextStatus = t.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE";
          setActionNotice(`Tenant ${t.name} status updated to ${nextStatus}.`);
          return { ...t, status: nextStatus };
        }
        return t;
      })
    );
    setTimeout(() => setActionNotice(null), 4000);
  };

  const handleProvisionTenant = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;

    const slug = newOrgName.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-");
    const mrr = newOrgPlan === "Enterprise" ? 15000 : newOrgPlan === "Professional" ? 6500 : 2500;
    const newRecord: TenantRecord = {
      id: `t-${Date.now().toString().slice(-4)}`,
      name: newOrgName,
      slug,
      business_type: newOrgType,
      branches_count: 1,
      plan: newOrgPlan,
      mrr,
      status: "ACTIVE",
      joined: new Date().toISOString().split("T")[0],
    };

    setTenants([newRecord, ...tenants]);
    setNewTenantModal(false);
    setNewOrgName("");
    setActionNotice(`Tenant ${newRecord.name} provisioned successfully with isolated database schema!`);
    setTimeout(() => setActionNotice(null), 5000);
  };

  const totalMrr = tenants.reduce((acc, cur) => acc + (cur.status === "ACTIVE" ? cur.mrr : 0), 0);
  const activeTenantsCount = tenants.filter((t) => t.status === "ACTIVE").length;

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Platform Admin Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/80 flex flex-col justify-between p-4">
        <div>
          {/* Platform Branding */}
          <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-800/50 rounded-xl mb-6">
            <div className="p-2 bg-blue-600 rounded-lg text-white">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight text-white">NextGen Cloud</h2>
              <span className="text-[10px] text-blue-400 font-semibold tracking-wider uppercase">
                Platform Admin
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {[
              { id: "overview", label: "SaaS Command Center", icon: Activity },
              { id: "tenants", label: "Tenants & Organizations", icon: Building2, count: tenants.length },
              { id: "subscriptions", label: "Plans & MRR Billing", icon: CreditCard },
              { id: "health", label: "Infrastructure Health", icon: Server },
              { id: "logs", label: "Audit & Security Logs", icon: FileText },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = tab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setTab(item.id as any)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
                    isActive
                      ? "bg-blue-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.count !== undefined && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-bold">
                      {item.count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Global Cluster Region Info */}
        <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-[11px] space-y-1 text-slate-400">
          <div className="flex items-center gap-2 text-emerald-400 font-bold">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Region: Kathmandu (ktm-dc-01)</span>
          </div>
          <div>Multi-tenant Isolation: Strict ORM Scope</div>
          <div className="text-[10px] text-slate-500 font-mono">v1.0.0-rc2 (Production)</div>
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        {/* Header */}
        <header className="px-8 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/80 backdrop-blur sticky top-0 z-10">
          <div>
            <h1 className="text-xl font-bold capitalize">
              {tab === "overview" ? "SaaS Global Overview" : tab.replace("-", " ")}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Antigravity NextGen SaaS Multi-Tenant Management Engine
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setNewTenantModal(true)}
              className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow transition"
            >
              <Plus className="w-4 h-4" />
              <span>Provision Tenant</span>
            </button>
          </div>
        </header>

        {actionNotice && (
          <div className="mx-8 mt-4 p-4 bg-blue-950/70 border border-blue-800 rounded-xl text-xs text-blue-300 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-blue-400" />
            <span>{actionNotice}</span>
          </div>
        )}

        {/* Dynamic Tab Body */}
        <div className="p-8 flex-1 space-y-6">
          {tab === "overview" && (
            <div className="space-y-6">
              {/* SaaS Top Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Monthly Recurring Revenue", val: `Rs. ${totalMrr.toLocaleString()}`, change: "+24.5% MoM", icon: CreditCard, color: "text-emerald-400" },
                  { label: "Active Tenant Organizations", val: `${activeTenantsCount} Stores`, change: "100% tenant-isolated", icon: Building2, color: "text-blue-400" },
                  { label: "Total POS Terminals Online", val: "12 Terminals", change: "Real-time sync active", icon: Globe, color: "text-purple-400" },
                  { label: "System Uptime & Health", val: "99.98%", change: "Zero reported outages", icon: Activity, color: "text-teal-400" },
                ].map((kpi, idx) => {
                  const Icon = kpi.icon;
                  return (
                    <div key={idx} className="p-5 bg-slate-900 border border-slate-800 rounded-2xl">
                      <div className="flex items-center justify-between text-slate-400">
                        <span className="text-xs font-medium">{kpi.label}</span>
                        <Icon className={`w-4 h-4 ${kpi.color}`} />
                      </div>
                      <div className="text-2xl font-bold text-white mt-2 font-mono">{kpi.val}</div>
                      <div className="text-[11px] text-slate-500 mt-1">{kpi.change}</div>
                    </div>
                  );
                })}
              </div>

              {/* Tenants Quick List & System Status Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Active Tenants Column */}
                <div className="lg:col-span-2 p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-blue-400" />
                      <span>Top Performing Tenants</span>
                    </h3>
                    <button onClick={() => setTab("tenants")} className="text-xs text-blue-400 hover:underline">
                      View All
                    </button>
                  </div>

                  <div className="space-y-2">
                    {tenants.map((t) => (
                      <div
                        key={t.id}
                        className="p-3 bg-slate-950 border border-slate-800/80 rounded-xl flex items-center justify-between text-xs hover:border-slate-700 transition"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 font-bold flex items-center justify-center">
                            {t.name[0]}
                          </div>
                          <div>
                            <div className="font-bold text-white">{t.name}</div>
                            <div className="text-[11px] text-slate-400 capitalize">
                              {t.business_type} · {t.branches_count} branch(es) · {t.plan} Plan
                            </div>
                          </div>
                        </div>

                        <div className="text-right font-mono">
                          <div className="font-bold text-emerald-400">Rs. {t.mrr.toLocaleString()} /mo</div>
                          <span className={`text-[10px] font-sans font-bold px-2 py-0.5 rounded-full ${
                            t.status === "ACTIVE"
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                              : "bg-amber-950 text-amber-400 border border-amber-800"
                          }`}>
                            {t.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Infrastructure Live Heartbeat Column */}
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Server className="w-4 h-4 text-emerald-400" />
                    <span>Live Cluster Services</span>
                  </h3>

                  <div className="space-y-3 text-xs">
                    {[
                      { name: "Django DRF API Gateway", status: "Operational", ping: "24ms", icon: Layers },
                      { name: "PostgreSQL 18 Multi-Tenant", status: "Healthy", ping: "8ms", icon: Database },
                      { name: "Redis 7 & Celery Workers", status: "Operational", ping: "2ms", icon: Cpu },
                      { name: "FastAPI AI Microservice", status: "Operational", ping: "42ms", icon: Sparkles },
                      { name: "eSewa & Khalti Integrations", status: "100% Up", ping: "68ms", icon: CreditCard },
                    ].map((svc, i) => {
                      const Icon = svc.icon;
                      return (
                        <div key={i} className="p-3 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <Icon className="w-4 h-4 text-slate-400" />
                            <div>
                              <div className="font-semibold text-white">{svc.name}</div>
                              <div className="text-[10px] text-slate-500 font-mono">RTT: {svc.ping}</div>
                            </div>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                            {svc.status}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {tab === "tenants" && (
            <div className="space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search tenant name, slug, industry..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-80 focus:outline-none focus:border-blue-500 text-slate-200"
                  />
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="px-5 py-3.5">Organization</th>
                      <th className="px-5 py-3.5">Industry Segment</th>
                      <th className="px-5 py-3.5">Branches</th>
                      <th className="px-5 py-3.5">SaaS Plan</th>
                      <th className="px-5 py-3.5 text-right">MRR (NPR)</th>
                      <th className="px-5 py-3.5 text-center">Status</th>
                      <th className="px-5 py-3.5 text-right">Joined</th>
                      <th className="px-5 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {filteredTenants.map((t) => (
                      <tr key={t.id} className="hover:bg-slate-800/30 transition">
                        <td className="px-5 py-3.5">
                          <div className="font-bold text-white font-sans">{t.name}</div>
                          <div className="text-[10px] text-slate-500">/{t.slug}</div>
                        </td>
                        <td className="px-5 py-3.5 font-sans capitalize text-slate-300">{t.business_type}</td>
                        <td className="px-5 py-3.5 text-slate-300">{t.branches_count}</td>
                        <td className="px-5 py-3.5 font-sans">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">
                            {t.plan}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right font-bold text-emerald-400">
                          Rs. {t.mrr.toLocaleString()}
                        </td>
                        <td className="px-5 py-3.5 text-center font-sans">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            t.status === "ACTIVE"
                              ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                              : t.status === "TRIAL"
                              ? "bg-blue-950 text-blue-400 border border-blue-800"
                              : "bg-red-950 text-red-400 border border-red-800"
                          }`}>
                            {t.status}
                          </span>
                        </td>
                        <td className="px-5 py-3.5 text-right text-slate-400">{t.joined}</td>
                        <td className="px-5 py-3.5 text-right font-sans">
                          <button
                            onClick={() => handleToggleStatus(t.id)}
                            className={`px-3 py-1 rounded-lg text-[11px] font-semibold transition border ${
                              t.status === "ACTIVE"
                                ? "bg-red-950/60 hover:bg-red-900 border-red-800 text-red-300"
                                : "bg-emerald-950/60 hover:bg-emerald-900 border-emerald-800 text-emerald-300"
                            }`}
                          >
                            {t.status === "ACTIVE" ? "Suspend" : "Activate"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "subscriptions" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  {
                    name: "Starter Plan",
                    price: "Rs. 2,500 / mo",
                    desc: "Perfect for single-counter retail shops & mini marts",
                    features: ["1 Branch, 2 POS Cashiers", "Offline Dexie.js POS", "13% Nepal VAT Billing", "50 AI Monthly Credits"],
                  },
                  {
                    name: "Professional Plan",
                    price: "Rs. 6,500 / mo",
                    desc: "Ideal for growing supermarkets, restaurants & multi-warehouse wholesalers",
                    features: ["3 Branches, 8 POS Cashiers", "Table & Kitchen Display (KDS)", "Khata Credit Limits & SMS", "250 AI Monthly Credits"],
                    highlight: true,
                  },
                  {
                    name: "Enterprise Plan",
                    price: "Rs. 15,000 / mo",
                    desc: "For large retail chains, hypermarkets & distributors",
                    features: ["Unlimited Branches & Users", "Full Double-Entry ERP Ledger", "Dedicated AI Microservice", "1,000 AI Monthly Credits"],
                  },
                ].map((plan, idx) => (
                  <div
                    key={idx}
                    className={`p-6 rounded-2xl border flex flex-col justify-between ${
                      plan.highlight
                        ? "bg-slate-900 border-blue-600 shadow-xl shadow-blue-950/40"
                        : "bg-slate-900 border-slate-800"
                    }`}
                  >
                    <div>
                      {plan.highlight && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-600 text-white uppercase tracking-wider">
                          Most Popular
                        </span>
                      )}
                      <h3 className="text-lg font-bold text-white mt-2">{plan.name}</h3>
                      <div className="text-2xl font-bold font-mono text-emerald-400 mt-2">{plan.price}</div>
                      <p className="text-xs text-slate-400 mt-1">{plan.desc}</p>

                      <div className="mt-5 space-y-2">
                        {plan.features.map((f, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs text-slate-300">
                            <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                            <span>{f}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {tab === "health" && (
            <div className="space-y-6">
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold text-white">Cluster Health Telemetry</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                    <div className="text-slate-400 font-sans">Database Query Latency (p99)</div>
                    <div className="text-xl font-bold text-emerald-400 mt-1">12.4 ms</div>
                  </div>
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                    <div className="text-slate-400 font-sans">Redis Memory Consumption</div>
                    <div className="text-xl font-bold text-blue-400 mt-1">142 MB / 2 GB</div>
                  </div>
                  <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                    <div className="text-slate-400 font-sans">Celery Asynchronous Jobs Queue</div>
                    <div className="text-xl font-bold text-purple-400 mt-1">0 Tasks Queued</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {tab === "logs" && (
            <div className="space-y-4">
              <h3 className="text-sm font-bold text-white">Platform Security & Audit Stream</h3>
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden p-4 space-y-2 font-mono text-xs">
                {[
                  { time: "21:28:10", tenant: "namaste-mart", event: "CHECKOUT_PROCESSED", desc: "Invoice INV-2083-000104 posted (Rs. 1,350.35)", status: "OK" },
                  { time: "21:25:40", tenant: "himalayan-wholesale", event: "PLAN_UPGRADE", desc: "Upgraded from Professional to Enterprise tier", status: "OK" },
                  { time: "21:18:22", tenant: "patan-fabrics", event: "STOCK_TRANSFER_DISPATCH", desc: "Dispatched 20 units from KTM Warehouse", status: "OK" },
                  { time: "20:55:12", tenant: "unauthorized-client", event: "CROSS_TENANT_ACCESS_BLOCKED", desc: "Attempted query with mismatched X-Organization-ID rejected", status: "DENIED" },
                ].map((log, idx) => (
                  <div key={idx} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-slate-500">{log.time}</span>
                      <span className="text-blue-400 font-bold">[{log.tenant}]</span>
                      <span className="text-slate-200 font-sans">{log.desc}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      log.status === "OK" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-red-950 text-red-400 border border-red-800"
                    }`}>
                      {log.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Provision Tenant Modal */}
      {newTenantModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <form onSubmit={handleProvisionTenant} className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-400" />
              <span>Provision New SaaS Tenant</span>
            </h3>
            <p className="text-xs text-slate-400">
              Creates a isolated tenant space with automatic chart of accounts and Nepal tax settings.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Business Organization Name:</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Annapurna Department Store"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Industry Module:</label>
                <select
                  value={newOrgType}
                  onChange={(e) => setNewOrgType(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="supermarket">Supermarket / FMCG Mart</option>
                  <option value="retail">Retail Store & Boutique</option>
                  <option value="restaurant">Restaurant & Dine-in Cafe</option>
                  <option value="wholesale">Wholesale & Bulk Distribution</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Subscription Plan Tier:</label>
                <select
                  value={newOrgPlan}
                  onChange={(e) => setNewOrgPlan(e.target.value as any)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  <option value="Starter">Starter (Rs. 2,500/mo)</option>
                  <option value="Professional">Professional (Rs. 6,500/mo)</option>
                  <option value="Enterprise">Enterprise (Rs. 15,000/mo)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={() => setNewTenantModal(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition shadow"
              >
                Create Tenant
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;

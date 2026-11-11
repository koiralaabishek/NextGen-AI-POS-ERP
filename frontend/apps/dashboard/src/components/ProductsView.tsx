import React, { useState } from "react";
import {
  Package,
  Barcode,
  Search,
  Tag,
  Percent,
} from "lucide-react";

interface ProductCatalogItem {
  id: string;
  sku: string;
  barcode: string;
  name: string;
  category: string;
  selling_price: number;
  cost_price: number;
  tax_rate: number;
  reorder_level: number;
  stock_total: number;
}

const SAMPLE_PRODUCTS: ProductCatalogItem[] = [
  { id: "p1", sku: "WHT-FLOUR-5KG", barcode: "8901234567890", name: "Shakti Wheat Flour 5kg", category: "Grains & Staples", cost_price: 410, selling_price: 475, tax_rate: 13, reorder_level: 25, stock_total: 194 },
  { id: "p2", sku: "BASMATI-RICE-25KG", barcode: "8909876543210", name: "Himalayan Basmati Rice 25kg", category: "Grains & Staples", cost_price: 2400, selling_price: 2850, tax_rate: 13, reorder_level: 10, stock_total: 65 },
  { id: "p3", sku: "MUSTARD-OIL-1L", barcode: "8901122334455", name: "Dhara Pure Mustard Oil 1L", category: "Cooking Oil & Ghee", cost_price: 210, selling_price: 245, tax_rate: 13, reorder_level: 20, stock_total: 42 },
  { id: "p4", sku: "WAI-WAI-NOODLE", barcode: "8905544332211", name: "Wai Wai Quick Chicken 75g", category: "Packaged Snacks", cost_price: 20, selling_price: 25, tax_rate: 13, reorder_level: 50, stock_total: 140 },
  { id: "p5", sku: "MILK-FULL-CREAM", barcode: "8906677889900", name: "DDC Pasteurised Milk 500ml", category: "Dairy & Eggs", cost_price: 42, selling_price: 50, tax_rate: 0, reorder_level: 30, stock_total: 8 },
];

export function ProductsView() {
  const [search, setSearch] = useState("");

  const filtered = SAMPLE_PRODUCTS.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase()) ||
      p.barcode.includes(search)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-400" />
            <span>Product Catalog & Nepal VAT Classification</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Maintain SKUs, barcodes, cost margin thresholds, and IRD VAT classifications (13% Standard vs 0% Exempt).
          </p>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search by product name, SKU, barcode..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs w-72 focus:outline-none focus:border-blue-500 text-slate-200"
          />
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="px-5 py-3.5">SKU & Barcode</th>
              <th className="px-5 py-3.5">Product Name</th>
              <th className="px-5 py-3.5">Category</th>
              <th className="px-5 py-3.5 text-right">Cost Price</th>
              <th className="px-5 py-3.5 text-right">Selling Price</th>
              <th className="px-5 py-3.5 text-right">Gross Margin</th>
              <th className="px-5 py-3.5 text-center">VAT Rate</th>
              <th className="px-5 py-3.5 text-right">Total Stock</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {filtered.map((p) => {
              const margin = (((p.selling_price - p.cost_price) / p.selling_price) * 100).toFixed(1);
              return (
                <tr key={p.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-5 py-3">
                    <div className="font-bold text-white">{p.sku}</div>
                    <div className="text-[10px] text-slate-500 flex items-center gap-1 font-sans">
                      <Barcode className="w-3 h-3 text-slate-400" />
                      <span>{p.barcode}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 font-sans font-medium text-slate-200">{p.name}</td>
                  <td className="px-5 py-3 font-sans text-slate-400">{p.category}</td>
                  <td className="px-5 py-3 text-right text-slate-400">Rs. {p.cost_price.toFixed(2)}</td>
                  <td className="px-5 py-3 text-right font-bold text-white">Rs. {p.selling_price.toFixed(2)}</td>
                  <td className="px-5 py-3 text-right text-emerald-400 font-bold">{margin}%</td>
                  <td className="px-5 py-3 text-center font-sans">
                    {p.tax_rate > 0 ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-800">
                        13% Taxable
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        0% Exempt
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right font-bold text-white">{p.stock_total} units</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

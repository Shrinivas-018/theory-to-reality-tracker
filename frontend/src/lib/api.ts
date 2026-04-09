const BASE = "http://localhost:5000";

export async function fetchLaureates({ search = "", category = "" } = {}) {
  const params = new URLSearchParams();
  if (search) params.set("name", search);
  if (category) params.set("category", category);
  const url = search
    ? `${BASE}/search?${params}`
    : `${BASE}/laureates${category ? `?${params}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch laureates");
  return res.json();
}

export async function fetchCategories() {
  const res = await fetch(`${BASE}/categories`);
  if (!res.ok) throw new Error("Failed to fetch categories");
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${BASE}/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchConnections() {
  const res = await fetch(`${BASE}/connections`);
  if (!res.ok) throw new Error("Failed to fetch connections");
  const data = await res.json();
  return data;
}

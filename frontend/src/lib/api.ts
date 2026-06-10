/**
 * Premium API Fetcher with Auto-Authentication Injection
 */
export const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem("session_token");
  
  // Format headers
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  
  // Only inject JSON content type if body is present and not explicitly set
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  
  // Securely inject the active user's session token
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  // If the URL is relative, point it to the local port (e.g. 5000) or keep it relative for deployment
  let targetUrl = url;
  if (url.startsWith("/api")) {
    targetUrl = `http://localhost:5000${url}`;
  }
  
  try {
    const response = await fetch(targetUrl, {
      ...options,
      headers,
    });
    
    // Auto-redirect to login on 401 Unauthorized
    if (response.status === 401) {
      localStorage.removeItem("session_token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    
    return response;
  } catch (error) {
    console.error(`[API ERROR] Fetch failed for ${url}:`, error);
    throw error;
  }
};
